from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlsplit

from sqlalchemy import select

from apps.api.real_sources import (
    HKUST_SOURCE, HKUST_VENUES, LOCAL_VENUES, LOHAS_SOURCE, LOHAS_VENUES,
)
from apps.api.modules.workouts.models import WorkoutSession


def test_real_places_are_sourced_and_separate_from_demo_meals(nl_client):
    for scope, source, count in (
        ("hkust", HKUST_SOURCE, len(HKUST_VENUES) + sum(row[0] == "hkust" for row in LOCAL_VENUES)),
        ("lohas", LOHAS_SOURCE, len(LOHAS_VENUES)),
    ):
        all_rows = nl_client.get(f"/api/v1/venues?scope={scope}&limit=100").json()
        assert len(all_rows) == count
        assert all(not row["is_demo"] and row["source_url"] == source for row in all_rows)
        first = nl_client.get(f"/api/v1/venues?scope={scope}&limit=3&offset=0").json()
        second = nl_client.get(f"/api/v1/venues?scope={scope}&limit=3&offset=3").json()
        assert {row["id"] for row in first}.isdisjoint({row["id"] for row in second})
        assert nl_client.get(f"/api/v1/menu-items?venue_id={first[0]['id']}").json() == []
    assert nl_client.get("/api/v1/venues?offset=-1").status_code == 422


def test_local_reviews_respect_scope_and_pagination(nl_client):
    first = nl_client.get("/api/v1/external-notes?scope=all&limit=6").json()
    second = nl_client.get("/api/v1/external-notes?scope=all&limit=6&offset=6").json()
    assert len(first) == len(second) == 6
    assert {note["id"] for note in first}.isdisjoint(note["id"] for note in second)

    notes = nl_client.get("/api/v1/external-notes?scope=all&limit=50").json()
    assert {note["scope"] for note in notes} == {"hkust", "tko", "hang_hau", "lohas", "tai_po_tsai"}
    domains = {"Reddit": "www.reddit.com", "OpenRice": "www.openrice.com"}
    for note in notes:
        assert urlsplit(note["source_url"]).hostname == domains[note["source_platform"]]

    hang_hau = nl_client.get("/api/v1/external-notes?scope=hang_hau").json()
    assert hang_hau == [note for note in notes if note["scope"] == "hang_hau"]
    assert {note["source_platform"] for note in hang_hau} == {"Reddit", "OpenRice"}
    assert nl_client.get("/api/v1/external-notes?scope=unknown").status_code == 422
    assert nl_client.get("/api/v1/community/posts").json() == []


def test_published_menus_are_searchable_without_inventing_nutrition(nl_client):
    donburi = nl_client.get("/api/v1/published-dishes?scope=hkust&q=照燒煎雞丼").json()
    assert len(donburi) == 1
    dish = donburi[0]
    assert dish["venue"]["name"] == "Donburi Bowl" and dish["price_hkd"] == 37
    assert dish["source_url"].endswith("DONBURI%20Bowls%20Menu.pdf")
    assert "nutrition" not in dish and "allergen_tags" not in dish
    assert dish["source_photo"] is None
    assert nl_client.get(f"/api/v1/menu-items/{dish['id']}").status_code == 404

    first_page = nl_client.get("/api/v1/published-dishes?scope=hkust&limit=2").json()
    assert len(first_page) == 2 and all(row["source_photo"] for row in first_page)
    big_mac = nl_client.get("/api/v1/published-dishes?scope=hkust&q=Big%20Mac").json()[0]
    assert big_mac["source_photo"]["source_url"].endswith("/product/big-mac/")

    for scope in ("hang_hau", "tko", "lohas", "tai_po_tsai"):
        rows = nl_client.get(f"/api/v1/published-dishes?scope={scope}&limit=2").json()
        assert rows and all(row["venue"]["scope"] == scope for row in rows)
    village = nl_client.get("/api/v1/published-dishes?scope=tai_po_tsai&q=椒香").json()
    assert len(village) == 1 and village[0]["price_hkd"] is None


def test_workout_equipment_has_separate_campus_and_movement_sources(nl_client):
    equipment = nl_client.get("/api/v1/workouts/equipment").json()
    assert any(row["name"] == "Rowing ergometer" for row in equipment)
    assert all(row["source_url"].startswith("https://dst.hkust.edu.hk/") for row in equipment)
    exercise = nl_client.get("/api/v1/exercises?q=Seated%20leg%20extension").json()[0]
    assert exercise["equipment_detail"] == "Leg extension machine"
    assert exercise["source_url"].endswith("/183/seated-leg-extension/")
    assert exercise["source_photo"]["source_url"] == exercise["source_url"]


def test_menu_location_filters_to_the_selected_mall(nl_client):
    locations = nl_client.get("/api/v1/menu-locations").json()
    assert len(locations) == 14
    assert {location["scope"] for location in locations} == {
        "hkust", "tko", "hang_hau", "lohas", "tai_po_tsai",
    }
    for location in locations:
        assert urlsplit(location["source_url"]).hostname == "www.openstreetmap.org"
        assert 22 < location["latitude"] < 23 and 114 < location["longitude"] < 115
        rows = nl_client.get(
            "/api/v1/published-dishes", params={"location_id": location["id"], "limit": 1},
        ).json()
        assert rows and rows[0]["venue"]["scope"] == location["scope"]

    rows = nl_client.get(
        "/api/v1/published-dishes",
        params={"scope": "tko", "location_id": "park-central", "q": "sushi"},
    ).json()
    assert rows and {row["venue"]["name"] for row in rows} == {"Genki Sushi · Park Central"}
    rows = nl_client.get("/api/v1/published-dishes?scope=tko&location_id=popcorn-2").json()
    assert rows and {row["venue"]["name"] for row in rows} == {"Café de Coral · PopCorn 2"}
    assert nl_client.get("/api/v1/published-dishes?location_id=unknown").status_code == 404


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


def test_automatic_workout_uses_only_available_equipment_and_rotates_focus(nl_client):
    assert nl_client.put("/api/v1/me/workout-profile", json={
        "stage": "beginner", "equipment": ["bodyweight"], "days_per_week": 2,
    }).status_code == 200
    response = nl_client.post("/api/v1/workouts/recommend", json={})
    assert response.status_code == 201
    plan = response.json()
    assert plan["minutes"] == 30
    assert plan["exercises"] and all(
        row["exercise"]["equipment"] == "bodyweight" for row in plan["exercises"]
    )
    assert nl_client.get("/api/v1/me/workout-sessions").json() == []
    assert nl_client.post("/api/v1/workouts/sessions", json={
        "plan_id": plan["id"], "duration_min": plan["minutes"],
    }).status_code == 201
    next_plan = nl_client.post("/api/v1/workouts/recommend", json={})
    assert next_plan.status_code == 201
    assert next_plan.json()["focus"] != plan["focus"]
