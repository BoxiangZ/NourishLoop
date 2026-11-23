from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.modules.tracking.models import MealLog, PhotoMealRecord

HONG_KONG = ZoneInfo("Asia/Hong_Kong")


def local_day(when: datetime) -> date:
    if when.tzinfo is None:  # SQLite returns naive UTC values for timezone-aware columns.
        when = when.replace(tzinfo=timezone.utc)
    return when.astimezone(HONG_KONG).date()


def day_bounds(start: date, through: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(start, time.min, HONG_KONG).astimezone(timezone.utc),
        datetime.combine(through + timedelta(days=1), time.min, HONG_KONG).astimezone(timezone.utc),
    )


def confirmed_menu_meals(
    db: Session, user_id: str, start: datetime, end: datetime,
) -> list[MealLog]:
    return list(db.scalars(select(MealLog).where(
        MealLog.user_id == user_id, MealLog.consumed_at >= start, MealLog.consumed_at < end,
    )))


def confirmed_photo_meals(
    db: Session, user_id: str, start: datetime, end: datetime,
) -> list[PhotoMealRecord]:
    return list(db.scalars(select(PhotoMealRecord).where(
        PhotoMealRecord.user_id == user_id,
        PhotoMealRecord.consumed_at >= start,
        PhotoMealRecord.consumed_at < end,
        PhotoMealRecord.review_status.in_(("not_requested", "completed")),
    )))
