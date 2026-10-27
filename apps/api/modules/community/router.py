from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.core.auth import current_user
from apps.api.core.database import get_db
from apps.api.modules.community.schemas import (
    CommunityCommentCreate, CommunityCommentRead, CommunityPostCreate, CommunityPostRead,
    CommunityReportCreate, CommunityReportRead, CommunityReportResolve,
)
from apps.api.modules.community.service import (
    create_comment, create_post, delete_comment, delete_post, like_post, list_posts,
    pending_reports, report_post, resolve_report, shared_meal_log_ids, unlike_post,
)
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
    offset: int = Query(default=0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return list_posts(db, user, limit, offset)


@router.get("/me/shared-meal-log-ids", response_model=list[str])
def my_shared_meals(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return shared_meal_log_ids(db, user)


@router.delete("/posts/{post_id}", status_code=204)
def retract(
    post_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    delete_post(db, user, post_id)


@router.post("/posts/{post_id}/comments", response_model=CommunityCommentRead, status_code=201)
def comment(
    post_id: str,
    payload: CommunityCommentCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return create_comment(db, user, post_id, payload)


@router.delete("/comments/{comment_id}", status_code=204)
def remove_comment(
    comment_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    delete_comment(db, user, comment_id)


@router.put("/posts/{post_id}/like", response_model=CommunityPostRead)
def like(
    post_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return like_post(db, user, post_id)


@router.delete("/posts/{post_id}/like", response_model=CommunityPostRead)
def unlike(
    post_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return unlike_post(db, user, post_id)


@router.post("/posts/{post_id}/reports", response_model=CommunityReportRead, status_code=201)
def report(
    post_id: str,
    payload: CommunityReportCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return report_post(db, user, post_id, payload)


@router.get("/reports/pending", response_model=list[CommunityReportRead])
def reports(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return pending_reports(db, user)


@router.post("/reports/{report_id}/resolve", response_model=CommunityReportRead)
def moderate(
    report_id: str,
    payload: CommunityReportResolve,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return resolve_report(db, user, report_id, payload)
