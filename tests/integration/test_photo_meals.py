from __future__ import annotations

import base64
import importlib
import json

import httpx
import pytest
from fastapi import HTTPException
from pydantic import SecretStr
from sqlalchemy import select

from apps.api.core.config import Settings
from apps.api.modules.catalog.nutrition import search_nutrition_foods
from apps.api.modules.tracking.models import PhotoMealRecord
from apps.api.modules.tracking.photo import analyze_photo
from apps.api.modules.tracking.photo import _best_match
from apps.api.modules.tracking.schemas import PhotoAnalysisRead, PhotoAnalysisRequest, PhotoFood
from apps.api.modules.catalog.schemas import NutritionFoodRead


def test_vision_payload_and_reviewed_foods() -> None:
    captured = {}

    def response(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": (
            '{"foods":[{"name":"Rice","preparation":null,'
            '"quantity_from_notes":"half a bowl","estimated_grams":100},'
            '{"name":"Rice","estimated_grams":150}],"review_questions":[]}'
        )}}]})

    image = base64.b64encode(b"\xff\xd8\xfftest-image").decode()
    result = analyze_photo(PhotoAnalysisRequest(
        image_base64=image, mime_type="image/jpeg", notes="half a bowl",
    ), Settings(openrouter_api_key=SecretStr("test-key"), openrouter_model="vision-test"),
        httpx.MockTransport(response))
    assert result.foods[0].name == "Rice"
    assert len(result.foods) == 1
    assert result.foods[0].estimated_grams == 150
    assert not result.requires_review
    assert captured["messages"][0]["content"][1]["image_url"]["url"] == (
        f"data:image/jpeg;base64,{image}"
    )
    assert captured["reasoning"] == {"enabled": False}
    assert captured["max_tokens"] == 1500


def test_photo_record_counts_without_inventing_nutrition(nl_stack, monkeypatch):
    client, session_factory = nl_stack
    router = importlib.import_module("apps.api.modules.tracking.router")
    monkeypatch.setattr(router, "analyze_photo", lambda *_: PhotoAnalysisRead(
        foods=[{"name": "Rice", "preparation": None, "quantity_from_notes": None}],
        review_questions=["How much rice?"], model="vision-test",
    ))
    image = base64.b64encode(b"\xff\xd8\xfftest-image").decode()
    analyzed = client.post("/api/v1/meals/analyze-photo", json={
        "image_base64": image, "mime_type": "image/jpeg",
    })
    assert analyzed.status_code == 200
    assert analyzed.json()["foods"][0]["name"] == "Rice"
    saved = client.post("/api/v1/photo-meals", json={
        "foods": [{"name": "Rice and tofu", "preparation": "steamed"}],
        "notes": "I ate this for lunch", "model": analyzed.json()["model"],
    })
    assert saved.status_code == 201
    record = saved.json()
    assert record["foods"][0]["name"] == "Rice and tofu"
    assert record["nutrition_status"] == "none"
    assert client.get("/api/v1/me/photo-meals?limit=1&offset=0").json()[0]["id"] == record["id"]
    assert client.get("/api/v1/me/photo-meals", headers={"X-Demo-User-Id": "demo-peer"}).json() == []
    summary = client.get("/api/v1/me/daily-summary").json()
    assert summary["meal_count"] == 1
    assert summary["totals"]["calories_kcal"] == 0
    assert client.get("/api/v1/rewards/overview").json()["balance"] == 5
    with session_factory() as db:
        row = db.scalar(select(PhotoMealRecord).where(PhotoMealRecord.id == record["id"]))
        assert row is not None and not hasattr(row, "image_base64")


def test_source_backed_photo_nutrition_preview_confirmation_and_daily_total(nl_stack):
    client, session_factory = nl_stack

    def usda_response(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"foods": [{
            "fdcId": 173423, "description": "Egg, whole, cooked, fried",
            "dataType": "SR Legacy", "foodNutrients": [
                {"nutrientId": 1008, "value": 196},
                {"nutrientId": 1003, "value": 13.6},
                {"nutrientId": 1005, "value": 0.83},
                {"nutrientId": 1004, "value": 14.8},
            ],
        }]})

    with session_factory() as db:
        foods = search_nutrition_foods(
            db, "egg fried", 6, Settings(usda_api_key=SecretStr("DEMO_KEY")),
            httpx.MockTransport(usda_response),
        )
    assert foods[0].fdc_id == 173423
    assert foods[0].source_url.startswith("https://fdc.nal.usda.gov/")
    automatic = client.post("/api/v1/photo-meals/auto-estimate", json={"foods": [{
        "name": "Egg", "preparation": "fried", "estimated_grams": 50,
        "portion_basis": "visual_estimate",
    }]})
    assert automatic.status_code == 200
    assert automatic.json()["estimate"]["nutrition"]["calories_kcal"] == 98
    assert automatic.json()["selections"][0]["portion_basis"] == "visual_estimate"
    unresolved = client.post("/api/v1/photo-meals/auto-estimate", json={"foods": [{
        "name": "Egg", "preparation": "fried", "estimated_grams": None,
    }]})
    assert unresolved.status_code == 200
    assert unresolved.json()["estimate"] is None
    assert "Portion weight unclear" in unresolved.json()["unresolved"][0]
    cached = client.get("/api/v1/nutrition-foods?q=egg%20fried")
    assert cached.status_code == 200
    assert any(item["fdc_id"] == 173423 for item in cached.json())
    payload = {
        "foods": [{"name": "Fried egg", "preparation": "fried"}],
        "nutrition_selections": automatic.json()["selections"],
    }
    preview = client.post("/api/v1/photo-meals/estimate", json=payload)
    assert preview.status_code == 200
    assert preview.json()["nutrition"] == {
        "calories_kcal": 98, "protein_g": 6.8,
        "carbs_g": 0.4, "fat_g": 7.4,
    }
    saved = client.post("/api/v1/photo-meals", json={
        **payload, "notes": "One egg, approximately 50 g edible portion", "model": "vision-test",
    })
    assert saved.status_code == 201
    assert saved.json()["nutrition"] == preview.json()["nutrition"]
    assert saved.json()["nutrition_status"] == "complete"
    assert saved.json()["nutrition_items"][0]["fdc_id"] == 173423
    assert saved.json()["nutrition_items"][0]["portion_basis"] == "visual_estimate"
    summary = client.get("/api/v1/me/daily-summary").json()
    assert summary["meal_count"] == 1
    assert summary["totals"] == preview.json()["nutrition"]
    assert client.get("/api/v1/me/photo-meals", headers={"X-Demo-User-Id": "demo-peer"}).json() == []
    assert client.post("/api/v1/photo-meals/estimate", json={
        "foods": payload["foods"], "nutrition_selections": [],
    }).status_code == 422
    assert client.post("/api/v1/photo-meals/estimate", json={
        "foods": payload["foods"],
        "nutrition_selections": [{"food_index": 0, "fdc_id": 999999, "grams": 50}],
    }).status_code == 422


def test_invalid_photo_bytes_and_quantity_are_rejected():
    settings = Settings(openrouter_api_key=SecretStr("test-key"))
    request = PhotoAnalysisRequest(
        image_base64=base64.b64encode(b"not-an-image").decode(), mime_type="image/png",
    )
    with pytest.raises(HTTPException) as exc:
        analyze_photo(request, settings, httpx.MockTransport(lambda _: httpx.Response(200)))
    assert exc.value.status_code == 422

    def invented_quantity(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": (
            '{"foods":[{"name":"Rice","quantity_from_notes":"200 g"}],'
            '"review_questions":[]}'
        )}}]})

    request = PhotoAnalysisRequest(
        image_base64=base64.b64encode(b"\xff\xd8\xfftest-image").decode(),
        mime_type="image/jpeg", notes="small bowl",
    )
    with pytest.raises(HTTPException) as exc:
        analyze_photo(request, settings, httpx.MockTransport(invented_quantity))
    assert exc.value.status_code == 503


def test_auto_matching_rejects_wrong_food_or_preparation():
    def source(description: str, fdc_id: int) -> NutritionFoodRead:
        return NutritionFoodRead(
            fdc_id=fdc_id, description=description, data_type="SR Legacy",
            calories_kcal=100, protein_g=1, carbs_g=1, fat_g=1, source_url="https://example.test",
        )

    food = PhotoFood(name="Rice, white, cooked")
    assert _best_match(food, [source("Rice noodles, cooked", 1),
                              source("Rice, white, dry", 2)]) is None
    assert _best_match(food, [source("Rice noodles, cooked", 1),
                              source("Rice, white, cooked", 3)]).fdc_id == 3
    assert _best_match(PhotoFood(name="Egg", preparation="fried"), [
        source("Egg, white, cooked, fried", 4),
    ]) is None
    assert _best_match(PhotoFood(name="egg, chicken, whole, fried"), [
        source("Egg, whole, cooked, fried", 173423),
    ]).fdc_id == 173423


def test_local_usda_index_and_partial_auto_result(nl_stack, monkeypatch):
    client, session_factory = nl_stack
    with session_factory() as db:
        foods = search_nutrition_foods(
            db, "tomato raw", 12, Settings(),
            httpx.MockTransport(lambda _: (_ for _ in ()).throw(AssertionError("remote call"))),
        )
    assert foods
    assert foods[0].description.startswith("Tomatoes, red, ripe, raw")
    photo = importlib.import_module("apps.api.modules.tracking.photo")
    original_search = photo.search_nutrition_foods
    monkeypatch.setattr(photo, "search_nutrition_foods", lambda db, query, limit, settings,
                        **kwargs: [] if query == "Unknown sauce" else original_search(
                            db, query, limit, settings, **kwargs))
    result = client.post("/api/v1/photo-meals/auto-estimate", json={"foods": [
        {"name": "Egg", "preparation": "fried", "estimated_grams": 50},
        {"name": "Unknown sauce", "estimated_grams": 30},
    ]})
    assert result.status_code == 200
    body = result.json()
    assert body["estimate"] is None
    assert body["partial_estimate"]["nutrition"]["calories_kcal"] == 98
    assert [item["name"] for item in body["partial_estimate"]["items"]] == ["Egg"]
    assert "Unknown sauce" in body["unresolved"][0]
    saved = client.post("/api/v1/photo-meals", json={
        "foods": [
            {"name": "Egg", "preparation": "fried", "estimated_grams": 50},
            {"name": "Unknown sauce", "estimated_grams": 30},
        ],
        "model": "vision-test", "nutrition_selections": body["selections"],
    })
    assert saved.status_code == 201
    assert saved.json()["nutrition_status"] == "partial"
    assert saved.json()["nutrition"]["calories_kcal"] == 98
    assert saved.json()["unresolved_foods"] == ["Unknown sauce"]
    history = client.get("/api/v1/me/photo-meals").json()
    assert history[0]["nutrition_status"] == "partial"
    assert history[0]["nutrition_items"][0]["name"] == "Egg"
    assert client.get("/api/v1/me/daily-summary").json()["totals"]["calories_kcal"] == 0
