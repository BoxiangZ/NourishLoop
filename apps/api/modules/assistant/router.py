from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.core.auth import current_user
from apps.api.core.config import get_settings
from apps.api.core.database import get_db
from apps.api.modules.assistant.provider import AssistantLLMProvider, DeepSeekChatProvider
from apps.api.modules.assistant.schemas import (
    AssistantAnswerRead,
    AssistantAskRequest,
    DailyCoachReport,
)
from apps.api.modules.assistant.service import ask_assistant, create_daily_report
from apps.api.modules.identity.models import User

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


def assistant_provider() -> AssistantLLMProvider:
    return DeepSeekChatProvider(get_settings())


@router.post("/ask", response_model=AssistantAnswerRead)
def ask(
    payload: AssistantAskRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    provider: AssistantLLMProvider = Depends(assistant_provider),
):
    return ask_assistant(db, user, payload.question, provider)


@router.post("/daily-report", response_model=DailyCoachReport)
def daily_report(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    provider: AssistantLLMProvider = Depends(assistant_provider),
):
    return create_daily_report(db, user, provider)
