"""Seven days of fictional activity for the development demo profile."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from apps.api.core.config import get_settings
from apps.api.modules.catalog.models import MenuItem, NutritionFact, Venue
from apps.api.modules.identity.models import User
from apps.api.modules.rewards.service import award_event
from apps.api.modules.tracking.models import Decision, MealLog, PhotoMealRecord
from apps.api.modules.workouts.models import Exercise, WorkoutPlan, WorkoutSession

HK_ZONE = ZoneInfo("Asia/Hong_Kong")
DEMO_USER_ID = "demo-student"
PRIOR_MEAL_NAMES = (
    "Chickpea salad",
    "Grilled tofu rice bowl",
    "Vegetable noodle bowl",
    "Chicken grain bowl",
    "Salmon quinoa plate",
    "Egg and avocado toast",
)
WORKOUTS_BY_OFFSET = {0: "back", 1: "legs", 3: "chest", 5: "core"}
PHOTO_NUTRITION = {
    "calories_kcal": 310,
    "protein_g": 18,
    "carbs_g": 38,
    "fat_g": 9,
}


def _activity_id(prefix: str, local_day, suffix: str) -> str:
    return f"{prefix}{local_day:%Y%m%d}-{suffix}"


def _at(local_day, hour: int, minute: int) -> datetime:
    return datetime.combine(local_day, time(hour, minute), tzinfo=HK_ZONE).astimezone(
        timezone.utc
    )


def _menu_with_nutrition(db: Session) -> dict[str, tuple[MenuItem, NutritionFact]]:
    required_names = {"Egg and avocado toast", *PRIOR_MEAL_NAMES}
    rows = db.execute(
        select(MenuItem, NutritionFact)
        .join(Venue, Venue.id == MenuItem.venue_id)
        .join(NutritionFact, NutritionFact.menu_item_id == MenuItem.id)
        .where(Venue.is_demo.is_(True), MenuItem.name.in_(required_names))
    ).all()
    by_name = {item.name: (item, nutrition) for item, nutrition in rows}
    missing = required_names - by_name.keys()
    if missing:
        raise RuntimeError(
            "Run the base demo seed first; missing fictional menu items: "
            + ", ".join(sorted(missing))
        )
    return by_name


def _add_menu_meal(
    db: Session,
    *,
    local_day,
    offset: int,
    item: MenuItem,
    nutrition: NutritionFact,
    consumed_at: datetime,
) -> MealLog:
    decision_id = _activity_id("demo-dec-", local_day, str(offset))
    log_id = _activity_id("demo-meal-", local_day, str(offset))
    if db.get(Decision, decision_id) is None:
        db.add(
            Decision(
                id=decision_id,
                user_id=DEMO_USER_ID,
                menu_item_id=item.id,
                status="confirmed",
                created_at=consumed_at,
            )
        )
        db.flush()

    log = db.get(MealLog, log_id)
    if log is None:
        log = MealLog(
            id=log_id,
            decision_id=decision_id,
            user_id=DEMO_USER_ID,
            menu_item_id=item.id,
            servings=1.0,
            consumed_at=consumed_at,
            nutrition_snapshot={
                "calories_kcal": nutrition.calories_kcal,
                "protein_g": nutrition.protein_g,
                "carbs_g": nutrition.carbs_g,
                "fat_g": nutrition.fat_g,
            },
        )
        db.add(log)
        db.flush()
    award_event(db, DEMO_USER_ID, "confirm_meal", "meal_log", log.id, log.consumed_at)
    return log


def _add_plan_decision(
    db: Session,
    *,
    local_day,
    suffix: str,
    item: MenuItem,
    created_at: datetime,
) -> None:
    decision_id = _activity_id("demo-plan-", local_day, suffix)
    if db.get(Decision, decision_id) is None:
        db.add(
            Decision(
                id=decision_id,
                user_id=DEMO_USER_ID,
                menu_item_id=item.id,
                status="planned",
                created_at=created_at,
            )
        )
        db.flush()


def _add_workout(
    db: Session,
    *,
    local_day,
    focus: str,
    exercises_by_focus: dict[str, list[Exercise]],
    completed: bool,
) -> None:
    suffix = "c" if completed else "a"
    plan_id = _activity_id("demo-wplan-", local_day, suffix)
    plan = db.get(WorkoutPlan, plan_id)
    if plan is None:
        plan = WorkoutPlan(
            id=plan_id,
            user_id=DEMO_USER_ID,
            requested_focus=focus,
            focus=focus,
            stage="beginner",
            minutes=30,
            prescription=[
                {
                    "exercise_id": exercise.id,
                    "sets": 2,
                    "reps": "10",
                    "rest_seconds": 60,
                }
                for exercise in exercises_by_focus[focus][:2]
            ],
            explanation="Fictional demo session for assistant context.",
            explanation_source="rules",
            created_at=_at(local_day, 7, 10),
        )
        db.add(plan)
        db.flush()

    if not completed:
        return

    session_id = _activity_id("demo-wsess-", local_day, suffix)
    session = db.get(WorkoutSession, session_id)
    if session is None:
        completed_at = _at(local_day, 18, 0)
        session = WorkoutSession(
            id=session_id,
            user_id=DEMO_USER_ID,
            plan_id=plan.id,
            duration_min=30,
            completed_at=completed_at,
        )
        db.add(session)
        db.flush()
    award_event(
        db,
        DEMO_USER_ID,
        "complete_workout",
        "workout_session",
        session.id,
        session.completed_at,
    )


def seed_demo_activity(db: Session, now: datetime | None = None) -> None:
    """Populate seven deterministic days for the development demo student."""
    settings = get_settings()
    if settings.app_env != "development":
        raise RuntimeError("Demo activity seed is available only in development")

    local_now = (now or datetime.now(timezone.utc)).astimezone(HK_ZONE)
    today = local_now.date()
    if db.get(User, DEMO_USER_ID) is None:
        raise RuntimeError("Run the base demo seed first; demo-student is missing")

    menu = _menu_with_nutrition(db)
    exercise_rows = db.scalars(
        select(Exercise).order_by(Exercise.muscle_group, Exercise.name, Exercise.id)
    ).all()
    exercises_by_focus: dict[str, list[Exercise]] = {}
    for exercise in exercise_rows:
        exercises_by_focus.setdefault(exercise.muscle_group, []).append(exercise)
    missing_focuses = set(WORKOUTS_BY_OFFSET.values()) | {"legs"}
    missing_focuses = {focus for focus in missing_focuses if not exercises_by_focus.get(focus)}
    if missing_focuses:
        raise RuntimeError(
            "Run the base demo seed first; missing exercise groups: "
            + ", ".join(sorted(missing_focuses))
        )

    db.execute(
        delete(Decision).where(
            Decision.user_id == DEMO_USER_ID,
            Decision.status == "planned",
            Decision.id.like("demo-plan-%"),
        )
    )
    db.execute(
        delete(WorkoutPlan).where(
            WorkoutPlan.user_id == DEMO_USER_ID,
            WorkoutPlan.id.like("demo-wplan-%"),
            ~exists(
                select(WorkoutSession.id).where(
                    WorkoutSession.plan_id == WorkoutPlan.id
                )
            ),
        )
    )
    db.flush()

    breakfast_day = today
    breakfast_item, breakfast_nutrition = menu["Egg and avocado toast"]
    _add_menu_meal(
        db,
        local_day=breakfast_day,
        offset=0,
        item=breakfast_item,
        nutrition=breakfast_nutrition,
        consumed_at=_at(breakfast_day, 8, 15),
    )

    for offset, name in enumerate(PRIOR_MEAL_NAMES, start=1):
        local_day = today - timedelta(days=offset)
        item, nutrition = menu[name]
        _add_menu_meal(
            db,
            local_day=local_day,
            offset=offset,
            item=item,
            nutrition=nutrition,
            consumed_at=_at(local_day, 12, 30),
        )

    photo_id = _activity_id("demo-photo-", today, "s")
    photo = db.get(PhotoMealRecord, photo_id)
    if photo is None:
        photo = PhotoMealRecord(
            id=photo_id,
            user_id=DEMO_USER_ID,
            foods=[{"name": "Greek yogurt"}, {"name": "Berries"}, {"name": "Granola"}],
            notes="Fictional demo photo meal: Greek yogurt, berries and granola.",
            model="demo_nutrition_review",
            consumed_at=_at(today, 16, 0),
            nutrition_snapshot=PHOTO_NUTRITION,
            nutrition_status="complete",
            unresolved_foods=[],
            review_status="completed",
        )
        db.add(photo)
        db.flush()
    award_event(
        db,
        DEMO_USER_ID,
        "confirm_meal",
        "photo_meal",
        photo.id,
        photo.consumed_at,
    )

    chicken = menu["Chicken grain bowl"][0]
    salmon = menu["Salmon quinoa plate"][0]
    _add_plan_decision(
        db,
        local_day=today,
        suffix="l",
        item=chicken,
        created_at=_at(today, 7, 0),
    )
    _add_plan_decision(
        db,
        local_day=today,
        suffix="d",
        item=salmon,
        created_at=_at(today, 7, 5),
    )

    for offset, focus in WORKOUTS_BY_OFFSET.items():
        local_day = today - timedelta(days=offset)
        _add_workout(
            db,
            local_day=local_day,
            focus=focus,
            exercises_by_focus=exercises_by_focus,
            completed=True,
        )
    _add_workout(
        db,
        local_day=today,
        focus="legs",
        exercises_by_focus=exercises_by_focus,
        completed=False,
    )

    db.commit()
