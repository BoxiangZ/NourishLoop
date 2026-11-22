from datetime import datetime, timezone

from apps.api.modules.assistant.context import build_today_context
from apps.api.modules.assistant.schemas import AssistantAskRequest, DailyCoachReport
from apps.api.modules.identity.models import User
from apps.api.modules.workouts.models import WorkoutProfile


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
    menu_item = client.get("/api/v1/menu-items").json()[0]
    decision = client.post(
        "/api/v1/decisions", json={"menu_item_id": menu_item["id"]}
    ).json()
    client.post(
        "/api/v1/meal-logs", json={"decision_id": decision["id"], "servings": 1}
    )
    client.post(
        "/api/v1/decisions", json={"menu_item_id": menu_item["id"]}
    )

    workout = client.post(
        "/api/v1/workouts/recommend", json={"focus": "back", "minutes": 30}
    ).json()
    client.post(
        "/api/v1/workouts/sessions",
        json={"plan_id": workout["id"], "duration_min": 30},
    )
    client.post(
        "/api/v1/workouts/recommend", json={"focus": "legs", "minutes": 30}
    )

    with session_factory() as db:
        user = db.get(User, "demo-student")
        context = build_today_context(db, user)

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
    decision = client.post(
        "/api/v1/decisions", json={"menu_item_id": menu_item["id"]}
    ).json()
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
        context = build_today_context(db, db.get(User, "demo-student"))

    assert context.meal_count == 1
    assert len(context.photo_meals) == 1
    assert context.photo_meals[0].food_names == ["Rice", "Tofu"]
    assert context.photo_meals[0].notes == "Lunch"
    serialized = context.model_dump_json()
    assert "image_path" not in serialized
    assert "display_name" not in serialized
    assert "Demo Student" not in serialized
    assert "vision-test" not in serialized


def test_context_does_not_create_a_missing_workout_profile(nl_stack):
    _, session_factory = nl_stack

    with session_factory() as db:
        profile = db.get(WorkoutProfile, "demo-student")
        db.delete(profile)
        db.commit()

        context = build_today_context(db, db.get(User, "demo-student"))

        assert context.workout_profile is None
        assert db.get(WorkoutProfile, "demo-student") is None
