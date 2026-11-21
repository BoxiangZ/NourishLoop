from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.modules.identity.models import User
from apps.api.modules.catalog.models import NutritionFood
from apps.api.modules.rewards.service import award_event
from apps.api.modules.tracking.models import PhotoMealRecord
from apps.api.modules.tracking.schemas import (
    PhotoAnalysisRead,
    PhotoAnalysisRequest,
    PhotoMealCreate,
    PhotoMealRead,
    PhotoNutritionEstimateRead,
    PhotoNutritionEstimateRequest,
    PhotoNutritionItemRead,
    NutritionTotals,
    PhotoAutoEstimateRequest,
    PhotoAutoEstimateRead,
    PhotoAutoMatchRead,
    PhotoNutritionSelection,
    PhotoFood,
)
from apps.api.modules.catalog.nutrition import search_nutrition_foods, _word_tokens, _first_subject
from apps.api.modules.tracking.review import MealAIReview, OpenRouterMealReviewProvider
import re


def _check_image(raw: bytes, mime_type: str) -> None:
    valid = (
        (mime_type == "image/jpeg" and raw.startswith(b"\xff\xd8\xff"))
        or (mime_type == "image/png" and raw.startswith(b"\x89PNG\r\n\x1a\n"))
        or (mime_type == "image/webp" and raw.startswith(b"RIFF") and raw[8:12] == b"WEBP")
    )
    if not valid:
        raise HTTPException(422, "Image bytes do not match the selected format")


def analyze_photo(
    request: PhotoAnalysisRequest,
    settings: Settings,
    transport: httpx.BaseTransport | None = None,
) -> PhotoAnalysisRead:
    raw = base64.b64decode(request.image_base64, validate=True)
    _check_image(raw, request.mime_type)
    secret = settings.openrouter_api_key
    if secret is None or not secret.get_secret_value():
        raise HTTPException(503, "Photo recognition requires an OpenRouter API key")
    prompt = (
        "Inspect this meal photo and the user's notes. Return only a compact JSON object with "
        "foods (array of {name, preparation, quantity_from_notes, estimated_grams, "
        "portion_basis}) and review_questions "
        "(array of strings). Keep names short, list each distinct ingredient only once, "
        "limit to 12 visible foods and use no prose or markdown. "
        "List only visibly plausible foods. Use null for uncertain "
        "preparation. Copy a quantity only if it is an exact substring of the notes; "
        "otherwise use null. Give each distinct visible food a specific English name "
        "and preparation suitable for a USDA search (for example 'rice, white, cooked'). "
        "Break mixed dishes into separately visible ingredients such as rice, identifiable "
        "meat, vegetables, and sauce. Allocate estimated grams across those components "
        "without double counting; do not name the whole dish as an extra food. "
        "Do not guess an ingredient that cannot be seen. "
        "For each visible food, set estimated_grams to a rough edible-weight estimate "
        "using visual size and ordinary serving references, or to an explicit gram amount "
        "in the notes. Use null only when the photo is too unclear to estimate. "
        "Set portion_basis to user_note only for explicit grams in notes, visual_estimate "
        "for visual estimates, or unknown if null. Never infer exact weight from the photo. "
        "Optional review questions may mention unclear food or portions. If the image does not show food, "
        "return an empty foods array. Also return ai_review as an object containing "
        "is_food, detected_foods (names of the visible foods), estimated_nutrition "
        "(calories_kcal, protein_g, carbs_g, fat_g for the entire visible meal), "
        "confidence (0 to 1), summary, suggestions and assumptions. "
        "Nutrition is a rough visual estimate, not a measured value: state portion, "
        "oil and sauce uncertainty in assumptions. For a non-food image, use "
        "is_food=false, detected_foods=[], estimated_nutrition=null. "
        "Do not invent hidden ingredients, health effects, or plan alignment. "
        f"User notes: {request.notes or '(none)'}"
    )
    try:
        with httpx.Client(
            timeout=settings.openrouter_timeout_seconds, transport=transport
        ) as client:
            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {secret.get_secret_value()}"},
                json={
                    "model": settings.openrouter_model,
                    "max_tokens": 2200,
                    "reasoning": {"enabled": False},
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                    "url": (
                                        f"data:{request.mime_type};base64,{request.image_base64}"
                                    ),
                                    },
                                },
                            ],
                        }
                    ],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("No recognition result")
        body = content.strip()
        if body.startswith("```"):
            body = body.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(body)
        review = None
        if isinstance(data, dict) and isinstance(data.get("ai_review"), dict):
            try:
                review = MealAIReview.model_validate(data["ai_review"])
            except ValueError:
                pass
        if review is None and isinstance(data, dict) and data.get("foods"):
            try:
                review = OpenRouterMealReviewProvider(settings, transport).review(
                    raw, request.mime_type, request.notes,
                ).review
            except Exception:
                pass
        result = PhotoAnalysisRead.model_validate({
            "foods": data["foods"], "review_questions": data.get("review_questions", []),
            "model": settings.openrouter_model, "requires_review": False,
            "ai_review": review if review and review.is_food else None,
        })
        if any(food.quantity_from_notes and
               food.quantity_from_notes.lower() not in request.notes.lower()
               for food in result.foods):
            raise ValueError("Quantity absent from notes")
        for food in result.foods:
            if food.portion_basis == "user_note":
                grams_in_notes = re.findall(
                    r"\b(\d+(?:\.\d+)?)\s*(?:g|grams?)\b",
                    food.quantity_from_notes or "",
                    re.I,
                )
                if not grams_in_notes or food.estimated_grams not in [
                    float(value) for value in grams_in_notes
                ]:
                    food.portion_basis = "visual_estimate" if food.estimated_grams else "unknown"
            if food.estimated_grams is None:
                food.portion_basis = "unknown"
        unique: dict[frozenset[str], PhotoFood] = {}
        for food in result.foods:
            key = _word_tokens(f"{food.name} {food.preparation or ''}")
            current = unique.get(key)
            if current is None or (
                (food.portion_basis == "user_note", food.estimated_grams or 0)
                > (current.portion_basis == "user_note", current.estimated_grams or 0)
            ):
                if current and current.quantity_from_notes and not food.quantity_from_notes:
                    food.quantity_from_notes = current.quantity_from_notes
                unique[key] = food
        result.foods = list(unique.values())
        return result
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(503, "Photo recognition is unavailable; please try again") from None


def photo_meal_read(record: PhotoMealRecord) -> PhotoMealRead:
    return PhotoMealRead(
        id=record.id,
        foods=record.foods,
        notes=record.notes,
        model=record.model,
        consumed_at=record.consumed_at,
        nutrition=NutritionTotals(**record.nutrition_snapshot)
        if record.nutrition_snapshot
        else None,
        nutrition_items=record.nutrition_items or [],
        nutrition_status=record.nutrition_status,
        unresolved_foods=record.unresolved_foods or [],
        review_status=record.review_status,
        review_attempts=record.review_attempts,
        review_error=record.review_error,
        ai_review=record.ai_review,
        review_questions=record.review_questions or [],
    )


def estimate_photo_nutrition(
    db: Session,
    payload: PhotoNutritionEstimateRequest,
) -> PhotoNutritionEstimateRead:
    selections = payload.nutrition_selections
    if len(selections) != len(payload.foods) or {item.food_index for item in selections} != set(
        range(len(payload.foods))
    ):
        raise HTTPException(422, "Select one USDA food and enter grams for every food")
    keys = ("calories_kcal", "protein_g", "carbs_g", "fat_g")
    totals = {key: Decimal("0") for key in keys}
    items = []
    for selection in sorted(selections, key=lambda item: item.food_index):
        source = db.get(NutritionFood, selection.fdc_id)
        if source is None:
            raise HTTPException(422, "Selected USDA food is not in the verified lookup cache")
        grams = Decimal(str(selection.grams))
        values = {key: Decimal(getattr(source, key)) * grams / Decimal("100") for key in keys}
        for key in keys:
            totals[key] += values[key]
        items.append(
            PhotoNutritionItemRead(
                name=payload.foods[selection.food_index].name,
                fdc_id=source.fdc_id,
                source_description=source.description,
                source_url=f"https://fdc.nal.usda.gov/food-search/?query={source.fdc_id}",
                grams=float(grams),
                portion_basis=selection.portion_basis,
                **{
                    key: float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
                    for key, value in values.items()
                },
            )
        )
    return PhotoNutritionEstimateRead(
        nutrition=NutritionTotals(
            **{
                key: float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
                for key, value in totals.items()
            }
        ),
        items=items,
    )


def _tokens(value: str) -> set[str]:
    return set(_word_tokens(value)) - {"and", "with", "the", "food", "fresh"}


def _best_match(food, candidates):
    wanted = _tokens(f"{food.name} {food.preparation or ''}")
    preparations = {
        "cooked",
        "raw",
        "fried",
        "boiled",
        "steamed",
        "roasted",
        "baked",
        "dry",
        "uncooked",
        "dehydrated",
        "instant",
    }
    core = wanted - preparations
    if not core:
        return None
    ranked = []
    primary = _first_subject(food.name)
    for candidate in candidates:
        got = _tokens(candidate.description)
        if _first_subject(candidate.description) != primary:
            continue
        if not core.issubset(got):
            continue
        if (
            primary == "beef"
            and "ground" not in wanted
            and not {
                "composite",
                "all",
                "grade",
            }.issubset(got)
        ):
            continue
        if (
            primary == "tomato"
            and not {"green", "yellow", "orange", "red"} & wanted
            and not {"red", "ripe"}.issubset(got)
        ):
            continue
        if any(
            term in got and term not in wanted
            for term in (
                "white",
                "brown",
                "wild",
                "yolk",
                "glutinous",
                "duck",
                "goose",
                "quail",
                "turkey",
                "noodle",
                "ring",
                "breaded",
                "sausage",
                "salami",
                "soup",
                "pie",
                "cake",
                "sandwich",
                "burger",
                "cured",
            )
        ):
            continue
        conflict = any(
            term in got and term not in wanted
            for term in (
                "raw",
                "fried",
                "boiled",
                "steamed",
                "roasted",
                "baked",
                "dry",
                "uncooked",
                "dehydrated",
                "instant",
            )
        )
        if conflict:
            continue
        if any(
            term in wanted and term not in got
            for term in ("cooked", "raw", "fried", "boiled", "steamed", "roasted", "baked")
        ):
            continue
        ranked.append((len(wanted & got), -len(got - wanted), candidate))
    return max(ranked, key=lambda row: row[:2])[2] if ranked else None


def auto_estimate_photo_nutrition(
    db: Session,
    payload: PhotoAutoEstimateRequest,
    settings: Settings,
) -> PhotoAutoEstimateRead:
    matches: list[PhotoAutoMatchRead] = []
    selections: list[PhotoNutritionSelection] = []
    unresolved: list[str] = []
    for index, food in enumerate(payload.foods):
        query = f"{food.name} {food.preparation or ''}".strip()
        lookup_unavailable = False
        try:
            candidates = search_nutrition_foods(db, query, 12, settings)
            match = _best_match(food, candidates)
            if match is None and candidates:
                match = _best_match(
                    food,
                    search_nutrition_foods(
                        db,
                        query,
                        12,
                        settings,
                        bypass_cache=True,
                    ),
                )
        except HTTPException:
            match = None
            lookup_unavailable = True
        reason = None
        if lookup_unavailable:
            reason = "USDA lookup unavailable"
        elif not match:
            reason = "No reliable USDA match"
        elif food.estimated_grams is None:
            reason = "Portion weight unclear"
        matches.append(PhotoAutoMatchRead(food_index=index, match=match, reason=reason))
        if reason:
            unresolved.append(f"{food.name}: {reason}")
        else:
            selections.append(
                PhotoNutritionSelection(
                    food_index=index,
                    fdc_id=match.fdc_id,
                    grams=food.estimated_grams,
                    portion_basis=(
                        "user_note" if food.portion_basis == "user_note" else "visual_estimate"
                    ),
                )
            )
    estimate = (
        estimate_photo_nutrition(
            db,
            PhotoNutritionEstimateRequest(
                foods=payload.foods,
                nutrition_selections=selections,
            ),
        )
        if not unresolved
        else None
    )
    partial_estimate = None
    if unresolved and selections:
        partial_estimate = estimate_photo_nutrition(
            db,
            PhotoNutritionEstimateRequest(
                foods=[payload.foods[item.food_index] for item in selections],
                nutrition_selections=[
                    item.model_copy(update={"food_index": index})
                    for index, item in enumerate(selections)
                ],
            ),
        )
    return PhotoAutoEstimateRead(
        estimate=estimate,
        partial_estimate=partial_estimate,
        selections=selections,
        matches=matches,
        unresolved=unresolved,
    )


def confirm_photo_meal(db: Session, user: User, payload: PhotoMealCreate) -> PhotoMealRead:
    selections = payload.nutrition_selections
    selected_indices = {item.food_index for item in selections}
    if len(selected_indices) != len(selections) or any(
        index >= len(payload.foods) for index in selected_indices
    ):
        raise HTTPException(422, "Nutrition selections must reference distinct foods in this meal")
    estimate = estimate_photo_nutrition(db, PhotoNutritionEstimateRequest(
        foods=[payload.foods[item.food_index] for item in selections],
        nutrition_selections=[item.model_copy(update={"food_index": index})
                              for index, item in enumerate(selections)],
    )) if selections else None
    if estimate is None and not (
        payload.ai_review and payload.ai_review.is_food and payload.ai_review.estimated_nutrition
    ):
        raise HTTPException(422, "A nutrition estimate is required before saving this photo meal")
    nutrition_status = ("complete" if len(selections) == len(payload.foods) else "partial") \
        if estimate else "none"
    unresolved_foods = [food.name for index, food in enumerate(payload.foods)
                        if index not in selected_indices]
    record = PhotoMealRecord(
        user_id=user.id,
        foods=[food.model_dump() for food in payload.foods],
        notes=payload.notes,
        model=payload.model,
        consumed_at=datetime.now(timezone.utc),
        nutrition_snapshot=estimate.nutrition.model_dump() if estimate else None,
        nutrition_items=[item.model_dump() for item in estimate.items] if estimate else None,
        nutrition_status=nutrition_status, unresolved_foods=unresolved_foods,
        ai_review=payload.ai_review.model_dump() if payload.ai_review else None,
    )
    db.add(record)
    db.flush()
    award_event(db, user.id, "confirm_meal", "photo_meal", record.id, record.consumed_at)
    db.commit()
    db.refresh(record)
    return photo_meal_read(record)


def list_photo_meals(db: Session, user: User, limit: int, offset: int) -> list[PhotoMealRead]:
    rows = db.scalars(
        select(PhotoMealRecord)
        .where(PhotoMealRecord.user_id == user.id)
        .order_by(PhotoMealRecord.consumed_at.desc(), PhotoMealRecord.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [photo_meal_read(row) for row in rows]


def photo_meal_stats(db: Session, user: User, day) -> tuple[int, dict[str, float]]:
    zone = ZoneInfo("Asia/Hong_Kong")
    start = datetime.combine(day, datetime.min.time(), tzinfo=zone).astimezone(timezone.utc)
    end = (datetime.combine(day, datetime.min.time(), tzinfo=zone) + timedelta(days=1)).astimezone(
        timezone.utc
    )
    rows = db.scalars(
        select(PhotoMealRecord).where(
            PhotoMealRecord.user_id == user.id,
            PhotoMealRecord.consumed_at >= start,
            PhotoMealRecord.consumed_at < end,
        )
    ).all()
    totals = {
        key: Decimal("0")
        for key in (
            "calories_kcal",
            "protein_g",
            "carbs_g",
            "fat_g",
        )
    }
    for row in rows:
        if row.review_status not in ("not_requested", "completed"):
            continue
        if row.nutrition_status == "complete" and row.nutrition_snapshot:
            for key in totals:
                totals[key] += Decimal(str(row.nutrition_snapshot[key]))
    return sum(row.review_status in ("not_requested", "completed") for row in rows), {key: float(value) for key, value in totals.items()}
