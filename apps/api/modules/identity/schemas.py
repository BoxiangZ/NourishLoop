from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


GoalType = Literal["eat_healthier", "reduce_body_fat", "build_muscle"]
PreferenceType = Literal["vegan", "vegetarian", "high_protein", "high_fibre"]
AllergenType = Literal["soy", "wheat", "egg", "fish"]
ActivityLevel = Literal["low", "light", "moderate", "high"]


class ProfileDetails(BaseModel):
    age: int | None = Field(default=None, ge=1, le=120)
    height_cm: float | None = Field(default=None, ge=30, le=275)
    weight_kg: float | None = Field(default=None, ge=2, le=700)
    target_weight_kg: float | None = Field(default=None, ge=2, le=700)
    activity_level: ActivityLevel | None = None
    meal_budget_hkd: float | None = Field(default=None, ge=0, le=5000)


class ProfileUpdate(ProfileDetails):
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
