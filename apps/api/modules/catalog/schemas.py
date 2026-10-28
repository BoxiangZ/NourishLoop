from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class NutritionFoodRead(BaseModel):
    fdc_id: int
    description: str
    data_type: str
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    source_url: str


class VenueRead(BaseModel):
    id: str
    name: str
    campus_area: str
    is_demo: bool
    scope: str
    source_url: str | None
    source_checked_at: date | None
    model_config = ConfigDict(from_attributes=True)


class ExternalNoteRead(BaseModel):
    id: str
    scope: str
    title: str
    summary: str
    source_platform: str
    source_url: str
    source_checked_at: date
    model_config = ConfigDict(from_attributes=True)


class NutritionRead(BaseModel):
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    basis: str
    provenance: str
    uncertainty_note: str
    model_config = ConfigDict(from_attributes=True)


class MenuItemRead(BaseModel):
    id: str
    venue_id: str
    name: str
    description: str
    category: str
    tags: list[str]
    allergen_tags: list[str]
    price_hkd: float | None
    available: bool
    source_label: str
    observed_at: datetime | None
    nutrition: NutritionRead


def menu_item_read(item, nutrition) -> MenuItemRead:
    return MenuItemRead(
        **{
            **{key: getattr(item, key) for key in MenuItemRead.model_fields if key != "nutrition"},
            "nutrition": NutritionRead.model_validate(nutrition),
        }
    )
