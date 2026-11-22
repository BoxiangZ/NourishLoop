from __future__ import annotations

import pytest

from apps.api.core.database import Base
from apps.api.main import app
from apps.api.modules.assistant.provider import (
    AssistantConfigurationError,
    AssistantResponseError,
    AssistantTimeoutError,
    AssistantUnavailableError,
)
from apps.api.modules.assistant.router import assistant_provider
from apps.api.modules.assistant.schemas import DailyCoachReport


class FakeProvider:
    def __init__(self):
        self.answer_calls = 0
        self.report_calls = 0

    def answer(self, question, context):
        self.answer_calls += 1
        assert question == "What should I eat?"
        assert context.date.isoformat() == "2026-11-23"
        return "Choose a balanced meal."

    def report(self, context):
        self.report_calls += 1
        return DailyCoachReport(
            headline="A steady day.",
            nutrition_insight="Two meals are recorded.",
            activity_insight="No workout is completed.",
            next_actions=["Choose a balanced dinner."],
            limitations=["No workout is recorded."],
        )


def test_ask_uses_provider_once(nl_client):
    provider = FakeProvider()
    app.dependency_overrides[assistant_provider] = lambda: provider
    try:
        response = nl_client.post(
            "/api/v1/assistant/ask",
            json={"question": "  What should I eat?  "},
        )
    finally:
        app.dependency_overrides.pop(assistant_provider, None)

    assert response.status_code == 200
    assert response.json() == {"answer": "Choose a balanced meal."}
    assert provider.answer_calls == 1


def test_ask_rejects_blank_and_oversized_questions(nl_client):
    provider = FakeProvider()
    app.dependency_overrides[assistant_provider] = lambda: provider
    try:
        blank_response = nl_client.post("/api/v1/assistant/ask", json={"question": "   "})
        oversized_response = nl_client.post("/api/v1/assistant/ask", json={"question": "x" * 501})
    finally:
        app.dependency_overrides.pop(assistant_provider, None)

    assert blank_response.status_code == 422
    assert oversized_response.status_code == 422
    assert provider.answer_calls == 0


def test_daily_report_returns_structured_content_without_persistence(nl_client):
    tables_before = set(Base.metadata.tables)
    provider = FakeProvider()
    app.dependency_overrides[assistant_provider] = lambda: provider
    try:
        response = nl_client.post("/api/v1/assistant/daily-report")
    finally:
        app.dependency_overrides.pop(assistant_provider, None)

    assert response.status_code == 200
    assert response.json()["headline"] == "A steady day."
    assert provider.report_calls == 1

    assert set(Base.metadata.tables) == tables_before
    assert not any("assistant" in name for name in Base.metadata.tables)


class RaisingProvider:
    def __init__(self, error: Exception):
        self.error = error
        self.calls = 0

    def answer(self, question, context):
        self.calls += 1
        raise self.error

    def report(self, context):
        self.calls += 1
        raise self.error


@pytest.mark.parametrize(
    ("error", "status_code", "message"),
    [
        (
            AssistantConfigurationError("provider key missing"),
            503,
            "Daily coach is not configured",
        ),
        (
            AssistantTimeoutError("provider timed out"),
            504,
            "Daily coach timed out; please try again",
        ),
        (
            AssistantUnavailableError("provider failed"),
            502,
            "Daily coach is unavailable; please try again",
        ),
        (
            AssistantResponseError("provider returned private details"),
            502,
            "Daily coach returned an invalid response",
        ),
    ],
)
@pytest.mark.parametrize("endpoint", ["/api/v1/assistant/ask", "/api/v1/assistant/daily-report"])
def test_provider_errors_are_mapped_without_leaking_details(
    nl_client, endpoint, error, status_code, message
):
    provider = RaisingProvider(error)
    app.dependency_overrides[assistant_provider] = lambda: provider
    try:
        response = nl_client.post(
            endpoint,
            json={"question": "What should I eat?"} if endpoint.endswith("/ask") else None,
        )
    finally:
        app.dependency_overrides.pop(assistant_provider, None)

    assert response.status_code == status_code
    assert response.json() == {"error": {"code": f"http_{status_code}", "message": message}}
    assert provider.calls == 1
    assert str(error) not in response.text


def test_unrelated_programming_errors_are_not_mapped_as_provider_failures(nl_client):
    provider = RaisingProvider(RuntimeError("programming defect"))
    app.dependency_overrides[assistant_provider] = lambda: provider
    try:
        with pytest.raises(RuntimeError, match="programming defect"):
            nl_client.post("/api/v1/assistant/ask", json={"question": "What should I eat?"})
    finally:
        app.dependency_overrides.pop(assistant_provider, None)

    assert provider.calls == 1
