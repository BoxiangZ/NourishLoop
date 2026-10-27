from __future__ import annotations

from typing import Protocol

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from apps.api.core.config import get_settings
from apps.api.core.database import get_db
from apps.api.modules.identity.models import User


class IdentityProvider(Protocol):
    def resolve_user(self, db: Session) -> User: ...


class DemoIdentityProvider:
    def resolve_user(self, db: Session, requested_user_id: str | None = None) -> User:
        settings = get_settings()
        if settings.app_env != "development" or not settings.demo_auth_enabled:
            raise HTTPException(status_code=503, detail="Authentication provider is not configured")
        allowed_ids = {settings.demo_user_id, "demo-peer"}
        user_id = requested_user_id or settings.demo_user_id
        if user_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="Unknown demo identity")
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=503, detail="Demo user missing; run the seed command")
        return user


def current_user(
    db: Session = Depends(get_db),
    demo_user_id: str | None = Header(default=None, alias="X-Demo-User-Id"),
) -> User:
    return DemoIdentityProvider().resolve_user(db, demo_user_id)
