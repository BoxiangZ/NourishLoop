from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.core.auth import current_user
from apps.api.core.database import get_db
from apps.api.modules.identity.models import User
from apps.api.modules.workouts.schemas import (
    Equipment, ExerciseRead, Focus, WorkoutPlanRead, WorkoutProfileRead,
    WorkoutProfileUpdate, WorkoutRecommendRequest, WorkoutSessionCreate,
    WorkoutSessionRead,
)
from apps.api.modules.workouts.service import (
    complete_session, get_profile, list_exercises, list_sessions, recommend, update_profile,
)

router = APIRouter(prefix="/api/v1", tags=["workouts"])


@router.get("/exercises", response_model=list[ExerciseRead])
def exercises(
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    muscle_group: Focus | None = None, equipment: Equipment | None = None,
    q: str | None = Query(None, max_length=100), db: Session = Depends(get_db),
):
    return list_exercises(db, limit, offset, muscle_group, equipment, q)


@router.get("/me/workout-profile", response_model=WorkoutProfileRead)
def read_workout_profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return get_profile(db, user)


@router.put("/me/workout-profile", response_model=WorkoutProfileRead)
def save_workout_profile(
    payload: WorkoutProfileUpdate, user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return update_profile(db, user, payload)


@router.post("/workouts/recommend", response_model=WorkoutPlanRead, status_code=201)
def recommend_workout(
    payload: WorkoutRecommendRequest, user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return recommend(db, user, payload)


@router.post("/workouts/sessions", response_model=WorkoutSessionRead, status_code=201)
def log_workout(
    payload: WorkoutSessionCreate, user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return complete_session(db, user, payload)


@router.get("/me/workout-sessions", response_model=list[WorkoutSessionRead])
def workout_history(
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    user: User = Depends(current_user), db: Session = Depends(get_db),
):
    return list_sessions(db, user, limit, offset)
