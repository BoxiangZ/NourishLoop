from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.core.auth import current_user
from apps.api.core.database import get_db
from apps.api.modules.community.schemas import CommunityPostCreate, CommunityPostRead
from apps.api.modules.community.service import create_post, delete_post, list_posts
from apps.api.modules.identity.models import User

router = APIRouter(prefix="/api/v1/community", tags=["community"])


@router.post("/posts", response_model=CommunityPostRead, status_code=201)
def publish(
    payload: CommunityPostCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return create_post(db, user, payload)


@router.get("/posts", response_model=list[CommunityPostRead])
def feed(
    limit: int = Query(default=20, ge=1, le=50),
    _user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return list_posts(db, limit)


@router.delete("/posts/{post_id}", status_code=204)
def retract(
    post_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    delete_post(db, user, post_id)
