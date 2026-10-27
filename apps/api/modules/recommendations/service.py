from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import get_settings
from apps.api.modules.catalog.schemas import menu_item_read
from apps.api.modules.catalog.service import get_menu_item, list_menu_items
from apps.api.modules.identity.models import User
from apps.api.modules.identity.service import get_goal, get_profile
from apps.api.modules.recommendations.engine import (
    Candidate,
    DeterministicExplanationProvider,
    OptionalExplanationProvider,
    RuleBasedRecommendationEngine,
    explain_with_fallback,
)
from apps.api.modules.recommendations.models import (
    RecommendationFeedback,
    RecommendationItem,
    RecommendationJob,
    RecommendationRun,
)
from apps.api.modules.recommendations.schemas import (
    FeedbackCreate,
    RecommendationJobRead,
    RecommendationRead,
    RecommendationRequest,
    RecommendationRunRead,
)


def generate(
    db: Session,
    user: User,
    request: RecommendationRequest,
    *,
    provider_name: str = "deterministic",
    provider: OptionalExplanationProvider | None = None,
    commit: bool = True,
) -> RecommendationRunRead:
    profile = get_profile(db, user)
    goal = get_goal(db, user)
    catalog_rows = list_menu_items(db, limit=100)
    lookup = {item.id: (item, nutrition) for item, nutrition in catalog_rows}
    candidates = [
        Candidate(
            item.id,
            item.name,
            tuple(item.tags),
            tuple(item.allergen_tags),
            nutrition.calories_kcal,
            nutrition.protein_g,
        )
        for item, nutrition in catalog_rows
    ]
    engine = RuleBasedRecommendationEngine()
    provider = provider or DeterministicExplanationProvider()
    ranked = engine.rank(
        candidates,
        goal.goal,
        goal.daily_calorie_target,
        profile.dietary_preferences,
        profile.allergies,
    )[: request.limit]
    run = RecommendationRun(
        user_id=user.id,
        meal_slot=request.meal_slot,
        scoring_version=engine.weights.version,
        scoring_config={
            **engine.config(),
            "explanation_provider": provider_name,
            "explanation_model": (
                get_settings().openrouter_model if provider_name == "openrouter" else None
            ),
            "llm_explanation_limit": 1 if provider_name == "openrouter" else 0,
        },
    )
    db.add(run)
    db.flush()
    response_items = []
    for rank, result in enumerate(ranked, start=1):
        row = RecommendationItem(
            run_id=run.id,
            menu_item_id=result.candidate.item_id,
            rank=rank,
            score=result.score,
            explanation=explain_with_fallback(
                provider if rank == 1 else DeterministicExplanationProvider(),
                result.candidate,
                result.explanation,
            ),
        )
        db.add(row)
        db.flush()
        item, nutrition = lookup[result.candidate.item_id]
        response_items.append(
            RecommendationRead(
                id=row.id,
                rank=rank,
                score=row.score,
                explanation=row.explanation,
                confidence="low",
                confidence_reason="Fictional demo catalog with illustrative nutrition estimates.",
                menu_item=menu_item_read(item, nutrition),
            )
        )
    if commit:
        db.commit()
    return RecommendationRunRead(
        id=run.id,
        scoring_version=run.scoring_version,
        meal_slot=run.meal_slot,
        recommendations=response_items,
    )


def enqueue(db: Session, user: User, request: RecommendationRequest) -> RecommendationJobRead:
    job = RecommendationJob(
        user_id=user.id,
        meal_slot=request.meal_slot,
        result_limit=request.limit,
        provider=get_settings().explanation_provider,
        status="pending",
        attempts=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job_read(db, job)


def job_read(db: Session, job: RecommendationJob) -> RecommendationJobRead:
    run = read_run(db, job.run_id) if job.run_id else None
    return RecommendationJobRead(
        id=job.id,
        status=job.status,
        attempts=job.attempts,
        provider=job.provider,
        error=job.error,
        created_at=job.created_at,
        completed_at=job.completed_at,
        run=run,
    )


def get_job(db: Session, user: User, job_id: str) -> RecommendationJobRead:
    job = db.get(RecommendationJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(404, "Recommendation job not found")
    return job_read(db, job)


def read_run(db: Session, run_id: str) -> RecommendationRunRead:
    run = db.get(RecommendationRun, run_id)
    items = db.scalars(
        select(RecommendationItem)
        .where(RecommendationItem.run_id == run_id)
        .order_by(RecommendationItem.rank)
    ).all()
    recommendations = []
    for row in items:
        item, nutrition = get_menu_item(db, row.menu_item_id)
        recommendations.append(
            RecommendationRead(
                id=row.id,
                rank=row.rank,
                score=row.score,
                explanation=row.explanation,
                confidence="low",
                confidence_reason="Fictional demo catalog with illustrative nutrition estimates.",
                menu_item=menu_item_read(item, nutrition),
            )
        )
    return RecommendationRunRead(
        id=run.id,
        scoring_version=run.scoring_version,
        meal_slot=run.meal_slot,
        recommendations=recommendations,
    )


def add_feedback(db: Session, user: User, item_id: str, payload: FeedbackCreate) -> None:
    item = db.get(RecommendationItem, item_id)
    if item is None:
        raise HTTPException(404, "Recommendation not found")
    run = db.get(RecommendationRun, item.run_id)
    if run.user_id != user.id:
        raise HTTPException(404, "Recommendation not found")
    db.add(
        RecommendationFeedback(
            recommendation_item_id=item_id,
            user_id=user.id,
            helpful=payload.helpful,
            comment=payload.comment,
        )
    )
    db.commit()
