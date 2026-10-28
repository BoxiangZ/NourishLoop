from __future__ import annotations

from datetime import date, datetime
from typing import Literal

import base64
import binascii

from pydantic import BaseModel, Field, field_validator

from apps.api.modules.catalog.schemas import MenuItemRead, NutritionFoodRead
from apps.api.modules.tracking.review import MealAIReview


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


class PhotoAnalysisRequest(BaseModel):
    image_base64: str = Field(min_length=1, max_length=7_000_000)
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]
    notes: str = Field(default="", max_length=500)

    @field_validator("image_base64")
    @classmethod
    def validate_image(cls, value: str) -> str:
        try:
            raw = base64.b64decode(value, validate=True)
        except binascii.Error:
            raise ValueError("Image must be valid base64") from None
        if not raw or len(raw) > 5_000_000:
            raise ValueError("Image must be 5 MB or smaller")
        return value


class PhotoFood(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    preparation: str | None = Field(default=None, max_length=120)
    quantity_from_notes: str | None = Field(default=None, max_length=120)
    estimated_grams: float | None = Field(default=None, gt=0, le=5000, allow_inf_nan=False)
    portion_basis: Literal["user_note", "visual_estimate", "unknown"] = "unknown"


class PhotoAnalysisRead(BaseModel):
    foods: list[PhotoFood] = Field(max_length=12)
    review_questions: list[str] = Field(max_length=8)
    model: str
    requires_review: Literal[False] = False
    ai_review: MealAIReview | None = None


class PhotoNutritionSelection(BaseModel):
    food_index: int = Field(ge=0, le=11)
    fdc_id: int = Field(gt=0)
    grams: float = Field(gt=0, le=5000, allow_inf_nan=False)
    portion_basis: Literal["user_note", "visual_estimate", "user_adjusted"] = "user_adjusted"


class PhotoAutoEstimateRequest(BaseModel):
    foods: list[PhotoFood] = Field(min_length=1, max_length=12)


class PhotoAutoMatchRead(BaseModel):
    food_index: int
    match: NutritionFoodRead | None = None
    reason: str | None = None


class PhotoAutoEstimateRead(BaseModel):
    estimate: PhotoNutritionEstimateRead | None = None
    partial_estimate: PhotoNutritionEstimateRead | None = None
    selections: list[PhotoNutritionSelection] = Field(default_factory=list)
    matches: list[PhotoAutoMatchRead] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)


class PhotoMealCreate(BaseModel):
    foods: list[PhotoFood] = Field(min_length=1, max_length=12)
    notes: str = Field(default="", max_length=500)
    model: str = Field(min_length=1, max_length=120)
    nutrition_selections: list[PhotoNutritionSelection] = Field(default_factory=list, max_length=12)
    ai_review: MealAIReview | None = None


class PhotoNutritionEstimateRequest(BaseModel):
    foods: list[PhotoFood] = Field(min_length=1, max_length=12)
    nutrition_selections: list[PhotoNutritionSelection] = Field(min_length=1, max_length=12)


class PhotoNutritionItemRead(BaseModel):
    name: str
    fdc_id: int
    source_description: str
    source_url: str
    grams: float
    portion_basis: Literal["user_note", "visual_estimate", "user_adjusted"] = "user_adjusted"
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float


class PhotoNutritionEstimateRead(BaseModel):
    nutrition: NutritionTotals
    items: list[PhotoNutritionItemRead]
    uncertainty_note: str = (
        "Approximate: USDA values are scaled by estimated edible grams. A photo cannot "
        "measure portion weight, cooking oil, sauces or hidden ingredients reliably."
    )


class PhotoMealRead(BaseModel):
    id: str
    foods: list[PhotoFood]
    notes: str
    model: str
    consumed_at: datetime
    nutrition: NutritionTotals | None = None
    nutrition_items: list[PhotoNutritionItemRead] = Field(default_factory=list)
    nutrition_status: Literal["complete", "partial", "none"] = "none"
    unresolved_foods: list[str] = Field(default_factory=list)
    review_status: Literal["not_requested", "pending", "processing", "completed", "failed"] = "not_requested"
    review_attempts: int = 0
    review_error: str | None = None
    ai_review: MealAIReview | None = None
    review_questions: list[str] = Field(default_factory=list)
