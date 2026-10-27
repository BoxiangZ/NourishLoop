from __future__ import annotations

import base64
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from services.ai.app.drafts import MealRecognitionRequest, recognize_meal
from services.ai.app.gemini import GeminiClient
from services.ai.app.hkgai import ProviderError
from services.ai.app.main import app
from services.common.config import Settings


PNG = base64.b64encode(b"\x89PNG\r\n\x1a\nsynthetic-test-bytes").decode()


def client_for(content: str, status_code: int = 200) -> GeminiClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-3.5-flash-lite:generateContent"
        )
        assert request.headers["x-goog-api-key"] == "test-secret"
        body = json.loads(request.content)
        assert body["contents"][0]["parts"][0]["inline_data"]["data"] == PNG
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        return httpx.Response(
            status_code,
            json={
                "modelVersion": "gemini-3.5-flash-lite",
                "candidates": [{"content": {"parts": [{"text": content}]}}],
            },
        )

    return GeminiClient(
        Settings(_env_file=None, gemini_api_key="test-secret"),
        httpx.MockTransport(handler),
    )


def test_image_draft_preserves_review_and_explicit_quantity() -> None:
    content = json.dumps(
        {
            "foods": [
                {
                    "name": "egg",
                    "preparation": None,
                    "quantity_from_notes": "2 eggs",
                    "needs_review": True,
                }
            ],
            "review_questions": ["How were the eggs prepared?"],
        }
    )
    request = MealRecognitionRequest(image_base64=PNG, mime_type="image/png", notes="2 eggs")

    result = recognize_meal(client_for(content), request)

    assert result.foods[0].needs_review is True
    assert result.foods[0].quantity_from_notes == "2 eggs"
    assert result.prompt_version == "meal-image-v1"


def test_image_draft_rejects_invented_quantity() -> None:
    content = json.dumps(
        {
            "foods": [
                {
                    "name": "egg",
                    "quantity_from_notes": "150 g",
                    "needs_review": True,
                }
            ],
            "review_questions": [],
        }
    )
    request = MealRecognitionRequest(image_base64=PNG, mime_type="image/png", notes="2 eggs")

    with pytest.raises(ProviderError, match="quantity absent"):
        recognize_meal(client_for(content), request)


def test_provider_failure_hides_secret_and_response_body() -> None:
    client = client_for("private provider detail", status_code=403)
    with pytest.raises(ProviderError) as error:
        client.generate("prompt", [{"inline_data": {"data": PNG}}])
    assert "403" in str(error.value)
    assert "test-secret" not in str(error.value)
    assert "private provider detail" not in str(error.value)


def test_invalid_image_base64_is_rejected_before_provider() -> None:
    with pytest.raises(ValueError):
        MealRecognitionRequest(image_base64="not base64", mime_type="image/png")


def test_image_route_returns_review_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    content = json.dumps({"foods": [], "review_questions": ["Please upload a meal photo."]})
    monkeypatch.setattr("services.ai.app.main.GeminiClient", lambda _settings: client_for(content))

    response = TestClient(app).post(
        "/meals/recognize",
        json={"image_base64": PNG, "mime_type": "image/png", "notes": ""},
    )

    assert response.status_code == 200
    assert response.json()["foods"] == []
    assert response.json()["prompt_version"] == "meal-image-v1"
