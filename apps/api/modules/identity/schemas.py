from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


GoalType = Literal["eat_healthier", "reduce_body_fat", "build_muscle"]
PreferenceType = Literal["vegan", "vegetarian", "high_protein", "high_fibre"]
AllergenType = Literal["soy", "wheat", "egg", "fish"]


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    dietary_preferences: list[PreferenceType] = Field(default_factory=list, max_length=20)
    allergies: list[AllergenType] = Field(default_factory=list, max_length=20)

    @field_validator("display_name")
    @classmethod
    def nonblank_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("display_name cannot be blank")
        return value


class ProfileRead(ProfileUpdate):
    user_id: str
    model_config = ConfigDict(from_attributes=True)


class GoalUpdate(BaseModel):
    goal: GoalType
    daily_calorie_target: float | None = Field(default=None, ge=1000, le=5000)


class GoalRead(GoalUpdate):
    user_id: str
    model_config = ConfigDict(from_attributes=True)


class MeRead(BaseModel):
    id: str
    is_moderator: bool
    profile: ProfileRead
    goal: GoalRead
