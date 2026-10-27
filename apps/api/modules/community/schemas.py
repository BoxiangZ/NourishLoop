from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from apps.api.modules.tracking.schemas import MealLogRead


class CommunityPostCreate(BaseModel):
    meal_log_id: str
    caption: str = Field(min_length=1, max_length=500)

    @field_validator("caption")
    @classmethod
    def nonblank_caption(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Caption must not be blank")
        return value.strip()


class CommunityPostRead(BaseModel):
    id: str
    author_display_name: str
    meal_log_id: str
    caption: str
    created_at: datetime
    meal: MealLogRead
