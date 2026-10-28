from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.modules.catalog.schemas import menu_item_read
from apps.api.modules.catalog.service import get_menu_item
from apps.api.modules.identity.models import User
from apps.api.modules.recommendations.models import RecommendationItem, RecommendationRun
from apps.api.modules.rewards.service import award_event
from apps.api.modules.tracking.models import Decision, MealLog
from apps.api.modules.tracking.photo import photo_meal_stats
from apps.api.modules.tracking.schemas import (
    DailySummary,
    DecisionCreate,
    DecisionRead,
    MealLogCreate,
    MealLogRead,
    NutritionTotals,
)


def decision_read(db: Session, decision: Decision) -> DecisionRead:
    item, nutrition = get_menu_item(db, decision.menu_item_id)
    return DecisionRead(
        id=decision.id,
        status=decision.status,
        created_at=decision.created_at,
        menu_item=menu_item_read(item, nutrition),
    )


def create_decision(db: Session, user: User, payload: DecisionCreate) -> DecisionRead:
    row = get_menu_item(db, payload.menu_item_id)
    if row is None or not row[0].available:
        raise HTTPException(404, "Menu item not found")
    if payload.recommendation_id:
        recommendation = db.get(RecommendationItem, payload.recommendation_id)
        if recommendation is None or recommendation.menu_item_id != payload.menu_item_id:
            raise HTTPException(422, "Recommendation does not match menu item")
        run = db.get(RecommendationRun, recommendation.run_id)
        if run.user_id != user.id:
            raise HTTPException(404, "Recommendation not found")
    decision = Decision(
        user_id=user.id,
        menu_item_id=payload.menu_item_id,
        recommendation_item_id=payload.recommendation_id,
        status="planned",
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision_read(db, decision)


def list_decisions(db: Session, user: User, limit: int, offset: int = 0) -> list[DecisionRead]:
    rows = db.scalars(
        select(Decision)
        .where(Decision.user_id == user.id)
        .order_by(Decision.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [decision_read(db, row) for row in rows]


def meal_log_read(db: Session, log: MealLog) -> MealLogRead:
    item, nutrition = get_menu_item(db, log.menu_item_id)
    return MealLogRead(
        id=log.id,
        decision_id=log.decision_id,
        servings=log.servings,
        consumed_at=log.consumed_at,
        nutrition=NutritionTotals(**log.nutrition_snapshot),
        menu_item=menu_item_read(item, nutrition),
    )


def create_meal_log(db: Session, user: User, payload: MealLogCreate) -> MealLogRead:
    decision = db.scalar(
        select(Decision)
        .where(Decision.id == payload.decision_id, Decision.user_id == user.id)
        .with_for_update()
    )
    if decision is None:
        raise HTTPException(404, "Decision not found")
    if decision.status != "planned":
        raise HTTPException(409, "Decision already confirmed")
    _, nutrition = get_menu_item(db, decision.menu_item_id)
    totals = {
        key: round(getattr(nutrition, key) * payload.servings, 2)
        for key in ("calories_kcal", "protein_g", "carbs_g", "fat_g")
    }
    log = MealLog(
        decision_id=decision.id,
        user_id=user.id,
        menu_item_id=decision.menu_item_id,
        servings=payload.servings,
        consumed_at=datetime.now(timezone.utc),
        nutrition_snapshot=totals,
    )
    decision.status = "confirmed"
    db.add(log)
    db.flush()
    award_event(db, user.id, "confirm_meal", "meal_log", log.id, log.consumed_at)
    db.commit()
    db.refresh(log)
    return meal_log_read(db, log)


def list_meal_logs(db: Session, user: User, limit: int, offset: int = 0) -> list[MealLogRead]:
    rows = db.scalars(
        select(MealLog)
        .where(MealLog.user_id == user.id)
        .order_by(MealLog.consumed_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [meal_log_read(db, row) for row in rows]


def daily_summary(db: Session, user: User, day: date) -> DailySummary:
    zone = ZoneInfo("Asia/Hong_Kong")
    start = datetime.combine(day, time.min, tzinfo=zone).astimezone(timezone.utc)
    end = (datetime.combine(day, time.min, tzinfo=zone) + timedelta(days=1)).astimezone(
        timezone.utc
    )
    logs = db.scalars(
        select(MealLog).where(
            MealLog.user_id == user.id,
            MealLog.consumed_at >= start,
            MealLog.consumed_at < end,
        )
    ).all()
    totals = NutritionTotals()
    for log in logs:
        for key, value in log.nutrition_snapshot.items():
            setattr(totals, key, round(getattr(totals, key) + value, 2))
    photo_count, photo_totals = photo_meal_stats(db, user, day)
    for key, value in photo_totals.items():
        setattr(totals, key, round(getattr(totals, key) + value, 1))
    return DailySummary(date=day, meal_count=len(logs) + photo_count, totals=totals)
