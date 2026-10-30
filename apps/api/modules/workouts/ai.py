"""Optional stage-aware wording. Selection and sets/reps come from the pure engine."""

from __future__ import annotations

import logging

import httpx

from apps.api.core.config import Settings


def coach_explanation(
    settings: Settings,
    baseline: str,
    stage: str,
    names: list[str],
    transport: httpx.BaseTransport | None = None,
) -> tuple[str, str]:
    if settings.explanation_provider != "openrouter":
        return baseline, "rules"
    try:
        secret = settings.openrouter_api_key
        if secret is None or not secret.get_secret_value():
            raise ValueError("OpenRouter key is not configured")
        with httpx.Client(
            timeout=settings.openrouter_timeout_seconds, transport=transport
        ) as client:
            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {secret.get_secret_value()}"},
                json={
                    "model": settings.openrouter_model,
                    "max_tokens": 180,
                    "reasoning": {"enabled": False},
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Write one supportive workout coaching sentence "
                                "under 250 characters. "
                                "Use only the provided stage, exercise names and grounded reason. "
                                "Do not add exercises, sets, loads, medical claims or promises. "
                                "Keep the recovery or pain warning if present. "
                                "Return only the sentence."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Stage: {stage}\nExercises: {', '.join(names)}"
                                f"\nGrounded reason: {baseline}"
                            ),
                        },
                    ],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip() or len(content) > 300:
            raise ValueError("Invalid workout explanation")
        # The fixed safety sentence is always retained even when AI wording succeeds.
        return content.strip() + " Stop if an exercise causes pain.", "openrouter"
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "workout_explanation_fallback", extra={"error_type": type(exc).__name__}
        )
        return baseline, "rules"
