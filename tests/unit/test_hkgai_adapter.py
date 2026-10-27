from __future__ import annotations

import json

import httpx
import pytest

from services.ai.app.drafts import (
    DietPlanDraftRequest,
    MealNotesRequest,
    draft_plan,
    interpret_meal_notes,
)
from services.ai.app.hkgai import HKGaiClient, ProviderError
from services.common.config import Settings


def client_for(response_content: str, status_code: int = 200) -> HKGaiClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api1.hkgai.net/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-secret"
        assert request.read()
        body = json.loads(request.content)
        assert body["model"] == "t2_hkgai-v3_fp8_1m_e7"
        return httpx.Response(
            status_code,
            json={"id": "req-1", "choices": [{"message": {"content": response_content}}]},
        )

    settings = Settings(_env_file=None, hkg_api_key="test-secret")
    return HKGaiClient(settings, httpx.MockTransport(handler))


def test_plan_draft_keeps_caller_targets() -> None:
    client = client_for('{"guidance_text":"Review the supplied target before using it."}')
    request = DietPlanDraftRequest(goal="Maintain weight", daily_calorie_target=2000)

    result = draft_plan(client, request)

    assert result.daily_calorie_target == 2000
    assert result.requires_review is True
    assert result.provider_request_id == "req-1"


def test_meal_notes_never_accept_invented_quantity() -> None:
    content = json.dumps(
        {
            "foods": [
                {
                    "name": "egg",
                    "preparation": "boiled",
                    "quantity_from_notes": "3 eggs",
                    "needs_review": True,
                }
            ],
            "review_questions": [],
        }
    )
    client = client_for(content)

    with pytest.raises(ProviderError, match="quantity absent"):
        interpret_meal_notes(client, MealNotesRequest(notes="2 eggs"))


def test_provider_error_does_not_include_secret_or_response_body() -> None:
    client = client_for("sensitive provider detail", status_code=401)

    with pytest.raises(ProviderError) as error:
        client.complete([{"role": "user", "content": "hello"}])

    assert "401" in str(error.value)
    assert "test-secret" not in str(error.value)
    assert "sensitive provider detail" not in str(error.value)


def test_missing_key_fails_before_network_call() -> None:
    client = HKGaiClient(Settings(_env_file=None, hkg_api_key=None))
    with pytest.raises(ProviderError, match="not configured"):
        client.complete([{"role": "user", "content": "hello"}])
