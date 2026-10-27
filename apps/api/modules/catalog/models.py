from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.core.database import Base
from apps.api.core.models import IdMixin, TimestampMixin


class Venue(Base, IdMixin, TimestampMixin):
    __tablename__ = "venues"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    campus_area: Mapped[str] = mapped_column(String(120), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MenuItem(Base, IdMixin, TimestampMixin):
    __tablename__ = "menu_items"

    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    allergen_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    price_hkd: Mapped[float | None] = mapped_column(Float, nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_label: Mapped[str] = mapped_column(String(160), nullable=False)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NutritionFact(Base):
    __tablename__ = "nutrition_facts"

    menu_item_id: Mapped[str] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True
    )
    calories_kcal: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_g: Mapped[float] = mapped_column(Float, nullable=False)
    basis: Mapped[str] = mapped_column(String(30), default="per_serving", nullable=False)
    provenance: Mapped[str] = mapped_column(String(30), nullable=False)
    uncertainty_note: Mapped[str] = mapped_column(String(240), nullable=False)
