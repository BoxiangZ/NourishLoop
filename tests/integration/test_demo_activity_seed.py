from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select

from apps.api.core.config import Settings
from apps.api.modules.catalog.models import MenuItem, NutritionFact
from apps.api.modules.rewards.models import CreditTransaction, HabitEvent
from apps.api.modules.tracking.models import Decision, MealLog, PhotoMealRecord
from apps.api.modules.workouts.models import Exercise, WorkoutPlan, WorkoutSession


HK = ZoneInfo("Asia/Hong_Kong")
NOW = datetime(2026, 11, 23, 9, 0, tzinfo=HK)


def _hong_kong_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(HK)


def _activity_counts(db) -> dict[str, int]:
    return {
        model.__tablename__: db.scalar(select(func.count()).select_from(model))
        for model in (
            Decision,
            MealLog,
            PhotoMealRecord,
            WorkoutPlan,
            WorkoutSession,
            HabitEvent,
            CreditTransaction,
        )
    }


def test_demo_activity_refuses_non_development(monkeypatch, nl_stack):
    _, session_factory = nl_stack
    import apps.api.demo_activity as demo_activity

    monkeypatch.setattr(
        demo_activity,
        "get_settings",
        lambda: Settings(_env_file=None, app_env="production"),
    )
    with session_factory() as db:
        with pytest.raises(RuntimeError, match="development"):
            demo_activity.seed_demo_activity(db, now=NOW)
        assert _activity_counts(db) == {
            "user_decisions": 0,
            "meal_logs": 0,
            "photo_meal_records": 0,
            "workout_plans": 0,
            "workout_sessions": 0,
            "habit_events": 0,
            "credit_transactions": 0,
        }


def test_demo_activity_populates_seven_days_without_peer_activity(nl_stack):
    from apps.api.demo_activity import seed_demo_activity

    _, session_factory = nl_stack
    with session_factory() as db:
        seed_demo_activity(db, now=NOW)

    with session_factory() as db:
        menu_rows = db.execute(
            select(MealLog, MenuItem)
            .join(MenuItem, MenuItem.id == MealLog.menu_item_id)
            .where(MealLog.id.like("demo-meal-%"))
        ).all()
        meals_by_day = {
            _hong_kong_datetime(log.consumed_at).date(): item.name
            for log, item in menu_rows
        }
        assert meals_by_day == {
            date(2026, 11, 23): "Egg and avocado toast",
            date(2026, 11, 22): "Chickpea salad",
            date(2026, 11, 21): "Grilled tofu rice bowl",
            date(2026, 11, 20): "Vegetable noodle bowl",
            date(2026, 11, 19): "Chicken grain bowl",
            date(2026, 11, 18): "Salmon quinoa plate",
            date(2026, 11, 17): "Egg and avocado toast",
        }
        today_breakfast = next(
            log
            for log, item in menu_rows
            if _hong_kong_datetime(log.consumed_at).date() == date(2026, 11, 23)
            and item.name == "Egg and avocado toast"
        )
        assert _hong_kong_datetime(today_breakfast.consumed_at).strftime("%H:%M") == "08:15"

        nutrition_by_item = {
            fact.menu_item_id: fact for fact in db.scalars(select(NutritionFact)).all()
        }
        for log, _ in menu_rows:
            fact = nutrition_by_item[log.menu_item_id]
            assert log.nutrition_snapshot == {
                "calories_kcal": fact.calories_kcal,
                "protein_g": fact.protein_g,
                "carbs_g": fact.carbs_g,
                "fat_g": fact.fat_g,
            }

        photo = db.scalar(
            select(PhotoMealRecord).where(PhotoMealRecord.id.like("demo-photo-%"))
        )
        assert photo is not None
        assert photo.user_id == "demo-student"
        assert [food["name"] for food in photo.foods] == [
            "Greek yogurt",
            "Berries",
            "Granola",
        ]
        assert _hong_kong_datetime(photo.consumed_at) == datetime(
            2026, 11, 23, 16, 0, tzinfo=HK
        )
        assert photo.nutrition_snapshot == {
            "calories_kcal": 310,
            "protein_g": 18,
            "carbs_g": 38,
            "fat_g": 9,
        }
        assert photo.nutrition_status == "complete"
        assert photo.review_status in {"not_requested", "completed"}

        planned = db.execute(
            select(Decision, MenuItem)
            .join(MenuItem, MenuItem.id == Decision.menu_item_id)
            .where(
                Decision.id.like("demo-plan-%"),
                Decision.status == "planned",
            )
        ).all()
        assert {item.name for _, item in planned} == {
            "Chicken grain bowl",
            "Salmon quinoa plate",
        }
        assert {
            _hong_kong_datetime(decision.created_at).strftime("%H:%M")
            for decision, _ in planned
        } == {"07:00", "07:05"}

        workout_rows = db.execute(
            select(WorkoutSession, WorkoutPlan)
            .join(WorkoutPlan, WorkoutPlan.id == WorkoutSession.plan_id)
            .where(WorkoutSession.id.like("demo-wsess-%"))
        ).all()
        assert len(workout_rows) == 4
        assert {
            _hong_kong_datetime(session.completed_at).date() for session, _ in workout_rows
        } == {
            datetime(2026, 11, 23).date() - timedelta(days=offset)
            for offset in (0, 1, 3, 5)
        }
        assert all(session.duration_min == 30 for session, _ in workout_rows)

        unfinished = db.scalars(
            select(WorkoutPlan)
            .outerjoin(WorkoutSession, WorkoutSession.plan_id == WorkoutPlan.id)
            .where(
                WorkoutPlan.id.like("demo-wplan-%"),
                WorkoutSession.id.is_(None),
            )
        ).all()
        assert [(plan.focus, plan.minutes, plan.stage) for plan in unfinished] == [
            ("legs", 30, "beginner")
        ]

        habit_events = db.scalars(
            select(HabitEvent).where(HabitEvent.user_id == "demo-student")
        ).all()
        meal_days = {
            event.local_day for event in habit_events if event.habit_id == "confirm_meal"
        }
        workout_days = {
            event.local_day
            for event in habit_events
            if event.habit_id == "complete_workout"
        }
        assert meal_days == {
            date(2026, 11, 23) - timedelta(days=offset) for offset in range(7)
        }
        assert workout_days == {
            date(2026, 11, 23) - timedelta(days=offset) for offset in (0, 1, 3, 5)
        }

        assert db.scalar(
            select(func.count()).select_from(Decision).where(
                Decision.user_id == "demo-peer"
            )
        ) == 0
        assert db.scalar(
            select(func.count()).select_from(MealLog).where(
                MealLog.user_id == "demo-peer"
            )
        ) == 0
        assert db.scalar(
            select(func.count()).select_from(PhotoMealRecord).where(
                PhotoMealRecord.user_id == "demo-peer"
            )
        ) == 0
        assert db.scalar(
            select(func.count()).select_from(WorkoutPlan).where(
                WorkoutPlan.user_id == "demo-peer"
            )
        ) == 0
        assert db.scalar(
            select(func.count()).select_from(WorkoutSession).where(
                WorkoutSession.user_id == "demo-peer"
            )
        ) == 0


def test_demo_activity_is_idempotent_on_the_same_hong_kong_day(nl_stack):
    from apps.api.demo_activity import seed_demo_activity

    _, session_factory = nl_stack
    later_same_day = datetime(2026, 11, 23, 23, 55, tzinfo=HK)
    with session_factory() as db:
        seed_demo_activity(db, now=NOW)
        first_counts = _activity_counts(db)

    with session_factory() as db:
        seed_demo_activity(db, now=later_same_day)
        second_counts = _activity_counts(db)

    assert first_counts == second_counts
    assert first_counts == {
        "user_decisions": 9,
        "meal_logs": 7,
        "photo_meal_records": 1,
        "workout_plans": 5,
        "workout_sessions": 4,
        "habit_events": 11,
        "credit_transactions": 11,
    }


def test_demo_activity_replaces_stale_unfinished_seeded_workout_plan(nl_stack):
    from apps.api.demo_activity import seed_demo_activity

    _, session_factory = nl_stack
    next_day = NOW + timedelta(days=1)
    with session_factory() as db:
        seed_demo_activity(db, now=NOW)
        prior_log_ids = set(
            db.scalars(select(MealLog.id).where(MealLog.id.like("demo-meal-%"))).all()
        )
        prior_photo_ids = set(
            db.scalars(
                select(PhotoMealRecord.id).where(
                    PhotoMealRecord.id.like("demo-photo-%")
                )
            ).all()
        )
        prior_session_ids = set(
            db.scalars(
                select(WorkoutSession.id).where(
                    WorkoutSession.id.like("demo-wsess-%")
                )
            ).all()
        )
        prior_completed_plan_ids = set(
            db.scalars(
                select(WorkoutPlan.id)
                .join(WorkoutSession, WorkoutSession.plan_id == WorkoutPlan.id)
                .where(WorkoutPlan.id.like("demo-wplan-%"))
            ).all()
        )
        exercise_id = db.scalar(select(Exercise.id).limit(1))
        db.add(
            WorkoutPlan(
                id="user-owned-wplan",
                user_id="demo-student",
                requested_focus="legs",
                focus="legs",
                stage="beginner",
                minutes=20,
                prescription=[
                    {
                        "exercise_id": exercise_id,
                        "sets": 1,
                        "reps": "8",
                        "rest_seconds": 60,
                    }
                ],
                explanation="User-owned plan",
                explanation_source="rules",
            )
        )
        db.commit()

    with session_factory() as db:
        seed_demo_activity(db, now=next_day)
        assert prior_log_ids <= set(
            db.scalars(select(MealLog.id).where(MealLog.id.like("demo-meal-%"))).all()
        )
        assert prior_photo_ids <= set(
            db.scalars(
                select(PhotoMealRecord.id).where(
                    PhotoMealRecord.id.like("demo-photo-%")
                )
            ).all()
        )
        assert prior_session_ids <= set(
            db.scalars(
                select(WorkoutSession.id).where(
                    WorkoutSession.id.like("demo-wsess-%")
                )
            ).all()
        )
        assert prior_completed_plan_ids <= set(
            db.scalars(
                select(WorkoutPlan.id)
                .join(WorkoutSession, WorkoutSession.plan_id == WorkoutPlan.id)
                .where(WorkoutPlan.id.like("demo-wplan-%"))
            ).all()
        )
        assert db.get(WorkoutPlan, "user-owned-wplan") is not None

        unfinished_seeded = db.scalars(
            select(WorkoutPlan)
            .outerjoin(WorkoutSession, WorkoutSession.plan_id == WorkoutPlan.id)
            .where(
                WorkoutPlan.user_id == "demo-student",
                WorkoutPlan.id.like("demo-wplan-%"),
                WorkoutSession.id.is_(None),
            )
        ).all()
        assert [
            (
                plan.id,
                plan.focus,
                _hong_kong_datetime(plan.created_at).date(),
            )
            for plan in unfinished_seeded
        ] == [("demo-wplan-20261124-a", "legs", date(2026, 11, 24))]

        for model in (Decision, MealLog, PhotoMealRecord, WorkoutPlan, WorkoutSession):
            assert db.scalar(
                select(func.count())
                .select_from(model)
                .where(model.user_id == "demo-peer")
            ) == 0


def test_demo_activity_deletes_only_stale_planned_seed_decisions(nl_stack):
    from apps.api.demo_activity import seed_demo_activity

    _, session_factory = nl_stack
    with session_factory() as db:
        seed_demo_activity(db, now=NOW)
        item_id = db.scalar(select(MenuItem.id).limit(1))
        db.add_all(
            [
                Decision(
                    id="demo-plan-20261120-stale",
                    user_id="demo-student",
                    menu_item_id=item_id,
                    status="planned",
                ),
                Decision(
                    id="demo-plan-20261121-kept",
                    user_id="demo-student",
                    menu_item_id=item_id,
                    status="confirmed",
                ),
                Decision(
                    id="user-owned-plan",
                    user_id="demo-student",
                    menu_item_id=item_id,
                    status="planned",
                ),
            ]
        )
        db.commit()

    with session_factory() as db:
        seed_demo_activity(db, now=NOW)
        assert db.get(Decision, "demo-plan-20261120-stale") is None
        assert db.get(Decision, "demo-plan-20261121-kept") is not None
        assert db.get(Decision, "user-owned-plan") is not None
        planned_demo_ids = set(
            db.scalars(
                select(Decision.id).where(
                    Decision.user_id == "demo-student",
                    Decision.id.like("demo-plan-%"),
                    Decision.status == "planned",
                )
            ).all()
        )
        assert planned_demo_ids == {
            "demo-plan-20261123-l",
            "demo-plan-20261123-d",
        }


def test_demo_activity_ids_fit_the_database_limit(nl_stack):
    from apps.api.demo_activity import seed_demo_activity

    _, session_factory = nl_stack
    with session_factory() as db:
        seed_demo_activity(db, now=NOW)
        ids = [
            *db.scalars(select(Decision.id).where(Decision.id.like("demo-%"))).all(),
            *db.scalars(select(MealLog.id).where(MealLog.id.like("demo-%"))).all(),
            *db.scalars(
                select(PhotoMealRecord.id).where(PhotoMealRecord.id.like("demo-%"))
            ).all(),
            *db.scalars(
                select(WorkoutPlan.id).where(WorkoutPlan.id.like("demo-%"))
            ).all(),
            *db.scalars(
                select(WorkoutSession.id).where(WorkoutSession.id.like("demo-%"))
            ).all(),
        ]

    assert ids
    assert all(len(identifier) <= 36 for identifier in ids)


def test_standalone_demo_activity_script_loads_complete_model_registry(tmp_path):
    from apps.api.core.database import Base, make_engine, make_session_factory
    from apps.api.seed import seed

    database_path = tmp_path / "standalone-demo-activity.db"
    engine = make_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(bind=engine)
    session_factory = make_session_factory(engine)
    with session_factory() as db:
        seed(db)
    engine.dispose()

    environment = os.environ.copy()
    environment.update(
        APP_ENV="development",
        DATABASE_URL=f"sqlite:///{database_path}",
        DEMO_AUTH_ENABLED="true",
    )
    repository_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "scripts.seed_demo_activity"],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Seeded seven days of fictional demo activity." in result.stdout
