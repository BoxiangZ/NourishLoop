from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.core.database import Base
from apps.api.core.models import IdMixin, TimestampMixin


class Decision(Base, IdMixin, TimestampMixin):
    __tablename__ = "user_decisions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    menu_item_id: Mapped[str] = mapped_column(ForeignKey("menu_items.id"), nullable=False)
    recommendation_item_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendation_items.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="planned", nullable=False)


class MealLog(Base, IdMixin, TimestampMixin):
    __tablename__ = "meal_logs"

    decision_id: Mapped[str] = mapped_column(
        ForeignKey("user_decisions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    menu_item_id: Mapped[str] = mapped_column(ForeignKey("menu_items.id"), nullable=False)
    servings: Mapped[float] = mapped_column(Float, nullable=False)
    consumed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    nutrition_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)


class PhotoMealRecord(Base, IdMixin, TimestampMixin):
    """User-confirmed food names from a photo; the image itself is never stored."""

    __tablename__ = "photo_meal_records"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    foods: Mapped[list] = mapped_column(JSON, nullable=False)
    notes: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    consumed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    nutrition_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    nutrition_items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    nutrition_status: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    unresolved_foods: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
