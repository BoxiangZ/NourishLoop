from __future__ import annotations

from typing import Any

import httpx

from services.ai.app.hkgai import Completion, ProviderError
from services.common.config import Settings


class GeminiClient:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    def generate(self, prompt: str, parts: list[dict[str, Any]]) -> Completion:
        secret = self.settings.gemini_api_key
        if secret is None or not secret.get_secret_value():
            raise ProviderError("GEMINI_API_KEY is not configured")
        base_url = self.settings.gemini_api_base_url.rstrip("/")
        if not base_url.startswith("https://"):
            raise ProviderError("GEMINI_API_BASE_URL must use HTTPS")

        try:
            with httpx.Client(
                timeout=self.settings.gemini_request_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = client.post(
                    f"{base_url}/v1beta/models/{self.settings.gemini_model}:generateContent",
                    headers={"x-goog-api-key": secret.get_secret_value()},
                    json={
                        "systemInstruction": {"parts": [{"text": prompt}]},
                        "contents": [{"role": "user", "parts": parts}],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "thinkingConfig": {"thinkingLevel": "low"},
                        },
                    },
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"Gemini returned HTTP {exc.response.status_code}") from None
        except (httpx.RequestError, ValueError) as exc:
            raise ProviderError(f"Gemini request failed: {type(exc).__name__}") from None

        try:
            parts = body["candidates"][0]["content"]["parts"]
            content = "".join(part.get("text", "") for part in parts)
            if not content.strip():
                raise ValueError("empty content")
            model = body.get("modelVersion")
            return Completion(
                content=content.strip(),
                request_id=response.headers.get("x-goog-request-id"),
                model=model if isinstance(model, str) else self.settings.gemini_model,
            )
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            raise ProviderError("Gemini returned an invalid content response") from None
