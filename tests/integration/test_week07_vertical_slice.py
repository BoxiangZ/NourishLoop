from __future__ import annotations

from datetime import timedelta

from apps.api.core.config import Settings
from apps.api.core.models import utcnow
from apps.api.modules.recommendations.models import RecommendationJob
from apps.api.worker import process_once


def test_async_recommendation_to_confirmed_community_post(nl_stack):
    client, session_factory = nl_stack

    queued = client.post("/api/v1/recommendations/jobs", json={"meal_slot": "lunch", "limit": 3})
    assert queued.status_code == 202
    job_id = queued.json()["id"]
    assert queued.json()["status"] == "pending"
    assert queued.json()["run"] is None
    assert client.get(f"/api/v1/recommendations/jobs/{job_id}").json()["status"] == "pending"

    processed = process_once(session_factory, Settings(_env_file=None))
    assert processed == job_id
    completed = client.get(f"/api/v1/recommendations/jobs/{job_id}")
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["attempts"] == 1
    choices = completed.json()["run"]["recommendations"]
    assert len(choices) == 3
    assert choices[0]["explanation"]
    assert client.get("/api/v1/community/posts").json() == []

    planned = client.post(
        "/api/v1/decisions",
        json={"menu_item_id": choices[0]["menu_item"]["id"], "recommendation_id": choices[0]["id"]},
    )
    assert planned.status_code == 201
    assert client.get("/api/v1/me/daily-summary").json()["meal_count"] == 0
    confirmed = client.post(
        "/api/v1/meal-logs", json={"decision_id": planned.json()["id"], "servings": 1}
    )
    assert confirmed.status_code == 201
    assert client.get("/api/v1/me/daily-summary").json()["meal_count"] == 1

    shared = client.post(
        "/api/v1/community/posts",
        json={"meal_log_id": confirmed.json()["id"], "caption": "Lunch today"},
    )
    assert shared.status_code == 201
    assert shared.json()["meal"]["id"] == confirmed.json()["id"]
    assert len(client.get("/api/v1/community/posts").json()) == 1
    preflight = client.options(
        f"/api/v1/community/posts/{shared.json()['id']}",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "DELETE",
        },
    )
    assert preflight.status_code == 200
    assert "DELETE" in preflight.headers["access-control-allow-methods"]
    assert client.post(
        "/api/v1/community/posts",
        json={"meal_log_id": confirmed.json()["id"], "caption": "Again"},
    ).status_code == 409
    assert client.delete(f"/api/v1/community/posts/{shared.json()['id']}").status_code == 204
    assert client.get("/api/v1/community/posts").json() == []


def test_worker_reclaims_stale_job_and_keeps_baseline_on_provider_failure(nl_stack, monkeypatch):
    client, session_factory = nl_stack
    from apps.api.core.config import get_settings

    monkeypatch.setenv("EXPLANATION_PROVIDER", "openrouter")
    get_settings.cache_clear()
    queued = client.post("/api/v1/recommendations/jobs", json={})
    job_id = queued.json()["id"]
    with session_factory() as db:
        job = db.get(RecommendationJob, job_id)
        job.status = "claimed"
        job.claimed_at = utcnow() - timedelta(minutes=10)
        job.attempts = 1
        db.commit()

    class BrokenProvider:
        def explain(self, candidate, baseline):
            raise RuntimeError("temporary provider failure")

    process_once(
        session_factory,
        Settings(_env_file=None, explanation_provider="openrouter", worker_lease_seconds=30),
        provider_factory=lambda settings: BrokenProvider(),
    )
    result = client.get(f"/api/v1/recommendations/jobs/{job_id}").json()
    assert result["status"] == "completed"
    assert result["attempts"] == 2
    assert "Nutrition is an estimate" in result["run"]["recommendations"][0]["explanation"]
