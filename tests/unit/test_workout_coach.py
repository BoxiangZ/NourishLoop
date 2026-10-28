from __future__ import annotations

import json

import httpx

from apps.api.core.config import Settings
from apps.api.modules.workouts.ai import coach_explanation


def test_workout_ai_rewords_grounded_stage_and_preserves_safety_note():
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.read()))
        return httpx.Response(200, json={"choices": [{"message": {
            "content": "At your beginner stage, use a steady pace with the seated row."
        }}]})

    settings = Settings(
        _env_file=None, explanation_provider="openrouter", openrouter_api_key="test-only",
        openrouter_model="nvidia/nemotron-3.5-super-vl:free",
    )
    result, source = coach_explanation(
        settings, "Beginner back session; stop if pain occurs.", "beginner", ["Seated row"],
        transport=httpx.MockTransport(respond),
    )
    assert source == "openrouter"
    assert "beginner" in result and "Stop if an exercise causes pain" in result
    assert requests[0]["reasoning"] == {"enabled": False}
    assert requests[0]["max_tokens"] == 180


def test_workout_ai_falls_back_when_provider_returns_no_content():
    settings = Settings(
        _env_file=None, explanation_provider="openrouter", openrouter_api_key="test-only",
    )
    baseline = "This session fits your beginner stage. Stop if pain occurs."
    result, source = coach_explanation(
        settings, baseline, "beginner", ["Seated row"],
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={
            "choices": [{"message": {"content": None}}],
        })),
    )
    assert (result, source) == (baseline, "rules")
