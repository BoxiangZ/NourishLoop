from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.core.auth import current_user
from apps.api.core.database import get_db
from apps.api.modules.identity.models import User
from apps.api.modules.recommendations.schemas import (
    FeedbackCreate,
    RecommendationJobRead,
    RecommendationRequest,
    RecommendationRunRead,
)
from apps.api.modules.recommendations.service import add_feedback, enqueue, generate, get_job

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.post("/meals", response_model=RecommendationRunRead)
def recommend(
    payload: RecommendationRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return generate(db, user, payload)


@router.post("/jobs", response_model=RecommendationJobRead, status_code=202)
def create_job(
    payload: RecommendationRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return enqueue(db, user, payload)


@router.get("/jobs/{job_id}", response_model=RecommendationJobRead)
def read_job(
    job_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return get_job(db, user, job_id)


@router.post("/{recommendation_id}/feedback", status_code=204)
def recommendation_feedback(
    recommendation_id: str,
    payload: FeedbackCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    add_feedback(db, user, recommendation_id, payload)
