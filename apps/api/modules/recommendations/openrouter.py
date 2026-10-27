from __future__ import annotations

import httpx

from apps.api.core.config import Settings
from apps.api.modules.recommendations.engine import Candidate


class OpenRouterExplanationProvider:
    """Rewords a grounded rule explanation; never participates in ranking."""

    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    def explain(self, candidate: Candidate, baseline: str) -> str:
        secret = self.settings.openrouter_api_key
        if secret is None or not secret.get_secret_value():
            raise ValueError("OpenRouter key is not configured")
        with httpx.Client(
            timeout=self.settings.openrouter_timeout_seconds, transport=self.transport
        ) as client:
            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {secret.get_secret_value()}"},
                json={
                    "model": self.settings.openrouter_model,
                    "max_tokens": 180,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Rewrite the supplied meal explanation in one plain sentence "
                                "under 350 characters. Use only the given meal name "
                                "and baseline facts. "
                                "Do not add foods, health claims, exact certainty, "
                                "or nutrition values. "
                                "Keep the estimate warning. Return only the sentence."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Meal: {candidate.name}\nBaseline: {baseline}",
                        },
                    ],
                },
            )
            response.raise_for_status()
            body = response.json()
        content = body["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("OpenRouter returned invalid explanation")
        return content
