from datetime import datetime, timedelta, timezone

from apps.api.core.config import Settings
from apps.api.modules.recommendations import service as recommendations
from apps.api.modules.tracking import progress
from apps.api.modules.tracking.models import Decision, MealLog, PhotoMealRecord
from apps.api.modules.workouts.models import WorkoutSession
from apps.api.worker import process_once


def test_confirmed_history_changes_the_plan_and_the_next_recommendation(nl_stack, monkeypatch):
    client, factory = nl_stack
    now = datetime(2026, 11, 22, 17, tzinfo=timezone.utc)  # Monday in Hong Kong.
    monkeypatch.setattr(progress, "utcnow", lambda: now)
    monkeypatch.setattr(recommendations, "utcnow", lambda: now)

    initial = client.post("/api/v1/recommendations/meals", json={}).json()
    first_choice = initial["recommendations"][0]["menu_item"]
    dish = {"menu_item_id": first_choice["id"]}
    pending = client.post("/api/v1/decisions", json=dish).json()
    with factory() as db:
        db.get(Decision, pending["id"]).created_at = now
        db.commit()
    empty_week = client.get("/api/v1/me/plan-progress").json()
    assert len(empty_week["weeks"]) == 4
    assert empty_week["planned_meal"]["id"] == pending["id"]
    assert empty_week["meals_today"] == empty_week["weeks"][-1]["meal_days"] == 0

    meal_ids = []
    for decision in (pending, client.post("/api/v1/decisions", json=dish).json()):
        log = client.post("/api/v1/meal-logs", json={"decision_id": decision["id"]})
        assert log.status_code == 201
        meal_ids.append(log.json()["id"])

    plan = client.post("/api/v1/workouts/recommend", json={}).json()
    workout = client.post(
        "/api/v1/workouts/sessions", json={"plan_id": plan["id"], "duration_min": 30},
    )
    assert workout.status_code == 201
    with factory() as db:
        for days_ago, meal_id in enumerate(meal_ids, start=1):
            db.get(MealLog, meal_id).consumed_at = now - timedelta(days=days_ago)
        db.get(WorkoutSession, workout.json()["id"]).completed_at = now
        for status in ("not_requested", "completed", "pending", "failed"):
            db.add(PhotoMealRecord(
                user_id="demo-student", model="fixture", foods=[], review_status=status,
                consumed_at=now - timedelta(days=1) if status == "not_requested" else now,
            ))
        db.commit()

    summary = client.get("/api/v1/me/plan-progress").json()
    assert summary["today"] == "2026-11-23"
    assert summary["planned_meal"] is None and summary["meals_today"] == 1
    assert summary["recent_meal_count"] == 4
    assert summary["weeks"][-2]["meal_days"] == 2
    assert summary["weeks"][-1] == {
        "starts_on": "2026-11-23", "meal_days": 1, "training_days": 1,
    }
    peer = client.get("/api/v1/me/plan-progress", headers={"X-Demo-User-Id": "demo-peer"}).json()
    assert peer["meals_today"] == 0 and peer["weeks"][-1]["training_days"] == 0

    queued = client.post("/api/v1/recommendations/jobs", json={}).json()
    assert process_once(factory, Settings(_env_file=None)) == queued["id"]
    run = client.get(f"/api/v1/recommendations/jobs/{queued['id']}").json()["run"]
    assert run["history_context"] == {
        "window_start": "2026-11-17", "through_date": "2026-11-23", "confirmed_meals": 4,
        "meal_days": 3, "repeated_dishes": [first_choice["name"]],
    }
    assert run["recommendations"][0]["menu_item"]["id"] != first_choice["id"]
    assert "adds variety" in run["recommendations"][0]["explanation"]
