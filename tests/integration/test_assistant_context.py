from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from apps.api.modules.assistant.context import build_today_context
from apps.api.modules.assistant.schemas import AssistantAskRequest, DailyCoachReport
from apps.api.modules.catalog.models import MenuItem, Venue
from apps.api.modules.identity.models import User
from apps.api.modules.tracking.models import Decision, MealLog, PhotoMealRecord
from apps.api.modules.workouts.models import Exercise, WorkoutPlan, WorkoutProfile, WorkoutSession


def test_ask_request_trims_question_and_rejects_blank_values():
    assert AssistantAskRequest(question="  dinner?  ").question == "dinner?"

    try:
        AssistantAskRequest(question="   ")
    except ValueError:
        pass
    else:
        raise AssertionError("blank question should fail")


def test_report_contract_rejects_more_than_three_actions():
    try:
        DailyCoachReport(
            headline="Today",
            nutrition_insight="Meals logged.",
            activity_insight="No completed workout yet.",
            next_actions=["one", "two", "three", "four"],
            limitations=[],
        )
    except ValueError:
        pass
    else:
        raise AssertionError("four actions should fail")


def test_context_includes_only_confirmed_today_food_and_completed_workouts(nl_stack):
    client, session_factory = nl_stack
    fixed_day = date(2026, 11, 23)
    menu_item = client.get("/api/v1/menu-items").json()[0]
    decision = client.post("/api/v1/decisions", json={"menu_item_id": menu_item["id"]}).json()
    client.post("/api/v1/meal-logs", json={"decision_id": decision["id"], "servings": 1})
    client.post("/api/v1/decisions", json={"menu_item_id": menu_item["id"]})

    workout = client.post(
        "/api/v1/workouts/recommend", json={"focus": "back", "minutes": 30}
    ).json()
    workout_session = client.post(
        "/api/v1/workouts/sessions",
        json={"plan_id": workout["id"], "duration_min": 30},
    ).json()
    client.post("/api/v1/workouts/recommend", json={"focus": "legs", "minutes": 30})

    with session_factory() as db:
        user = db.get(User, "demo-student")
        logged = db.execute(select(MealLog).where(MealLog.user_id == user.id)).scalar_one()
        logged.consumed_at = datetime(2026, 11, 23, 4, 0, tzinfo=timezone.utc)
        session_row = db.get(WorkoutSession, workout_session["id"])
        session_row.completed_at = datetime(2026, 11, 23, 5, 0, tzinfo=timezone.utc)
        db.commit()
        context = build_today_context(db, user, day=fixed_day)

    assert context.meal_count == 1
    assert len(context.menu_meals) == 1
    assert context.menu_meals[0].name == menu_item["name"]
    assert len(context.workouts) == 1
    assert context.workouts[0].duration_min == 30
    assert "user_id" not in context.model_dump_json()


def test_context_uses_hong_kong_day_boundaries(nl_stack):
    client, session_factory = nl_stack
    from apps.api.modules.tracking.models import MealLog

    menu_item = client.get("/api/v1/menu-items").json()[0]
    decision = client.post("/api/v1/decisions", json={"menu_item_id": menu_item["id"]}).json()
    logged = client.post(
        "/api/v1/meal-logs", json={"decision_id": decision["id"], "servings": 1}
    ).json()

    with session_factory() as db:
        row = db.get(MealLog, logged["id"])
        row.consumed_at = datetime(2026, 11, 22, 15, 59, tzinfo=timezone.utc)
        db.commit()
        user = db.get(User, "demo-student")
        context = build_today_context(db, user, day=datetime(2026, 11, 23).date())

    assert context.menu_meals == []


def test_context_includes_saved_photo_meal_without_private_fields(nl_stack):
    client, session_factory = nl_stack
    fixed_day = date(2026, 11, 23)
    saved = client.post(
        "/api/v1/photo-meals",
        json={
            "foods": [{"name": "Rice"}, {"name": "Tofu"}],
            "notes": "Lunch",
            "model": "vision-test",
            "ai_review": {
                "is_food": True,
                "detected_foods": ["Rice", "Tofu"],
                "estimated_nutrition": {
                    "calories_kcal": 420,
                    "protein_g": 18,
                    "carbs_g": 62,
                    "fat_g": 10,
                },
                "confidence": 0.7,
                "summary": "Rice and tofu",
                "assumptions": ["Portion is estimated"],
            },
        },
    )
    assert saved.status_code == 201

    with session_factory() as db:
        user = db.get(User, "demo-student")
        photo = db.execute(
            select(PhotoMealRecord).where(PhotoMealRecord.user_id == user.id)
        ).scalar_one()
        photo.consumed_at = datetime(2026, 11, 23, 4, 0, tzinfo=timezone.utc)
        db.commit()
        context = build_today_context(db, user, day=fixed_day)

    assert context.meal_count == 1
    assert len(context.photo_meals) == 1
    assert context.photo_meals[0].food_names == ["Rice", "Tofu"]
    assert context.photo_meals[0].notes == "Lunch"
    serialized = context.model_dump_json()
    assert "image_path" not in serialized
    assert "display_name" not in serialized
    assert "Demo Student" not in serialized
    assert "vision-test" not in serialized


@pytest.mark.parametrize("review_status", ["not_requested", "completed"])
def test_context_includes_complete_nutrition_for_confirmed_photo_reviews(nl_stack, review_status):
    _, session_factory = nl_stack
    fixed_day = date(2026, 11, 23)

    with session_factory() as db:
        user = db.get(User, "demo-student")
        db.add(
            PhotoMealRecord(
                user_id=user.id,
                foods=[{"name": f"{review_status} food"}],
                notes=f"{review_status} note",
                model="test-model",
                consumed_at=datetime(2026, 11, 23, 4, 0, tzinfo=timezone.utc),
                nutrition_snapshot={
                    "calories_kcal": 400,
                    "protein_g": 20,
                    "carbs_g": 40,
                    "fat_g": 10,
                },
                nutrition_status="complete",
                unresolved_foods=[],
                review_status=review_status,
            )
        )
        db.commit()

        context = build_today_context(db, user, day=fixed_day)

    assert context.meal_count == 1
    assert len(context.photo_meals) == 1
    assert context.photo_meals[0].review_status == review_status
    assert context.photo_meals[0].nutrition_status == "complete"
    assert context.photo_meals[0].nutrition is not None
    assert context.photo_meals[0].nutrition.calories_kcal == 400


@pytest.mark.parametrize("review_status", ["pending", "processing", "failed"])
def test_context_omits_nutrition_for_status_only_photo_reviews(nl_stack, review_status):
    _, session_factory = nl_stack
    fixed_day = date(2026, 11, 23)

    with session_factory() as db:
        user = db.get(User, "demo-student")
        db.add(
            PhotoMealRecord(
                user_id=user.id,
                foods=[{"name": f"{review_status} food"}],
                notes=f"{review_status} note",
                model="test-model",
                consumed_at=datetime(2026, 11, 23, 4, 0, tzinfo=timezone.utc),
                nutrition_snapshot={
                    "calories_kcal": 999,
                    "protein_g": 9,
                    "carbs_g": 9,
                    "fat_g": 9,
                },
                nutrition_status="complete",
                unresolved_foods=[],
                review_status=review_status,
            )
        )
        db.commit()

        context = build_today_context(db, user, day=fixed_day)

    assert context.meal_count == 0
    assert len(context.photo_meals) == 1
    assert context.photo_meals[0].review_status == review_status
    assert context.photo_meals[0].nutrition_status == "none"
    assert context.photo_meals[0].nutrition is None
    assert context.nutrition_totals.model_dump() == {
        "calories_kcal": 0,
        "protein_g": 0,
        "carbs_g": 0,
        "fat_g": 0,
    }


def test_context_photo_facts_and_daily_aggregate_agree_for_instant_photo(nl_stack):
    _, session_factory = nl_stack
    fixed_day = date(2026, 11, 23)

    with session_factory() as db:
        user = db.get(User, "demo-student")
        rows = [
            ("not_requested", "complete", 320, 20, 40, 10),
            ("completed", "complete", 180, 10, 20, 5),
            ("not_requested", "partial", 70, 3, 5, 2),
            ("not_requested", "none", None, None, None, None),
            ("pending", "complete", 500, 30, 50, 20),
        ]
        for minute, (status, nutrition_status, calories, protein, carbs, fat) in enumerate(rows):
            snapshot = (
                {
                    "calories_kcal": calories,
                    "protein_g": protein,
                    "carbs_g": carbs,
                    "fat_g": fat,
                }
                if calories is not None
                else None
            )
            db.add(
                PhotoMealRecord(
                    user_id=user.id,
                    foods=[{"name": f"{status} {nutrition_status} food"}],
                    notes="",
                    model="test-model",
                    consumed_at=datetime(2026, 11, 23, 4, minute, tzinfo=timezone.utc),
                    nutrition_snapshot=snapshot,
                    nutrition_status=nutrition_status,
                    unresolved_foods=[],
                    review_status=status,
                )
            )
        db.commit()

        context = build_today_context(db, user, day=fixed_day)

    confirmed_rows = [
        photo
        for photo in context.photo_meals
        if photo.review_status in ("completed", "not_requested")
    ]
    complete_nutrition = [
        photo.nutrition
        for photo in confirmed_rows
        if photo.nutrition_status == "complete" and photo.nutrition is not None
    ]
    partial_row = next(
        photo for photo in context.photo_meals if photo.nutrition_status == "partial"
    )

    assert context.meal_count == len(confirmed_rows) == 4
    assert context.nutrition_totals.calories_kcal == sum(
        nutrition.calories_kcal for nutrition in complete_nutrition
    )
    assert context.nutrition_totals.protein_g == sum(
        nutrition.protein_g for nutrition in complete_nutrition
    )
    assert context.nutrition_totals.carbs_g == sum(
        nutrition.carbs_g for nutrition in complete_nutrition
    )
    assert context.nutrition_totals.fat_g == sum(
        nutrition.fat_g for nutrition in complete_nutrition
    )
    assert context.nutrition_totals.calories_kcal == 500
    assert partial_row.review_status == "not_requested"
    assert partial_row.nutrition is not None
    assert partial_row.nutrition.calories_kcal == 70


def test_context_scopes_meal_photo_and_workout_records_to_current_user(nl_stack):
    _, session_factory = nl_stack
    fixed_day = date(2026, 11, 23)
    consumed_at = datetime(2026, 11, 23, 4, 0, tzinfo=timezone.utc)

    with session_factory() as db:
        venue_id = db.scalar(select(Venue.id).limit(1))
        exercise = db.scalar(select(Exercise).limit(1))
        peer_exercise = Exercise(
            id=f"peer-exercise-{uuid4().hex}",
            name="PEER_EXERCISE",
            muscle_group="back",
            equipment="machine",
            difficulty="beginner",
            instructions="",
            source_url="https://example.org/peer-exercise",
        )
        current_user = db.get(User, "demo-student")
        peer_user = db.get(User, "demo-peer")

        current_item = MenuItem(
            id=f"current-item-{uuid4().hex}",
            venue_id=venue_id,
            name="CURRENT_PRIVATE_MEAL",
            description="",
            category="meal",
            tags=[],
            allergen_tags=[],
            available=True,
            source_label="fictional demo data",
        )
        peer_item = MenuItem(
            id=f"peer-item-{uuid4().hex}",
            venue_id=venue_id,
            name="PEER_PRIVATE_MEAL",
            description="",
            category="meal",
            tags=[],
            allergen_tags=[],
            available=True,
            source_label="fictional demo data",
        )
        db.add_all([current_item, peer_item, peer_exercise])
        db.flush()

        current_decision = Decision(
            id=f"current-decision-{uuid4().hex}",
            user_id=current_user.id,
            menu_item_id=current_item.id,
            status="confirmed",
        )
        peer_decision = Decision(
            id=f"peer-decision-{uuid4().hex}",
            user_id=peer_user.id,
            menu_item_id=peer_item.id,
            status="confirmed",
        )
        db.add_all([current_decision, peer_decision])
        db.flush()

        db.add_all(
            [
                MealLog(
                    id=f"current-log-{uuid4().hex}",
                    decision_id=current_decision.id,
                    user_id=current_user.id,
                    menu_item_id=current_item.id,
                    servings=1,
                    consumed_at=consumed_at,
                    nutrition_snapshot={
                        "calories_kcal": 1,
                        "protein_g": 1,
                        "carbs_g": 1,
                        "fat_g": 1,
                    },
                ),
                MealLog(
                    id=f"peer-log-{uuid4().hex}",
                    decision_id=peer_decision.id,
                    user_id=peer_user.id,
                    menu_item_id=peer_item.id,
                    servings=1,
                    consumed_at=consumed_at,
                    nutrition_snapshot={
                        "calories_kcal": 2,
                        "protein_g": 2,
                        "carbs_g": 2,
                        "fat_g": 2,
                    },
                ),
                PhotoMealRecord(
                    id=f"current-photo-{uuid4().hex}",
                    user_id=current_user.id,
                    foods=[{"name": "CURRENT_PHOTO_FOOD"}],
                    notes="CURRENT_PHOTO_NOTE",
                    model="test-model",
                    consumed_at=consumed_at,
                    nutrition_snapshot={
                        "calories_kcal": 1,
                        "protein_g": 1,
                        "carbs_g": 1,
                        "fat_g": 1,
                    },
                    nutrition_status="complete",
                    unresolved_foods=[],
                    review_status="completed",
                ),
                PhotoMealRecord(
                    id=f"peer-photo-{uuid4().hex}",
                    user_id=peer_user.id,
                    foods=[{"name": "PEER_PHOTO_FOOD"}],
                    notes="PEER_PHOTO_NOTE",
                    model="test-model",
                    consumed_at=consumed_at,
                    nutrition_snapshot={
                        "calories_kcal": 2,
                        "protein_g": 2,
                        "carbs_g": 2,
                        "fat_g": 2,
                    },
                    nutrition_status="complete",
                    unresolved_foods=[],
                    review_status="completed",
                ),
            ]
        )

        current_plan = WorkoutPlan(
            id=f"current-plan-{uuid4().hex}",
            user_id=current_user.id,
            requested_focus="back",
            focus="back",
            stage="beginner",
            minutes=30,
            prescription=[{"exercise_id": exercise.id, "sets": 1, "reps": "1", "rest_seconds": 60}],
            explanation="",
            explanation_source="rules",
        )
        peer_plan = WorkoutPlan(
            id=f"peer-plan-{uuid4().hex}",
            user_id=peer_user.id,
            requested_focus="legs",
            focus="legs",
            stage="beginner",
            minutes=77,
            prescription=[
                {"exercise_id": peer_exercise.id, "sets": 1, "reps": "1", "rest_seconds": 60}
            ],
            explanation="",
            explanation_source="rules",
        )
        db.add_all([current_plan, peer_plan])
        db.flush()
        db.add_all(
            [
                WorkoutSession(
                    id=f"current-session-{uuid4().hex}",
                    user_id=current_user.id,
                    plan_id=current_plan.id,
                    duration_min=30,
                    completed_at=consumed_at,
                ),
                WorkoutSession(
                    id=f"peer-session-{uuid4().hex}",
                    user_id=peer_user.id,
                    plan_id=peer_plan.id,
                    duration_min=77,
                    completed_at=consumed_at,
                ),
            ]
        )
        db.commit()

        context = build_today_context(db, current_user, day=fixed_day)

    serialized = context.model_dump_json()
    assert "CURRENT_PRIVATE_MEAL" in serialized
    assert "CURRENT_PHOTO_NOTE" in serialized
    assert "CURRENT_PHOTO_FOOD" in serialized
    assert "PEER_EXERCISE" not in serialized
    assert "PEER_PRIVATE_MEAL" not in serialized
    assert "PEER_PHOTO_NOTE" not in serialized
    assert "PEER_PHOTO_FOOD" not in serialized
    assert '"focus":"legs"' not in serialized
    assert '"duration_min":77' not in serialized


def test_context_does_not_create_a_missing_workout_profile(nl_stack):
    _, session_factory = nl_stack

    with session_factory() as db:
        profile = db.get(WorkoutProfile, "demo-student")
        db.delete(profile)
        db.commit()

        context = build_today_context(db, db.get(User, "demo-student"))

        assert context.workout_profile is None
        assert db.get(WorkoutProfile, "demo-student") is None
