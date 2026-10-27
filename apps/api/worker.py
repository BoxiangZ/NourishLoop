from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Callable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from apps.api.core.config import Settings, get_settings
from apps.api.core.database import make_engine, make_session_factory
from apps.api.core.models import utcnow
from apps.api.modules.identity.models import User
from apps.api.modules.recommendations.engine import (
    DeterministicExplanationProvider,
    OptionalExplanationProvider,
)
from apps.api.modules.recommendations.models import RecommendationJob
from apps.api.modules.recommendations.openrouter import OpenRouterExplanationProvider
from apps.api.modules.recommendations.schemas import RecommendationRequest
from apps.api.modules.recommendations.service import generate

logger = logging.getLogger(__name__)


def claim_next(db: Session, settings: Settings) -> RecommendationJob | None:
    stale_before = utcnow() - timedelta(seconds=settings.worker_lease_seconds)
    job = db.scalar(
        select(RecommendationJob)
        .where(
            or_(
                RecommendationJob.status == "pending",
                (RecommendationJob.status == "claimed")
                & (RecommendationJob.claimed_at < stale_before),
            )
        )
        .order_by(RecommendationJob.created_at, RecommendationJob.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job is None:
        return None
    if job.attempts >= 3:
        job.status = "failed"
        job.error = "worker_attempts_exhausted"
        job.completed_at = utcnow()
        db.commit()
        return None
    job.status = "claimed"
    job.claimed_at = utcnow()
    job.attempts += 1
    db.commit()
    return job


def process_once(
    session_factory: sessionmaker,
    settings: Settings | None = None,
    provider_factory: Callable[[Settings], OptionalExplanationProvider] | None = None,
) -> str | None:
    settings = settings or get_settings()
    with session_factory() as db:
        job = claim_next(db, settings)
        if job is None:
            return None
        job_id = job.id
        provider_name = job.provider
    logger.info("recommendation_job_claimed", extra={"job_id": job_id})

    try:
        with session_factory() as db:
            job = db.get(RecommendationJob, job_id)
            user = db.get(User, job.user_id)
            if user is None:
                raise ValueError("Job user is missing")
            if provider_factory is not None:
                provider = provider_factory(settings)
            elif provider_name == "openrouter":
                provider = OpenRouterExplanationProvider(settings)
            else:
                provider = DeterministicExplanationProvider()
            run = generate(
                db,
                user,
                RecommendationRequest(meal_slot=job.meal_slot, limit=job.result_limit),
                provider_name=provider_name,
                provider=provider,
                commit=False,
            )
            job.run_id = run.id
            job.status = "completed"
            job.error = None
            job.completed_at = utcnow()
            db.commit()
        logger.info(
            "recommendation_job_completed",
            extra={"job_id": job_id, "run_id": run.id, "provider": provider_name},
        )
    except Exception as exc:
        logger.exception("recommendation_job_failed", extra={"job_id": job_id})
        with session_factory() as db:
            job = db.get(RecommendationJob, job_id)
            if job is not None and job.status == "claimed":
                job.status = "failed"
                job.error = type(exc).__name__
                job.completed_at = utcnow()
                db.commit()
    return job_id


def run_forever() -> None:
    settings = get_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)
    logger.info("recommendation_worker_started")
    while True:
        if process_once(session_factory, settings) is None:
            time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    run_forever()
