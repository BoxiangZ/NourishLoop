from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.core.auth import current_user
from apps.api.core.database import get_db
from apps.api.modules.identity.models import User
from apps.api.modules.identity.schemas import (
    GoalRead,
    GoalUpdate,
    MeRead,
    ProfileRead,
    ProfileUpdate,
)
from apps.api.modules.identity.service import get_goal, get_profile, update_goal, update_profile

router = APIRouter(prefix="/api/v1", tags=["identity"])


@router.get("/me", response_model=MeRead)
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return MeRead(
        id=user.id,
        is_moderator=user.is_moderator,
        profile=ProfileRead.model_validate(get_profile(db, user)),
        goal=GoalRead.model_validate(get_goal(db, user)),
    )


@router.patch("/me/profile", response_model=ProfileRead)
def patch_profile(
    payload: ProfileUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return ProfileRead.model_validate(update_profile(db, user, payload))


@router.get("/me/goals", response_model=GoalRead)
def read_goals(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return GoalRead.model_validate(get_goal(db, user))


@router.put("/me/goals", response_model=GoalRead)
def put_goals(
    payload: GoalUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return GoalRead.model_validate(update_goal(db, user, payload))
