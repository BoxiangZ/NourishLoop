from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from apps.api.modules.identity.models import User, UserGoal, UserProfile
from apps.api.modules.identity.schemas import GoalUpdate, ProfileDetails, ProfileUpdate


def get_profile(db: Session, user: User) -> UserProfile:
    profile = db.get(UserProfile, user.id)
    if profile is None:
        raise HTTPException(503, "Profile missing; run the seed command")
    return profile


def get_goal(db: Session, user: User) -> UserGoal:
    goal = db.get(UserGoal, user.id)
    if goal is None:
        raise HTTPException(503, "Goal missing; run the seed command")
    return goal


def update_profile(db: Session, user: User, payload: ProfileUpdate) -> UserProfile:
    profile = get_profile(db, user)
    profile.display_name = payload.display_name
    profile.dietary_preferences = sorted(
        set(x.lower().strip() for x in payload.dietary_preferences)
    )
    profile.allergies = sorted(set(x.lower().strip() for x in payload.allergies))
    supplied_details = payload.model_dump(
        include=set(ProfileDetails.model_fields), exclude_unset=True,
    )
    for field, value in supplied_details.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def update_goal(db: Session, user: User, payload: GoalUpdate) -> UserGoal:
    goal = get_goal(db, user)
    goal.goal = payload.goal
    goal.daily_calorie_target = payload.daily_calorie_target
    db.commit()
    db.refresh(goal)
    return goal
