from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.core.auth import current_user
from apps.api.core.database import get_db
from apps.api.modules.identity.models import User
from apps.api.modules.tracking.schemas import (
    DailySummary,
    DecisionCreate,
    DecisionRead,
    MealLogCreate,
    MealLogRead,
)
from apps.api.modules.tracking.service import (
    create_decision,
    create_meal_log,
    daily_summary,
    list_decisions,
    list_meal_logs,
)

router = APIRouter(prefix="/api/v1", tags=["tracking"])


@router.post("/decisions", response_model=DecisionRead, status_code=201)
def decide(
    payload: DecisionCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return create_decision(db, user, payload)


@router.get("/me/decisions", response_model=list[DecisionRead])
def decisions(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return list_decisions(db, user, limit)


@router.post("/meal-logs", response_model=MealLogRead, status_code=201)
def log_meal(
    payload: MealLogCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return create_meal_log(db, user, payload)


@router.get("/me/meal-logs", response_model=list[MealLogRead])
def meal_logs(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return list_meal_logs(db, user, limit)


@router.get("/me/daily-summary", response_model=DailySummary)
def summary(
    day: date | None = Query(default=None, alias="date"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    actual_day = day or datetime.now(ZoneInfo("Asia/Hong_Kong")).date()
    return daily_summary(db, user, actual_day)
