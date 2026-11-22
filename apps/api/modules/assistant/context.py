from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.modules.assistant.schemas import (
    AssistantContext,
    MenuMealContext,
    NutritionContext,
    PhotoMealContext,
    WorkoutContext,
    WorkoutProfileContext,
)
from apps.api.modules.catalog.models import MenuItem
from apps.api.modules.identity.models import User
from apps.api.modules.identity.service import get_goal, get_profile
from apps.api.modules.tracking.models import MealLog, PhotoMealRecord
from apps.api.modules.tracking.service import daily_summary
from apps.api.modules.workouts.models import WorkoutPlan, WorkoutProfile, WorkoutSession
from apps.api.modules.workouts.service import session_read

HK_ZONE = ZoneInfo("Asia/Hong_Kong")


def _day_bounds(day: date | None) -> tuple[date, datetime, datetime]:
    local_day = day or datetime.now(HK_ZONE).date()
    start_local = datetime.combine(local_day, time.min, tzinfo=HK_ZONE)
    end_local = start_local + timedelta(days=1)
    return (
        local_day,
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
    )


def _photo_food_names(foods: list) -> list[str]:
    return [
        food["name"] if isinstance(food, dict) else str(food)
        for food in foods
        if (not isinstance(food, dict)) or food.get("name")
    ]


def build_today_context(
    db: Session, user: User, day: date | None = None
) -> AssistantContext:
    local_day, start, end = _day_bounds(day)
    goal = get_goal(db, user)
    profile = get_profile(db, user)

    menu_rows = db.execute(
        select(MealLog, MenuItem)
        .join(MenuItem, MenuItem.id == MealLog.menu_item_id)
        .where(
            MealLog.user_id == user.id,
            MealLog.consumed_at >= start,
            MealLog.consumed_at < end,
        )
        .order_by(MealLog.consumed_at, MealLog.id)
    ).all()
    menu_meals = [
        MenuMealContext(
            name=item.name,
            servings=log.servings,
            consumed_at=log.consumed_at,
            nutrition=NutritionContext(**log.nutrition_snapshot),
        )
        for log, item in menu_rows
    ]

    photo_rows = db.scalars(
        select(PhotoMealRecord)
        .where(
            PhotoMealRecord.user_id == user.id,
            PhotoMealRecord.consumed_at >= start,
            PhotoMealRecord.consumed_at < end,
        )
        .order_by(PhotoMealRecord.consumed_at, PhotoMealRecord.id)
    ).all()
    photo_meals = [
        PhotoMealContext(
            food_names=_photo_food_names(row.foods),
            notes=row.notes,
            review_status=row.review_status,
            nutrition_status=row.nutrition_status,
            nutrition=(
                NutritionContext(**row.nutrition_snapshot)
                if row.nutrition_snapshot
                else None
            ),
            unresolved_foods=row.unresolved_foods or [],
        )
        for row in photo_rows
    ]

    workout_rows = db.execute(
        select(WorkoutSession, WorkoutPlan)
        .join(WorkoutPlan, WorkoutPlan.id == WorkoutSession.plan_id)
        .where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.completed_at >= start,
            WorkoutSession.completed_at < end,
        )
        .order_by(WorkoutSession.completed_at, WorkoutSession.id)
    ).all()
    workouts = []
    for workout_session, plan in workout_rows:
        session_context = session_read(db, workout_session, plan)
        workouts.append(
            WorkoutContext(
                focus=session_context.focus,
                stage=session_context.stage,
                duration_min=session_context.duration_min,
                exercise_names=session_context.exercise_names,
                completed_at=session_context.completed_at,
            )
        )

    workout_profile = db.get(WorkoutProfile, user.id)
    summary = daily_summary(db, user, local_day)

    return AssistantContext(
        date=local_day,
        goal=goal.goal,
        daily_calorie_target=goal.daily_calorie_target,
        dietary_preferences=profile.dietary_preferences,
        allergies=profile.allergies,
        nutrition_totals=NutritionContext(**summary.totals.model_dump()),
        meal_count=summary.meal_count,
        menu_meals=menu_meals,
        photo_meals=photo_meals,
        workouts=workouts,
        workout_profile=(
            WorkoutProfileContext(
                stage=workout_profile.stage,
                equipment=workout_profile.equipment,
                days_per_week=workout_profile.days_per_week,
            )
            if workout_profile is not None
            else None
        ),
    )
