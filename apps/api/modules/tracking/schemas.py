from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from apps.api.modules.catalog.schemas import MenuItemRead


class DecisionCreate(BaseModel):
    menu_item_id: str
    recommendation_id: str | None = None


class DecisionRead(BaseModel):
    id: str
    status: Literal["planned", "confirmed"]
    created_at: datetime
    menu_item: MenuItemRead


class MealLogCreate(BaseModel):
    decision_id: str
    servings: float = Field(default=1.0, gt=0, le=10)


class NutritionTotals(BaseModel):
    calories_kcal: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0


class MealLogRead(BaseModel):
    id: str
    decision_id: str
    servings: float
    consumed_at: datetime
    nutrition: NutritionTotals
    menu_item: MenuItemRead


class DailySummary(BaseModel):
    date: date
    timezone: str = "Asia/Hong_Kong"
    meal_count: int
    totals: NutritionTotals
