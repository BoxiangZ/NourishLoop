from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import get_settings
from apps.api.core.models import utcnow
from apps.api.modules.catalog.models import MenuItem
from apps.api.modules.catalog.schemas import menu_item_read
from apps.api.modules.catalog.service import get_menu_item, list_menu_items
from apps.api.modules.identity.models import User
from apps.api.modules.identity.service import get_goal, get_profile
from apps.api.modules.recommendations.engine import (
    Candidate,
    DeterministicExplanationProvider,
    OptionalExplanationProvider,
    REPEATED_MEAL_DISCOUNT,
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
    MealHistoryContextRead,
    RecommendationJobRead,
    RecommendationRead,
    RecommendationRequest,
    RecommendationRunRead,
)
from apps.api.modules.tracking.history import (
    confirmed_menu_meals, confirmed_photo_meals, day_bounds, local_day,
)


def meal_history_context(
    db: Session, user_id: str,
) -> tuple[MealHistoryContextRead, frozenset[str]]:
    today = local_day(utcnow())
    first_day = today - timedelta(days=6)
    bounds = day_bounds(first_day, today)
    menu_logs = confirmed_menu_meals(db, user_id, *bounds)
    photo_logs = confirmed_photo_meals(db, user_id, *bounds)
    logged_days = {local_day(log.consumed_at) for log in photo_logs}
    menu_days_by_item = defaultdict(set)
    for log in menu_logs:
        day = local_day(log.consumed_at)
        logged_days.add(day)
        menu_days_by_item[log.menu_item_id].add(day)
    repeated = frozenset(item for item, days in menu_days_by_item.items() if len(days) >= 2)
    dish_names = list(db.scalars(select(MenuItem.name).where(
        MenuItem.id.in_(repeated),
    ).order_by(MenuItem.name, MenuItem.id))) if repeated else []
    return MealHistoryContextRead(
        window_start=first_day, through_date=today,
        confirmed_meals=len(menu_logs) + len(photo_logs),
        meal_days=len(logged_days), repeated_dishes=dish_names,
    ), repeated


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
    history_context, repeated_items = meal_history_context(db, user.id)
    catalog_rows = list_menu_items(db, limit=100, max_price_hkd=profile.meal_budget_hkd)
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
        repeated_items,
    )[: request.limit]
    run = RecommendationRun(
        user_id=user.id,
        meal_slot=request.meal_slot,
        scoring_version=engine.weights.version,
        scoring_config={
            **engine.config(),
            "meal_budget_hkd": profile.meal_budget_hkd,
            "history_context": history_context.model_dump(mode="json"),
            "repeated_meal_discount": REPEATED_MEAL_DISCOUNT,
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
        history_context=history_context,
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
        history_context=run.scoring_config.get("history_context"),
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
