from __future__ import annotations


def test_lunch_decision_is_not_consumption_until_confirmed(nl_client):
    me = nl_client.get("/api/v1/me")
    assert me.status_code == 200
    assert me.json()["goal"]["goal"] == "reduce_body_fat"

    catalog = nl_client.get("/api/v1/menu-items")
    assert catalog.status_code == 200
    assert len(catalog.json()) == 6
    assert all(row["nutrition"]["provenance"] == "illustrative_estimate" for row in catalog.json())

    recommended = nl_client.post(
        "/api/v1/recommendations/meals", json={"meal_slot": "lunch", "limit": 3}
    )
    assert recommended.status_code == 200
    choices = recommended.json()["recommendations"]
    assert len(choices) == 3
    assert choices[0]["explanation"]

    selected = nl_client.post(
        "/api/v1/decisions",
        json={"menu_item_id": choices[0]["menu_item"]["id"], "recommendation_id": choices[0]["id"]},
    )
    assert selected.status_code == 201
    assert selected.json()["status"] == "planned"
    decision_id = selected.json()["id"]
    assert nl_client.get("/api/v1/me/daily-summary").json()["meal_count"] == 0

    confirmed = nl_client.post(
        "/api/v1/meal-logs", json={"decision_id": decision_id, "servings": 1.5}
    )
    assert confirmed.status_code == 201
    assert (
        confirmed.json()["nutrition"]["calories_kcal"]
        == choices[0]["menu_item"]["nutrition"]["calories_kcal"] * 1.5
    )
    assert nl_client.get("/api/v1/me/daily-summary").json()["meal_count"] == 1
    assert nl_client.get("/api/v1/me/decisions").json()[0]["status"] == "confirmed"
    assert nl_client.post("/api/v1/meal-logs", json={"decision_id": decision_id}).status_code == 409


def test_allergy_and_vegetarian_constraints(nl_client):
    response = nl_client.patch(
        "/api/v1/me/profile",
        json={"display_name": "Student", "dietary_preferences": ["vegan"], "allergies": ["soy"]},
    )
    assert response.status_code == 200
    recommended = nl_client.post("/api/v1/recommendations/meals", json={"meal_slot": "lunch"})
    assert recommended.status_code == 200
    choices = recommended.json()["recommendations"]
    assert choices
    assert all("vegan" in choice["menu_item"]["tags"] for choice in choices)
    assert all("soy" not in choice["menu_item"]["allergen_tags"] for choice in choices)


def test_feedback_and_validation(nl_client):
    recommendation = nl_client.post("/api/v1/recommendations/meals", json={}).json()[
        "recommendations"
    ][0]
    feedback = nl_client.post(
        f"/api/v1/recommendations/{recommendation['id']}/feedback", json={"helpful": True}
    )
    assert feedback.status_code == 204
    assert nl_client.post("/api/v1/meal-logs", json={"decision_id": "missing"}).status_code == 404
    assert nl_client.post("/api/v1/decisions", json={"menu_item_id": "missing"}).status_code == 404
    assert (
        nl_client.post(
            "/api/v1/meal-logs", json={"decision_id": "missing", "servings": 0}
        ).status_code
        == 422
    )


def test_demo_identity_is_disabled_outside_development(nl_client, monkeypatch):
    from apps.api.core import auth
    from apps.api.core.config import Settings

    monkeypatch.setattr(
        auth, "get_settings", lambda: Settings(app_env="production", demo_auth_enabled=True)
    )
    response = nl_client.get("/api/v1/me")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "http_503"
