from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.core.database import Base
from apps.api.core.models import IdMixin, TimestampMixin


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "users"

    is_moderator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    dietary_preferences: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    allergies: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    age: Mapped[int | None] = mapped_column(Integer)
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    target_weight_kg: Mapped[float | None] = mapped_column(Float)
    activity_level: Mapped[str | None] = mapped_column(String(16))
    meal_budget_hkd: Mapped[float | None] = mapped_column(Float)


class UserGoal(Base, TimestampMixin):
    __tablename__ = "user_goals"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    goal: Mapped[str] = mapped_column(String(30), nullable=False)
    daily_calorie_target: Mapped[float | None] = mapped_column(Float, nullable=True)


class UserConsent(Base):
    __tablename__ = "user_consents"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    analytics_opt_in: Mapped[bool] = mapped_column(default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
