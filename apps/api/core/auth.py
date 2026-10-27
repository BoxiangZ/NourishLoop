from __future__ import annotations

from typing import Protocol

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.core.config import get_settings
from apps.api.core.database import get_db
from apps.api.modules.identity.models import User


class IdentityProvider(Protocol):
    def resolve_user(self, db: Session) -> User: ...


class DemoIdentityProvider:
    def resolve_user(self, db: Session) -> User:
        settings = get_settings()
        if settings.app_env != "development" or not settings.demo_auth_enabled:
            raise HTTPException(status_code=503, detail="Authentication provider is not configured")
        user = db.get(User, settings.demo_user_id)
        if user is None:
            raise HTTPException(status_code=503, detail="Demo user missing; run the seed command")
        return user


def current_user(db: Session = Depends(get_db)) -> User:
    return DemoIdentityProvider().resolve_user(db)
