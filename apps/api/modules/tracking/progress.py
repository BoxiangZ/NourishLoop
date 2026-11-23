from __future__ import annotations

from collections import Counter
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.models import utcnow
from apps.api.modules.identity.models import User
from apps.api.modules.rewards.models import HabitDefinition
from apps.api.modules.tracking.history import (
    confirmed_menu_meals, confirmed_photo_meals, day_bounds, local_day,
)
from apps.api.modules.tracking.models import Decision
from apps.api.modules.tracking.schemas import PlanProgressRead, PlanWeekRead
from apps.api.modules.tracking.service import decision_read
from apps.api.modules.workouts.models import WorkoutSession
from apps.api.modules.workouts.service import get_profile


def plan_progress(db: Session, user: User) -> PlanProgressRead:
    today = local_day(utcnow())
    monday = today - timedelta(days=today.weekday())
    first_week = monday - timedelta(weeks=3)
    start, end = day_bounds(first_week, today)
    menu = confirmed_menu_meals(db, user.id, start, end)
    photos = confirmed_photo_meals(db, user.id, start, end)
    meals_by_day = Counter(local_day(meal.consumed_at) for meal in (*menu, *photos))
    workout_times = db.scalars(select(WorkoutSession.completed_at).where(
        WorkoutSession.user_id == user.id,
        WorkoutSession.completed_at >= start, WorkoutSession.completed_at < end,
    ))
    training_days = {local_day(completed_at) for completed_at in workout_times}
    weeks = []
    for offset in range(4):
        week = first_week + timedelta(weeks=offset)
        next_week = week + timedelta(weeks=1)
        weeks.append(PlanWeekRead(
            starts_on=week,
            meal_days=sum(week <= day < next_week for day in meals_by_day),
            training_days=sum(week <= day < next_week for day in training_days),
        ))
    today_start, _ = day_bounds(today, today)
    planned = db.scalar(select(Decision).where(
        Decision.user_id == user.id, Decision.status == "planned",
        Decision.created_at >= today_start, Decision.created_at < end,
    ).order_by(Decision.created_at.desc(), Decision.id.desc()).limit(1))
    meal_habit = db.get(HabitDefinition, "confirm_meal")
    recent_start = today - timedelta(days=6)
    return PlanProgressRead(
        today=today, weeks=weeks, meal_days_target=meal_habit.weekly_target if meal_habit else None,
        training_days_target=get_profile(db, user).days_per_week,
        meals_today=meals_by_day[today],
        recent_meal_count=sum(count for day, count in meals_by_day.items() if day >= recent_start),
        planned_meal=decision_read(db, planned) if planned else None,
    )
