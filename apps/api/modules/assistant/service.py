from __future__ import annotations

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from apps.api.modules.assistant.context import build_today_context
from apps.api.modules.assistant.provider import (
    AssistantConfigurationError,
    AssistantLLMProvider,
    AssistantResponseError,
    AssistantTimeoutError,
    AssistantUnavailableError,
)
from apps.api.modules.assistant.schemas import AssistantAnswerRead, DailyCoachReport
from apps.api.modules.identity.models import User


PROVIDER_ERRORS = (
    AssistantConfigurationError,
    AssistantTimeoutError,
    AssistantUnavailableError,
    AssistantResponseError,
)


def _provider_http_error(error: Exception) -> HTTPException:
    if isinstance(error, AssistantConfigurationError):
        return HTTPException(503, "Daily coach is not configured")
    if isinstance(error, AssistantTimeoutError):
        return HTTPException(504, "Daily coach timed out; please try again")
    if isinstance(error, AssistantUnavailableError):
        return HTTPException(502, "Daily coach is unavailable; please try again")
    if isinstance(error, AssistantResponseError):
        return HTTPException(502, "Daily coach returned an invalid response")
    raise error


def ask_assistant(
    db: Session, user: User, question: str, provider: AssistantLLMProvider
) -> AssistantAnswerRead:
    context = build_today_context(db, user)
    try:
        answer = provider.answer(question, context)
    except PROVIDER_ERRORS as error:
        raise _provider_http_error(error) from error
    try:
        return AssistantAnswerRead(answer=answer)
    except ValidationError:
        raise HTTPException(502, "Daily coach returned an invalid response") from None


def create_daily_report(
    db: Session, user: User, provider: AssistantLLMProvider
) -> DailyCoachReport:
    context = build_today_context(db, user)
    try:
        return provider.report(context)
    except PROVIDER_ERRORS as error:
        raise _provider_http_error(error) from error
