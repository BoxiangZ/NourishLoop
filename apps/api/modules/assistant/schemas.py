from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

NonBlank160 = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)
]
NonBlank500 = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]
ActionText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=240)
]


class AssistantAskRequest(BaseModel):
    question: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ]


class AssistantAnswerRead(BaseModel):
    answer: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=600)
    ]


class DailyCoachReport(BaseModel):
    headline: NonBlank160
    nutrition_insight: NonBlank500
    activity_insight: NonBlank500
    next_actions: list[ActionText] = Field(max_length=3)
    limitations: list[ActionText] = Field(max_length=3)


class NutritionContext(BaseModel):
    calories_kcal: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0


class MenuMealContext(BaseModel):
    name: str
    servings: float
    consumed_at: datetime
    nutrition: NutritionContext


class PhotoMealContext(BaseModel):
    food_names: list[str]
    notes: str
    review_status: Literal[
        "not_requested", "pending", "processing", "completed", "failed"
    ]
    nutrition_status: Literal["complete", "partial", "none"]
    nutrition: NutritionContext | None
    unresolved_foods: list[str]


class WorkoutContext(BaseModel):
    focus: str
    stage: str
    duration_min: int
    exercise_names: list[str]
    completed_at: datetime


class WorkoutProfileContext(BaseModel):
    stage: str
    equipment: list[str]
    days_per_week: int


class AssistantContext(BaseModel):
    date: date
    goal: str
    daily_calorie_target: float | None
    dietary_preferences: list[str]
    allergies: list[str]
    nutrition_totals: NutritionContext
    meal_count: int
    menu_meals: list[MenuMealContext]
    photo_meals: list[PhotoMealContext]
    workouts: list[WorkoutContext]
    workout_profile: WorkoutProfileContext | None
