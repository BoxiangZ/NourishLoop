from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.core.database import Base
from apps.api.core.models import IdMixin, TimestampMixin, utcnow


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    muscle_group: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    equipment: Mapped[str] = mapped_column(String(30), nullable=False)
    equipment_detail: Mapped[str | None] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(30), nullable=False)
    instructions: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_photo: Mapped[dict[str, str] | None] = mapped_column(JSON(none_as_null=True))


class GymEquipment(Base, IdMixin):
    __tablename__ = "gym_equipment"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_checked_at: Mapped[date] = mapped_column(Date, nullable=False)


class WorkoutProfile(Base, TimestampMixin):
    __tablename__ = "workout_profiles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    stage: Mapped[str] = mapped_column(String(20), nullable=False, default="beginner")
    equipment: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    days_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=2)


class WorkoutPlan(Base, IdMixin, TimestampMixin):
    __tablename__ = "workout_plans"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    requested_focus: Mapped[str] = mapped_column(String(30), nullable=False)
    focus: Mapped[str] = mapped_column(String(30), nullable=False)
    stage: Mapped[str] = mapped_column(String(20), nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    prescription: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_source: Mapped[str] = mapped_column(String(20), nullable=False)


class WorkoutSession(Base, IdMixin):
    __tablename__ = "workout_sessions"
    __table_args__ = (UniqueConstraint("plan_id"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("workout_plans.id", ondelete="CASCADE"))
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
