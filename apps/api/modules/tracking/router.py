from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.core.auth import current_user
from apps.api.core.database import get_db
from apps.api.core.config import get_settings
from apps.api.modules.identity.models import User
from apps.api.modules.tracking.schemas import (
    DailySummary,
    DecisionCreate,
    DecisionRead,
    MealLogCreate,
    MealLogRead,
    PhotoAnalysisRequest,
    PhotoAnalysisRead,
    PhotoMealCreate,
    PhotoMealRead,
    PhotoNutritionEstimateRequest,
    PhotoNutritionEstimateRead,
    PhotoAutoEstimateRequest,
    PhotoAutoEstimateRead,
)
from apps.api.modules.tracking.photo import (
    analyze_photo, confirm_photo_meal, estimate_photo_nutrition, list_photo_meals,
    auto_estimate_photo_nutrition,
)
from apps.api.modules.tracking.service import (
    create_decision,
    create_meal_log,
    daily_summary,
    list_decisions,
    list_meal_logs,
)

router = APIRouter(prefix="/api/v1", tags=["tracking"])


@router.post("/meals/analyze-photo", response_model=PhotoAnalysisRead)
def analyze_meal_photo(
    payload: PhotoAnalysisRequest,
    _user: User = Depends(current_user),
):
    return analyze_photo(payload, get_settings())


@router.post("/photo-meals", response_model=PhotoMealRead, status_code=201)
def record_photo_meal(
    payload: PhotoMealCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return confirm_photo_meal(db, user, payload)


@router.post("/photo-meals/estimate", response_model=PhotoNutritionEstimateRead)
def preview_photo_nutrition(
    payload: PhotoNutritionEstimateRequest,
    _user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return estimate_photo_nutrition(db, payload)


@router.post("/photo-meals/auto-estimate", response_model=PhotoAutoEstimateRead)
def auto_preview_photo_nutrition(
    payload: PhotoAutoEstimateRequest,
    _user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return auto_estimate_photo_nutrition(db, payload, get_settings())


@router.get("/me/photo-meals", response_model=list[PhotoMealRead])
def photo_meals(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return list_photo_meals(db, user, limit, offset)


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
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return list_decisions(db, user, limit, offset)


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
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return list_meal_logs(db, user, limit, offset)


@router.get("/me/daily-summary", response_model=DailySummary)
def summary(
    day: date | None = Query(default=None, alias="date"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    actual_day = day or datetime.now(ZoneInfo("Asia/Hong_Kong")).date()
    return daily_summary(db, user, actual_day)
