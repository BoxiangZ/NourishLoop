from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from apps.api.modules.catalog.schemas import MenuItemRead


class RecommendationRequest(BaseModel):
    meal_slot: Literal["breakfast", "lunch", "dinner"] = "lunch"
    limit: int = Field(default=3, ge=1, le=10)


class RecommendationRead(BaseModel):
    id: str
    rank: int
    score: float
    explanation: str
    confidence: Literal["low", "medium", "high"]
    confidence_reason: str
    menu_item: MenuItemRead


class RecommendationRunRead(BaseModel):
    id: str
    scoring_version: str
    meal_slot: str
    recommendations: list[RecommendationRead]


class RecommendationJobRead(BaseModel):
    id: str
    status: Literal["pending", "claimed", "completed", "failed"]
    attempts: int
    provider: Literal["deterministic", "openrouter"]
    error: str | None
    created_at: datetime
    completed_at: datetime | None
    run: RecommendationRunRead | None


class FeedbackCreate(BaseModel):
    helpful: bool
    comment: str | None = Field(default=None, max_length=500)
