from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Protocol

import httpx
from pydantic import BaseModel, Field, StringConstraints, ValidationError, model_validator

from apps.api.core.config import Settings


class NutritionEstimate(BaseModel):
    calories_kcal: float = Field(ge=0, le=5000)
    protein_g: float = Field(ge=0, le=1000)
    carbs_g: float = Field(ge=0, le=1000)
    fat_g: float = Field(ge=0, le=1000)


FoodName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
ReviewText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)
]


class MealAIReview(BaseModel):
    is_food: bool
    detected_foods: list[FoodName] = Field(default_factory=list, max_length=20)
    estimated_nutrition: NutritionEstimate | None = None
    confidence: float = Field(ge=0, le=1)
    summary: str = Field(min_length=1, max_length=1000)
    suggestions: list[ReviewText] = Field(default_factory=list, max_length=10)
    assumptions: list[ReviewText] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validate_food_shape(self):
        if not self.is_food:
            self.detected_foods = []
            self.estimated_nutrition = None
            return self
        if not self.detected_foods:
            raise ValueError("food reviews require detected foods")
        if self.estimated_nutrition is None:
            raise ValueError("food reviews require nutrition estimates")
        if not self.assumptions:
            raise ValueError("food reviews require assumptions")
        return self


@dataclass(frozen=True)
class ProviderReview:
    review: MealAIReview
    raw_response: dict[str, Any]
    request_id: str | None
    provider: str
    model: str
    status_code: int = 200


class MealReviewProviderError(Exception):
    error_type = "provider_error"
    user_message = "AI review failed. Please retry."

    def __init__(
        self,
        developer_message: str = "",
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        raw_response: Any = None,
        diagnostics: dict[str, Any] | None = None,
    ):
        super().__init__(self.user_message)
        self.status_code = status_code
        self.request_id = request_id
        self.raw_response = raw_response
        self.diagnostics = {
            **(diagnostics or {}),
            "developer_message": developer_message,
        }


class MealReviewConfigurationError(MealReviewProviderError):
    error_type = "configuration_error"
    user_message = "AI review is not configured."


class MealReviewTimeoutError(MealReviewProviderError):
    error_type = "timeout"
    user_message = "AI review timed out. Please retry."


class MealReviewUnavailableError(MealReviewProviderError):
    error_type = "unavailable"
    user_message = "AI review service is unavailable. Please retry."


class MealReviewHTTPError(MealReviewProviderError):
    error_type = "http_error"
    user_message = "AI review service failed. Please retry."


class MealReviewMalformedResponseError(MealReviewProviderError):
    error_type = "malformed_response"
    user_message = "AI review returned an invalid response. Please retry."


_SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "access_token",
    "refresh_token",
    "secret",
    "token",
}
_AUTH_HEADER_RE = re.compile(
    r"(?i)authorization\s*:\s*(?:bearer\s+)?[^\s,;]+"
)
_DATA_URI_RE = re.compile(
    r"(?i)data:image/[a-z0-9.+-]+;base64,[a-z0-9+/=]+"
)
_LONG_BASE64_RE = re.compile(r"[A-Za-z0-9+/]{64,}={0,2}")


def sanitize_provider_diagnostics(
    value: Any, sensitive_values: tuple[str, ...] = ()
) -> Any:
    if isinstance(value, bytes):
        return "[REDACTED_BYTES]"
    if isinstance(value, str):
        cleaned = value
        cleaned = _AUTH_HEADER_RE.sub("[REDACTED_AUTHORIZATION]", cleaned)
        cleaned = _DATA_URI_RE.sub("[REDACTED_IMAGE_DATA]", cleaned)
        for sensitive in sensitive_values:
            if sensitive:
                cleaned = cleaned.replace(sensitive, "[REDACTED]")
        return _LONG_BASE64_RE.sub("[REDACTED_BASE64]", cleaned)
    if isinstance(value, dict):
        return {
            key: (
                "[REDACTED]"
                if str(key).lower() in _SENSITIVE_KEYS
                else sanitize_provider_diagnostics(item, sensitive_values)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            sanitize_provider_diagnostics(item, sensitive_values) for item in value
        ]
    return value


def provider_error(exc: Exception) -> MealReviewProviderError:
    if isinstance(exc, MealReviewProviderError):
        return exc
    error = MealReviewProviderError(
        f"{type(exc).__name__}: {str(exc)[:500]}",
        diagnostics={"exception_type": type(exc).__name__},
    )
    error.error_type = type(exc).__name__
    return error


def _normalize_review_payload(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    normalized = dict(payload)
    for field in ("detected_foods", "suggestions", "assumptions"):
        value = normalized.get(field)
        if isinstance(value, str):
            normalized[field] = [value]
    confidence = normalized.get("confidence")
    if isinstance(confidence, str):
        confidence = confidence.strip().removesuffix("%")
        try:
            confidence = float(confidence)
        except ValueError:
            pass
    if isinstance(confidence, (int, float)) and 1 < confidence <= 100:
        confidence = confidence / 100
    if isinstance(confidence, (int, float)):
        normalized["confidence"] = confidence
    return normalized


class MealReviewProvider(Protocol):
    def review(self, image_bytes: bytes, media_type: str, note: str) -> ProviderReview: ...


SYSTEM_PROMPT = """Estimate the meal from the photo for general wellness guidance.
Return only one JSON object with is_food, detected_foods, estimated_nutrition
(calories_kcal, protein_g, carbs_g, fat_g), confidence, summary, suggestions,
and assumptions. Estimate one visible serving. State uncertainty in assumptions.
Do not provide medical diagnosis. Nutrition values are estimates."""


class OpenRouterMealReviewProvider:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.settings = settings
        self.transport = transport
        self.client_factory: Callable[..., httpx.Client] = httpx.Client

    def review(self, image_bytes: bytes, media_type: str, note: str) -> ProviderReview:
        secret = self.settings.openrouter_api_key
        if secret is None or not secret.get_secret_value():
            raise MealReviewConfigurationError("OpenRouter key is not configured")
        api_key = secret.get_secret_value()
        encoded = base64.b64encode(image_bytes).decode("ascii")
        with self.client_factory(
            timeout=self.settings.openrouter_timeout_seconds,
            transport=self.transport,
        ) as client:
            try:
                response = client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": self.settings.openrouter_model,
                        "max_tokens": 4096,
                        "temperature": 0.1,
                        "reasoning": {"effort": "low"},
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"User note: {note or '(none)'}",
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{media_type};base64,{encoded}"
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                )
            except httpx.TimeoutException as exc:
                raise MealReviewTimeoutError(
                    sanitize_provider_diagnostics(
                        f"{type(exc).__name__}: {exc}",
                        (api_key, encoded),
                    ),
                    diagnostics={"exception_type": type(exc).__name__},
                ) from exc
            except httpx.RequestError as exc:
                raise MealReviewUnavailableError(
                    sanitize_provider_diagnostics(
                        f"{type(exc).__name__}: {exc}",
                        (api_key, encoded),
                    ),
                    diagnostics={"exception_type": type(exc).__name__},
                ) from exc

        request_id = response.headers.get("x-request-id")
        raw = _response_payload(response)
        if isinstance(raw, dict):
            raw_request_id = raw.get("id")
            if request_id is None and isinstance(raw_request_id, str):
                request_id = raw_request_id
        if response.is_error:
            raise MealReviewHTTPError(
                f"OpenRouter returned HTTP {response.status_code}",
                status_code=response.status_code,
                request_id=request_id,
                raw_response=raw,
            )
        if not isinstance(raw, dict):
            raise MealReviewMalformedResponseError(
                "OpenRouter response was not a JSON object",
                status_code=response.status_code,
                request_id=request_id,
                raw_response=raw,
            )
        try:
            content = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise MealReviewMalformedResponseError(
                "OpenRouter response did not contain content",
                status_code=response.status_code,
                request_id=request_id,
                raw_response=raw,
                diagnostics={"exception_type": type(exc).__name__},
            ) from exc
        if not isinstance(content, str) or not content.strip():
            raise MealReviewMalformedResponseError(
                "OpenRouter response did not contain textual content",
                status_code=response.status_code,
                request_id=request_id,
                raw_response=raw,
            )
        try:
            body = content.strip()
            if body.startswith("```"):
                body = body.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            payload = json.loads(body)
            review = MealAIReview.model_validate(_normalize_review_payload(payload))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise MealReviewMalformedResponseError(
                "OpenRouter response did not match the review schema",
                status_code=response.status_code,
                request_id=request_id,
                raw_response=raw,
                diagnostics={"exception_type": type(exc).__name__},
            ) from exc
        return ProviderReview(
            review=review,
            raw_response=raw,
            request_id=request_id if isinstance(request_id, str) else None,
            provider="openrouter",
            model=self.settings.openrouter_model,
            status_code=response.status_code,
        )


def _response_payload(response: httpx.Response) -> Any:
    try:
        return response.json()
    except json.JSONDecodeError:
        return response.text
