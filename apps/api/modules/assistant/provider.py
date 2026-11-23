from __future__ import annotations

import json
from typing import Protocol
from urllib.parse import urlsplit

import httpx
from pydantic import ValidationError

from apps.api.core.config import Settings
from apps.api.modules.assistant.prompts import (
    ANSWER_SYSTEM_PROMPT,
    REPORT_SYSTEM_PROMPT,
    build_answer_payload,
    build_report_payload,
)
from apps.api.modules.assistant.schemas import AssistantContext, DailyCoachReport


class AssistantConfigurationError(RuntimeError):
    pass


class AssistantTimeoutError(RuntimeError):
    pass


class AssistantUnavailableError(RuntimeError):
    pass


class AssistantResponseError(RuntimeError):
    pass


class AssistantLLMProvider(Protocol):
    def answer(self, question: str, context: AssistantContext) -> str: ...

    def report(self, context: AssistantContext) -> DailyCoachReport: ...


ANSWER_MAX_TOKENS = 2400
REPORT_MAX_TOKENS = 2400
INCOMPLETE_FINISH_REASONS = frozenset({"length", "content_filter"})
TERMINAL_SENTENCE_BOUNDARIES = frozenset({".", "!", "?", "。", "！", "？"})
CLOSING_QUOTES = "\"'”’」』】）"


def _ends_with_complete_sentence(answer: str) -> bool:
    without_closing_quotes = answer.rstrip().rstrip(CLOSING_QUOTES).rstrip()
    return bool(without_closing_quotes) and (
        without_closing_quotes[-1] in TERMINAL_SENTENCE_BOUNDARIES
    )


def _names_ineligible_menu_item(answer: str, context: AssistantContext) -> bool:
    normalized_answer = " ".join(answer.casefold().split())
    return any(
        " ".join(item.name.casefold().split()) in normalized_answer
        for item in context.menu_catalog
        if not item.eligible
    )


class DeepSeekChatProvider:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None) -> None:
        self.settings = settings
        self.transport = transport

    def answer(self, question: str, context: AssistantContext) -> str:
        content = json.dumps(
            build_answer_payload(question, context),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        answer = self._complete(
            system_prompt=ANSWER_SYSTEM_PROMPT,
            content=content,
            max_tokens=ANSWER_MAX_TOKENS,
            temperature=0.2,
        )
        answer = answer.strip()
        if not answer:
            raise AssistantResponseError("DeepSeek returned an empty answer")
        if not _ends_with_complete_sentence(answer):
            raise AssistantResponseError("DeepSeek returned an incomplete answer")
        if _names_ineligible_menu_item(answer, context):
            raise AssistantResponseError("DeepSeek recommended an ineligible menu item")
        return answer

    def report(self, context: AssistantContext) -> DailyCoachReport:
        content = json.dumps(
            build_report_payload(context),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        response = self._complete(
            system_prompt=REPORT_SYSTEM_PROMPT,
            content=content,
            max_tokens=REPORT_MAX_TOKENS,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        try:
            return DailyCoachReport.model_validate(json.loads(response))
        except (json.JSONDecodeError, ValidationError):
            raise AssistantResponseError("DeepSeek returned an invalid report") from None

    def _complete(
        self,
        *,
        system_prompt: str,
        content: str,
        max_tokens: int,
        temperature: float,
        response_format: dict[str, str] | None = None,
    ) -> str:
        api_key, base_url, model = self._configuration()
        payload: dict[str, object] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
        }
        if response_format is not None:
            payload["response_format"] = response_format

        with httpx.Client(
            timeout=self.settings.deepseek_timeout_seconds,
            transport=self.transport,
        ) as client:
            try:
                response = client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            except httpx.TimeoutException as exc:
                raise AssistantTimeoutError("DeepSeek request timed out") from exc
            except httpx.HTTPError as exc:
                raise AssistantUnavailableError("DeepSeek request failed") from exc

        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AssistantUnavailableError("DeepSeek request failed") from exc

        try:
            body = response.json()
            choice = body["choices"][0]
            reply = choice["message"]["content"]
        except (AttributeError, ValueError, KeyError, IndexError, TypeError):
            raise AssistantUnavailableError("DeepSeek returned an unusable response") from None
        if not isinstance(reply, str):
            raise AssistantResponseError("DeepSeek returned no textual answer")
        if choice.get("finish_reason") in INCOMPLETE_FINISH_REASONS:
            raise AssistantResponseError("DeepSeek returned an incomplete response")
        return reply

    def _configuration(self) -> tuple[str, str, str]:
        secret = self.settings.deepseek_api_key
        if secret is None:
            raise AssistantConfigurationError("DeepSeek key is not configured")
        api_key = secret.get_secret_value()
        if not api_key.strip():
            raise AssistantConfigurationError("DeepSeek key is not configured")

        base_url = self.settings.deepseek_base_url.strip().rstrip("/")
        try:
            parsed_url = urlsplit(base_url)
            parsed_url.port
        except ValueError:
            raise AssistantConfigurationError("DeepSeek base URL is not configured") from None
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise AssistantConfigurationError("DeepSeek base URL is not configured")

        model = self.settings.deepseek_model.strip()
        if not model:
            raise AssistantConfigurationError("DeepSeek model is not configured")

        timeout_seconds = self.settings.deepseek_timeout_seconds
        if not 0 < timeout_seconds <= 120:
            raise AssistantConfigurationError("DeepSeek timeout is invalid")

        return api_key.strip(), base_url, model
