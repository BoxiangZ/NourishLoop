from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from apps.api.real_sources import HKUST_SOURCE, HKUST_VENUES, LOHAS_SOURCE, LOHAS_VENUES
from apps.api.modules.workouts.models import WorkoutSession


def test_real_places_are_sourced_and_separate_from_demo_meals(nl_client):
    for scope, source, count in (
        ("hkust", HKUST_SOURCE, len(HKUST_VENUES)),
        ("lohas", LOHAS_SOURCE, len(LOHAS_VENUES)),
    ):
        all_rows = nl_client.get(f"/api/v1/venues?scope={scope}&limit=100").json()
        assert len(all_rows) == count
        assert all(not row["is_demo"] and row["source_url"] == source for row in all_rows)
        first = nl_client.get(f"/api/v1/venues?scope={scope}&limit=3&offset=0").json()
        second = nl_client.get(f"/api/v1/venues?scope={scope}&limit=3&offset=3").json()
        assert {row["id"] for row in first}.isdisjoint({row["id"] for row in second})
        assert nl_client.get(f"/api/v1/menu-items?venue_id={first[0]['id']}").json() == []
        notes = nl_client.get(f"/api/v1/external-notes?scope={scope}").json()
        assert notes and all(note["source_url"].startswith("https://www.reddit.com/")
                             for note in notes)
    assert nl_client.get("/api/v1/venues?offset=-1").status_code == 422


def test_stage_aware_workout_completion_recovery_and_rewards(nl_stack):
    nl_client, session_factory = nl_stack
    profile = nl_client.get("/api/v1/me/workout-profile").json()
    assert profile["stage"] == "beginner"
    saved = nl_client.put("/api/v1/me/workout-profile", json={
        "stage": "intermediate", "equipment": ["machine", "cable", "bodyweight"],
        "days_per_week": 2,
    })
    assert saved.status_code == 200
    assert saved.json()["stage"] == "intermediate"
    back = nl_client.get("/api/v1/exercises?muscle_group=back&limit=2&offset=0")
    next_back = nl_client.get("/api/v1/exercises?muscle_group=back&limit=2&offset=2")
    assert back.status_code == next_back.status_code == 200
    assert {row["id"] for row in back.json()}.isdisjoint(
        {row["id"] for row in next_back.json()}
    )
    request = {"focus": "back", "minutes": 30}
    planned = nl_client.post("/api/v1/workouts/recommend", json=request)
    assert planned.status_code == 201
    plan = planned.json()
    assert plan["stage"] == "intermediate" and plan["focus"] == "back"
    assert plan["explanation_source"] == "rules"
    assert len(plan["exercises"]) >= 2
    assert all(row["exercise"]["muscle_group"] == "back" for row in plan["exercises"])
    assert all(row["sets"] == 3 for row in plan["exercises"])
    assert nl_client.post("/api/v1/workouts/sessions", json={
        "plan_id": plan["id"], "duration_min": 30,
    }, headers={"X-Demo-User-Id": "demo-peer"}).status_code == 404
    completed = nl_client.post("/api/v1/workouts/sessions", json={
        "plan_id": plan["id"], "duration_min": 30,
    })
    assert completed.status_code == 201
    assert completed.json()["focus"] == "back"
    assert nl_client.post("/api/v1/workouts/sessions", json={
        "plan_id": plan["id"], "duration_min": 30,
    }).status_code == 409
    assert nl_client.get("/api/v1/rewards/overview").json()["balance"] == 5
    next_plan = nl_client.post("/api/v1/workouts/recommend", json=request)
    assert next_plan.status_code == 201
    assert next_plan.json()["requested_focus"] == "back"
    assert next_plan.json()["focus"] != "back"
    assert "recovery" in next_plan.json()["explanation"]
    assert nl_client.post("/api/v1/workouts/sessions", json={
        "plan_id": next_plan.json()["id"], "duration_min": 30,
    }).status_code == 201
    assert nl_client.get("/api/v1/rewards/overview").json()["balance"] == 5
    # Two distinct training days satisfy a two-day target; reward timing remains today.
    with session_factory() as db:
        first_session = db.scalar(select(WorkoutSession).where(
            WorkoutSession.plan_id == plan["id"]
        ))
        first_session.completed_at -= timedelta(days=1)
        db.commit()
    optional = nl_client.post("/api/v1/workouts/recommend", json={
        "focus": "chest", "minutes": 30,
    })
    assert optional.status_code == 201
    assert all(row["sets"] == 2 for row in optional.json()["exercises"])
    assert "2-day training target" in optional.json()["explanation"]
    first = nl_client.get("/api/v1/me/workout-sessions?limit=1&offset=0").json()
    second = nl_client.get("/api/v1/me/workout-sessions?limit=1&offset=1").json()
    assert len(first) == len(second) == 1 and first[0]["id"] != second[0]["id"]
    assert nl_client.get("/api/v1/workouts/recommend?focus=back").status_code == 405
    assert nl_client.post("/api/v1/workouts/recommend", json={
        "focus": "back", "minutes": 5,
    }).status_code == 422
