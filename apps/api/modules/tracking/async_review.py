"""Temporary photo storage and worker processing for meal check-ins."""

from __future__ import annotations

import base64
import logging
import os
from io import BytesIO
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

from fastapi import HTTPException
from PIL import Image
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from apps.api.core.config import Settings
from apps.api.core.images import IMAGE_EXTENSIONS, validate_image
from apps.api.modules.rewards.service import award_event
from apps.api.modules.tracking.models import PhotoMealRecord
from apps.api.modules.tracking.photo import (
    analyze_photo, auto_estimate_photo_nutrition, photo_meal_read,
)
from apps.api.modules.tracking.review import MealReviewProvider, OpenRouterMealReviewProvider
from apps.api.modules.tracking.schemas import PhotoAnalysisRequest, PhotoAutoEstimateRequest, PhotoFood

logger = logging.getLogger(__name__)


def _event(record: PhotoMealRecord, status: str, detail: str = "") -> None:
    record.review_log = [*(record.review_log or []), {
        "at": datetime.now(timezone.utc).isoformat(), "status": status, "detail": detail,
        "attempt": record.review_attempts,
    }]


def queue_photo_review(db: Session, user_id: str, image: bytes, mime_type: str,
                       notes: str, settings: Settings):
    validate_image(image, mime_type)
    # Re-encode camera uploads without metadata, and keep the recognition payload bounded.
    with Image.open(BytesIO(image)) as source:
        source.thumbnail((1600, 1600))
        prepared = BytesIO()
        source.convert("RGB").save(prepared, format="JPEG", quality=82)
    image = prepared.getvalue()
    mime_type = "image/jpeg"
    if len(image) > 5_000_000:
        raise HTTPException(413, "Prepared photo is too large")
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = upload_dir / f"{uuid4().hex}{IMAGE_EXTENSIONS[mime_type]}"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as target:
        target.write(image)
    record = PhotoMealRecord(
        user_id=user_id, foods=[], notes=notes, model=settings.openrouter_model,
        consumed_at=datetime.now(timezone.utc), nutrition_status="none", unresolved_foods=[],
        review_status="pending", review_attempts=0, review_log=[],
        image_path=str(path), image_type=mime_type, review_questions=[],
    )
    _event(record, "pending")
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return photo_meal_read(record)


def get_photo_review(db: Session, user_id: str, record_id: str) -> PhotoMealRecord:
    record = db.get(PhotoMealRecord, record_id)
    if record is None or record.user_id != user_id:
        raise HTTPException(404, "Photo meal not found")
    return record


def retry_photo_review(db: Session, user_id: str, record_id: str):
    record = get_photo_review(db, user_id, record_id)
    if record.review_status != "failed" or not record.image_path:
        raise HTTPException(409, "Only a failed review with a saved photo can be retried")
    if record.review_attempts >= 3:
        raise HTTPException(409, "This photo has reached the retry limit")
    record.review_status = "pending"
    record.review_error = None
    _event(record, "pending", "retry")
    db.commit()
    db.refresh(record)
    return photo_meal_read(record)


def delete_photo_review(db: Session, user_id: str, record_id: str) -> None:
    record = get_photo_review(db, user_id, record_id)
    if record.review_status not in ("pending", "failed"):
        raise HTTPException(409, "Only pending or failed reviews can be removed")
    image_path = record.image_path
    db.delete(record)
    db.commit()
    if image_path:
        Path(image_path).unlink(missing_ok=True)


def claim_photo_review(db: Session, settings: Settings) -> tuple[str, str] | None:
    stale_before = datetime.now(timezone.utc) - timedelta(seconds=settings.worker_lease_seconds)
    record = db.scalar(
        select(PhotoMealRecord).where(or_(
            PhotoMealRecord.review_status == "pending",
            (PhotoMealRecord.review_status == "processing") &
            (PhotoMealRecord.review_claimed_at < stale_before),
        )).order_by(PhotoMealRecord.created_at, PhotoMealRecord.id)
        .with_for_update(skip_locked=True).limit(1)
    )
    if record is None:
        return None
    if record.review_attempts >= 3:
        record.review_status = "failed"
        record.review_error = "Review retry limit reached"
        _event(record, "failed", "attempts_exhausted")
        db.commit()
        return None
    token = str(uuid4())
    record.review_status = "processing"
    record.review_claimed_at = datetime.now(timezone.utc)
    record.review_claim_token = token
    record.review_attempts += 1
    _event(record, "processing")
    db.commit()
    return record.id, token


def process_photo_review_once(
    session_factory: sessionmaker,
    settings: Settings,
    provider_factory: Callable[[Settings], MealReviewProvider] | None = None,
    analyzer: Callable | None = None,
) -> str | None:
    with session_factory() as db:
        claim = claim_photo_review(db, settings)
    if claim is None:
        return None
    record_id, token = claim
    try:
        with session_factory() as db:
            record = db.get(PhotoMealRecord, record_id)
            if not record or not record.image_path or not record.image_type:
                raise ValueError("Photo is unavailable")
            image = Path(record.image_path).read_bytes()
            validate_image(image, record.image_type)
            provider = (provider_factory or OpenRouterMealReviewProvider)(settings)
            ai_result = None
            ai_error = None
            try:
                ai_result = provider.review(image, record.image_type, record.notes).review
            except Exception as exc:
                ai_error = type(exc).__name__
                logger.warning("photo_ai_review_failed", extra={"record_id": record_id, "error": ai_error})
            analysis = None
            analysis_error = None
            try:
                analysis = (analyzer or analyze_photo)(PhotoAnalysisRequest(
                    image_base64=base64.b64encode(image).decode("ascii"),
                    mime_type=record.image_type, notes=record.notes,
                ), settings)
            except Exception as exc:
                analysis_error = type(exc).__name__
                logger.warning("photo_usda_analysis_failed", extra={"record_id": record_id, "error": analysis_error})
            foods = analysis.foods if analysis and analysis.foods else [
                PhotoFood(name=name) for name in (ai_result.detected_foods if ai_result and ai_result.is_food else [])[:12]
            ]
            if not foods:
                raise ValueError("No food detected" if ai_result or analysis else "Recognition unavailable")
            nutrition = None
            nutrition_status = "none"
            unresolved = ["Source-backed nutrition unavailable"] if analysis_error else []
            if analysis and analysis.foods:
                try:
                    auto = auto_estimate_photo_nutrition(
                        db, PhotoAutoEstimateRequest(foods=analysis.foods), settings,
                    )
                    nutrition = auto.estimate or auto.partial_estimate
                    nutrition_status = "complete" if auto.estimate else "partial" if auto.partial_estimate else "none"
                    unresolved = auto.unresolved
                except Exception as exc:
                    db.rollback()
                    logger.warning("photo_usda_lookup_failed", extra={"record_id": record_id, "error": type(exc).__name__})
                    unresolved = ["USDA lookup unavailable"]
            if nutrition is None and not (ai_result and ai_result.is_food):
                raise ValueError("Nutrition unavailable")
            record = db.get(PhotoMealRecord, record_id)
            if record.review_claim_token != token or record.review_status != "processing":
                return record_id
            record.foods = [food.model_dump() for food in foods]
            record.nutrition_snapshot = nutrition.nutrition.model_dump() if nutrition else None
            record.nutrition_items = [item.model_dump() for item in nutrition.items] if nutrition else None
            record.nutrition_status = nutrition_status
            record.unresolved_foods = unresolved
            record.ai_review = ai_result.model_dump() if ai_result and ai_result.is_food else None
            record.review_questions = analysis.review_questions if analysis else []
            record.review_status = "completed"
            record.review_error = None
            record.review_claim_token = None
            image_path = record.image_path
            record.image_path = None
            _event(record, "completed", f"ai={ai_error or 'ok'}; source={analysis_error or nutrition_status}")
            award_event(db, record.user_id, "confirm_meal", "photo_meal", record.id, record.consumed_at)
            db.commit()
            if image_path:
                Path(image_path).unlink(missing_ok=True)
    except Exception as exc:
        logger.exception("photo_review_failed", extra={"record_id": record_id})
        with session_factory() as db:
            record = db.get(PhotoMealRecord, record_id)
            if record and record.review_claim_token == token and record.review_status == "processing":
                record.review_status = "failed"
                record.review_error = "No food detected in this photo" if str(exc) == "No food detected" else "Photo review failed; please retry"
                record.review_claim_token = None
                _event(record, "failed", type(exc).__name__)
                db.commit()
    return record_id
