from __future__ import annotations

from datetime import datetime

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.core.database import Base
from apps.api.core.models import IdMixin, TimestampMixin


class Venue(Base, IdMixin, TimestampMixin):
    __tablename__ = "venues"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    campus_area: Mapped[str] = mapped_column(String(120), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(20), default="demo", nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_checked_at: Mapped[date | None] = mapped_column(Date, nullable=True)


class PublishedDish(Base, IdMixin):
    __tablename__ = "published_dishes"

    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    price_hkd: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_scope: Mapped[str] = mapped_column(String(20), nullable=False)
    reference_note: Mapped[str] = mapped_column(String(240), nullable=False)
    source_checked_at: Mapped[date] = mapped_column(Date, nullable=False)
    source_photo: Mapped[dict[str, str] | None] = mapped_column(JSON(none_as_null=True))


class ExternalNote(Base, IdMixin):
    __tablename__ = "external_notes"

    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    source_platform: Mapped[str] = mapped_column(String(40), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_checked_at: Mapped[date] = mapped_column(Date, nullable=False)


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


class NutritionFood(Base):
    """A cached, source-backed USDA SR Legacy density (per 100 edible grams)."""

    __tablename__ = "nutrition_foods"

    fdc_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    data_type: Mapped[str] = mapped_column(String(30), nullable=False)
    calories_kcal: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    protein_g: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    carbs_g: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    fat_g: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
