from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from services.common.config import Settings


class ProviderError(Exception):
    """A safe-to-report provider failure without request or credential contents."""


@dataclass(frozen=True)
class Completion:
    content: str
    request_id: str | None
    model: str


class HKGaiClient:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    def complete(self, messages: list[dict[str, Any]]) -> Completion:
        secret = self.settings.hkg_api_key
        if secret is None or not secret.get_secret_value():
            raise ProviderError("HKG_API_KEY is not configured")

        base_url = self.settings.hkg_api_base_url.rstrip("/")
        if not base_url.startswith("https://"):
            raise ProviderError("HKG_API_BASE_URL must use HTTPS")

        try:
            with httpx.Client(
                timeout=self.settings.hkg_request_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = client.post(
                    f"{base_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {secret.get_secret_value()}"},
                    json={"model": self.settings.hkg_model, "messages": messages},
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"HKGAI returned HTTP {exc.response.status_code}") from None
        except (httpx.RequestError, ValueError) as exc:
            raise ProviderError(f"HKGAI request failed: {type(exc).__name__}") from None

        try:
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("empty content")
            request_id = body.get("id")
            return Completion(
                content=content.strip(),
                request_id=request_id if isinstance(request_id, str) else None,
                model=self.settings.hkg_model,
            )
        except (KeyError, IndexError, TypeError, ValueError):
            raise ProviderError("HKGAI returned an invalid chat response") from None
