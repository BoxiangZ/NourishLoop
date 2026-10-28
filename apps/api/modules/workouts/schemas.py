from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Focus = Literal["back", "shoulders", "chest", "legs", "core"]
Stage = Literal["beginner", "intermediate", "advanced"]
Equipment = Literal["bodyweight", "machine", "dumbbell", "cable"]


class ExerciseRead(BaseModel):
    id: str
    name: str
    muscle_group: Focus
    equipment: Equipment
    difficulty: Stage
    instructions: str
    source_url: str
    model_config = ConfigDict(from_attributes=True)


class WorkoutProfileUpdate(BaseModel):
    stage: Stage
    equipment: list[Equipment] = Field(min_length=1, max_length=4)
    days_per_week: int = Field(ge=1, le=6)


class WorkoutProfileRead(WorkoutProfileUpdate):
    user_id: str
    model_config = ConfigDict(from_attributes=True)


class WorkoutRecommendRequest(BaseModel):
    focus: Focus
    minutes: int = Field(default=30, ge=15, le=75)


class ExercisePrescription(BaseModel):
    exercise: ExerciseRead
    sets: int
    reps: str
    rest_seconds: int


class WorkoutPlanRead(BaseModel):
    id: str
    requested_focus: Focus
    focus: Focus
    stage: Stage
    minutes: int
    exercises: list[ExercisePrescription]
    explanation: str
    explanation_source: Literal["rules", "openrouter"]
    created_at: datetime


class WorkoutSessionCreate(BaseModel):
    plan_id: str
    duration_min: int = Field(ge=5, le=180)


class WorkoutSessionRead(BaseModel):
    id: str
    plan_id: str
    focus: Focus
    stage: Stage
    duration_min: int
    exercise_names: list[str]
    completed_at: datetime
