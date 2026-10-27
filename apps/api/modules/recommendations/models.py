from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.core.database import Base
from apps.api.core.models import IdMixin, TimestampMixin


class RecommendationRun(Base, IdMixin, TimestampMixin):
    __tablename__ = "recommendation_runs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    meal_slot: Mapped[str] = mapped_column(String(20), nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(30), nullable=False)
    scoring_config: Mapped[dict] = mapped_column(JSON, nullable=False)


class RecommendationItem(Base, IdMixin):
    __tablename__ = "recommendation_items"
    __table_args__ = (UniqueConstraint("run_id", "menu_item_id"),)

    run_id: Mapped[str] = mapped_column(
        ForeignKey("recommendation_runs.id", ondelete="CASCADE"), index=True
    )
    menu_item_id: Mapped[str] = mapped_column(ForeignKey("menu_items.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)


class RecommendationFeedback(Base, IdMixin, TimestampMixin):
    __tablename__ = "recommendation_feedback"

    recommendation_item_id: Mapped[str] = mapped_column(
        ForeignKey("recommendation_items.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    helpful: Mapped[bool] = mapped_column(nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)


class RecommendationJob(Base, IdMixin, TimestampMixin):
    __tablename__ = "recommendation_jobs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    meal_slot: Mapped[str] = mapped_column(String(20), nullable=False)
    result_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(String(200), nullable=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("recommendation_runs.id"))
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
