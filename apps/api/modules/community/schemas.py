from __future__ import annotations

from datetime import datetime

from typing import Literal

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
    like_count: int
    liked_by_me: bool
    is_mine: bool
    comments: list["CommunityCommentRead"]


class CommunityCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=500)

    @field_validator("body")
    @classmethod
    def nonblank_body(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Comment must not be blank")
        return value.strip()


class CommunityCommentRead(BaseModel):
    id: str
    post_id: str
    author_display_name: str
    is_mine: bool
    body: str
    created_at: datetime


class CommunityReportCreate(BaseModel):
    reason: Literal["spam", "harassment", "misinformation", "other"]
    detail: str | None = Field(default=None, max_length=500)


class CommunityReportRead(BaseModel):
    id: str
    post_id: str
    post_caption: str
    post_author: str
    reason: str
    detail: str | None
    status: Literal["pending", "dismissed", "removed"]
    created_at: datetime


class CommunityReportResolve(BaseModel):
    action: Literal["dismiss", "remove"]
