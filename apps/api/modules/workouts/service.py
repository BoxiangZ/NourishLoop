from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import get_settings
from apps.api.core.models import utcnow
from apps.api.modules.identity.models import User
from apps.api.modules.rewards.service import award_event
from apps.api.modules.workouts.ai import coach_explanation
from apps.api.modules.workouts.engine import select_routine
from apps.api.modules.workouts.models import Exercise, WorkoutPlan, WorkoutProfile, WorkoutSession
from apps.api.modules.workouts.schemas import (
    ExercisePrescription,
    ExerciseRead,
    WorkoutPlanRead,
    WorkoutProfileUpdate,
    WorkoutRecommendRequest,
    WorkoutSessionCreate,
    WorkoutSessionRead,
)


def list_exercises(
    db: Session,
    limit: int,
    offset: int,
    muscle_group: str | None,
    equipment: str | None,
    query: str | None,
) -> list[Exercise]:
    stmt = select(Exercise)
    if muscle_group:
        stmt = stmt.where(Exercise.muscle_group == muscle_group)
    if equipment:
        stmt = stmt.where(Exercise.equipment == equipment)
    if query:
        stmt = stmt.where(Exercise.name.ilike(f"%{query.strip()}%"))
    return list(db.scalars(stmt.order_by(Exercise.name, Exercise.id).offset(offset).limit(limit)))


def get_profile(db: Session, user: User) -> WorkoutProfile:
    profile = db.get(WorkoutProfile, user.id)
    if profile is None:
        profile = WorkoutProfile(
            user_id=user.id,
            stage="beginner",
            equipment=["bodyweight", "machine", "dumbbell", "cable"],
            days_per_week=2,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def update_profile(db: Session, user: User, payload: WorkoutProfileUpdate) -> WorkoutProfile:
    profile = get_profile(db, user)
    profile.stage = payload.stage
    profile.equipment = sorted(set(payload.equipment))
    profile.days_per_week = payload.days_per_week
    db.commit()
    db.refresh(profile)
    return profile


def plan_read(db: Session, plan: WorkoutPlan) -> WorkoutPlanRead:
    exercises = {
        item.id: item
        for item in db.scalars(
            select(Exercise).where(
                Exercise.id.in_([row["exercise_id"] for row in plan.prescription])
            )
        ).all()
    }
    return WorkoutPlanRead(
        id=plan.id,
        requested_focus=plan.requested_focus,
        focus=plan.focus,
        stage=plan.stage,
        minutes=plan.minutes,
        exercises=[
            ExercisePrescription(
                exercise=ExerciseRead.model_validate(exercises[row["exercise_id"]]),
                sets=row["sets"],
                reps=row["reps"],
                rest_seconds=row["rest_seconds"],
            )
            for row in plan.prescription
        ],
        explanation=plan.explanation,
        explanation_source=plan.explanation_source,
        created_at=plan.created_at,
    )


def recommend(db: Session, user: User, payload: WorkoutRecommendRequest) -> WorkoutPlanRead:
    profile = get_profile(db, user)
    exercises = db.scalars(select(Exercise)).all()
    recent_rows = db.execute(
        select(WorkoutPlan.focus, WorkoutSession.completed_at)
        .join(WorkoutSession, WorkoutSession.plan_id == WorkoutPlan.id)
        .where(WorkoutSession.user_id == user.id)
        .order_by(WorkoutSession.completed_at.desc())
        .limit(20)
    ).all()
    focus, prescription, baseline = select_routine(
        exercises,
        payload.focus,
        profile.stage,
        profile.equipment,
        profile.days_per_week,
        payload.minutes,
        list(recent_rows),
        utcnow(),
    )
    if not prescription:
        raise HTTPException(409, "No exercise matches this focus, stage and equipment")
    selected = {item.id: item for item in exercises}
    explanation, source = coach_explanation(
        get_settings(),
        baseline,
        profile.stage,
        [selected[row["exercise_id"]].name for row in prescription],
    )
    plan = WorkoutPlan(
        user_id=user.id,
        requested_focus=payload.focus,
        focus=focus,
        stage=profile.stage,
        minutes=payload.minutes,
        prescription=prescription,
        explanation=explanation,
        explanation_source=source,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan_read(db, plan)


def session_read(db: Session, session: WorkoutSession, plan: WorkoutPlan) -> WorkoutSessionRead:
    exercises = {
        item.id: item.name
        for item in db.scalars(
            select(Exercise).where(
                Exercise.id.in_([row["exercise_id"] for row in plan.prescription])
            )
        ).all()
    }
    return WorkoutSessionRead(
        id=session.id,
        plan_id=plan.id,
        focus=plan.focus,
        stage=plan.stage,
        duration_min=session.duration_min,
        exercise_names=[exercises[row["exercise_id"]] for row in plan.prescription],
        completed_at=session.completed_at,
    )


def complete_session(db: Session, user: User, payload: WorkoutSessionCreate) -> WorkoutSessionRead:
    plan = db.get(WorkoutPlan, payload.plan_id)
    if plan is None or plan.user_id != user.id:
        raise HTTPException(404, "Workout plan not found")
    if db.scalar(select(WorkoutSession.id).where(WorkoutSession.plan_id == plan.id)):
        raise HTTPException(409, "Workout already completed")
    session = WorkoutSession(
        user_id=user.id,
        plan_id=plan.id,
        duration_min=payload.duration_min,
        completed_at=utcnow(),
    )
    db.add(session)
    db.flush()
    award_event(
        db, user.id, "complete_workout", "workout_session", session.id, session.completed_at
    )
    db.commit()
    db.refresh(session)
    return session_read(db, session, plan)


def list_sessions(db: Session, user: User, limit: int, offset: int) -> list[WorkoutSessionRead]:
    rows = db.execute(
        select(WorkoutSession, WorkoutPlan)
        .join(WorkoutPlan, WorkoutSession.plan_id == WorkoutPlan.id)
        .where(WorkoutSession.user_id == user.id)
        .order_by(WorkoutSession.completed_at.desc(), WorkoutSession.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [session_read(db, session, plan) for session, plan in rows]
