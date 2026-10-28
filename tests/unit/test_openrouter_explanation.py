from __future__ import annotations

import httpx

from apps.api.core.config import Settings
from apps.api.modules.recommendations.engine import Candidate, explain_with_fallback
from apps.api.modules.recommendations.openrouter import OpenRouterExplanationProvider


def test_openrouter_rewords_only_grounded_candidate_and_uses_key():
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "This meal fits your estimate; nutrition is an estimate."
                        }
                    }
                ]
            },
        )

    provider = OpenRouterExplanationProvider(
        Settings(_env_file=None, openrouter_api_key="test-only", openrouter_model="test-model"),
        transport=httpx.MockTransport(respond),
    )
    candidate = Candidate("id-1", "Chickpea salad", ("vegan",), (), 470, 18)
    result = provider.explain(candidate, "Estimated 470 kcal. Nutrition is an estimate.")
    assert result.startswith("This meal")
    assert len(requests) == 1
    assert requests[0].headers["Authorization"] == "Bearer test-only"
    body = requests[0].read().decode()
    assert "Chickpea salad" in body
    assert "Estimated 470 kcal" in body
    assert '"reasoning":{"enabled":false}' in body
    assert "test-only" not in body


def test_provider_failure_preserves_baseline():
    def unavailable(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"})

    provider = OpenRouterExplanationProvider(
        Settings(_env_file=None, openrouter_api_key="test-only"),
        transport=httpx.MockTransport(unavailable),
    )
    candidate = Candidate("id-1", "Chickpea salad", (), (), 470, 18)
    baseline = "Estimated 470 kcal. Nutrition is an estimate."
    assert explain_with_fallback(provider, candidate, baseline) == baseline
