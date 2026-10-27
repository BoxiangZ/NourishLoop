from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.core.models import utcnow
from apps.api.modules.community.models import (
    CommunityComment, CommunityPost, CommunityReaction, CommunityReport,
)
from apps.api.modules.community.schemas import (
    CommunityCommentCreate, CommunityCommentRead, CommunityPostCreate, CommunityPostRead,
    CommunityReportCreate, CommunityReportRead, CommunityReportResolve,
)
from apps.api.modules.identity.models import User, UserProfile
from apps.api.modules.rewards.service import award_event, reverse_share_award
from apps.api.modules.tracking.models import MealLog
from apps.api.modules.tracking.service import meal_log_read


def display_name(db: Session, user_id: str) -> str:
    profile = db.get(UserProfile, user_id)
    return profile.display_name if profile else "NourishLoop member"


def comment_read(db: Session, user: User, comment: CommunityComment) -> CommunityCommentRead:
    return CommunityCommentRead(
        id=comment.id, post_id=comment.post_id,
        author_display_name=display_name(db, comment.author_id),
        is_mine=comment.author_id == user.id,
        body=comment.body, created_at=comment.created_at,
    )


def post_read(db: Session, user: User, post: CommunityPost) -> CommunityPostRead:
    meal = db.get(MealLog, post.meal_log_id)
    comments = db.scalars(select(CommunityComment).where(
        CommunityComment.post_id == post.id
    ).order_by(CommunityComment.created_at, CommunityComment.id).limit(50)).all()
    like_count = db.scalar(select(func.count(CommunityReaction.id)).where(
        CommunityReaction.post_id == post.id
    )) or 0
    liked = db.scalar(select(CommunityReaction.id).where(
        CommunityReaction.post_id == post.id,
        CommunityReaction.user_id == user.id,
    )) is not None
    return CommunityPostRead(
        id=post.id, author_display_name=display_name(db, post.author_id),
        meal_log_id=post.meal_log_id, caption=post.caption,
        created_at=post.created_at, meal=meal_log_read(db, meal),
        like_count=like_count, liked_by_me=liked, is_mine=post.author_id == user.id,
        comments=[comment_read(db, user, row) for row in comments],
    )


def visible_post(db: Session, post_id: str) -> CommunityPost:
    post = db.get(CommunityPost, post_id)
    if post is None or post.visibility != "visible":
        raise HTTPException(404, "Community post not found")
    return post


def create_post(db: Session, user: User, payload: CommunityPostCreate) -> CommunityPostRead:
    meal = db.get(MealLog, payload.meal_log_id)
    if meal is None or meal.user_id != user.id:
        raise HTTPException(404, "Confirmed meal not found")
    if db.scalar(select(CommunityPost.id).where(CommunityPost.meal_log_id == meal.id)):
        raise HTTPException(409, "Meal already shared")
    post = CommunityPost(
        author_id=user.id, meal_log_id=meal.id,
        caption=payload.caption, visibility="visible",
    )
    db.add(post)
    try:
        db.flush()
        award_event(db, user.id, "share_meal", "community_post", post.id, post.created_at)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Meal already shared") from None
    db.refresh(post)
    return post_read(db, user, post)


def list_posts(db: Session, user: User, limit: int, offset: int) -> list[CommunityPostRead]:
    posts = db.scalars(
        select(CommunityPost).where(CommunityPost.visibility == "visible")
        .order_by(CommunityPost.created_at.desc(), CommunityPost.id.desc())
        .offset(offset).limit(limit)
    ).all()
    return [post_read(db, user, post) for post in posts]


def shared_meal_log_ids(db: Session, user: User) -> list[str]:
    return list(db.scalars(select(CommunityPost.meal_log_id).where(
        CommunityPost.author_id == user.id
    )).all())


def delete_post(db: Session, user: User, post_id: str) -> None:
    post = db.get(CommunityPost, post_id)
    if post is None or post.author_id != user.id or post.visibility != "visible":
        raise HTTPException(404, "Community post not found")
    post.visibility = "removed"
    reverse_share_award(db, user.id, post.id)
    db.commit()


def create_comment(
    db: Session, user: User, post_id: str, payload: CommunityCommentCreate,
) -> CommunityCommentRead:
    visible_post(db, post_id)
    row = CommunityComment(post_id=post_id, author_id=user.id, body=payload.body)
    db.add(row)
    db.commit()
    db.refresh(row)
    return comment_read(db, user, row)


def delete_comment(db: Session, user: User, comment_id: str) -> None:
    row = db.get(CommunityComment, comment_id)
    if row is None or (row.author_id != user.id and not user.is_moderator):
        raise HTTPException(404, "Comment not found")
    db.delete(row)
    db.commit()


def like_post(db: Session, user: User, post_id: str) -> CommunityPostRead:
    post = visible_post(db, post_id)
    existing = db.scalar(select(CommunityReaction).where(
        CommunityReaction.post_id == post_id, CommunityReaction.user_id == user.id,
    ))
    if existing is None:
        db.add(CommunityReaction(post_id=post_id, user_id=user.id, created_at=utcnow()))
        db.commit()
    return post_read(db, user, post)


def unlike_post(db: Session, user: User, post_id: str) -> CommunityPostRead:
    post = visible_post(db, post_id)
    existing = db.scalar(select(CommunityReaction).where(
        CommunityReaction.post_id == post_id, CommunityReaction.user_id == user.id,
    ))
    if existing is not None:
        db.delete(existing)
        db.commit()
    return post_read(db, user, post)


def report_read(db: Session, report: CommunityReport) -> CommunityReportRead:
    post = db.get(CommunityPost, report.post_id)
    return CommunityReportRead(
        id=report.id, post_id=report.post_id,
        post_caption=post.caption, post_author=display_name(db, post.author_id),
        reason=report.reason,
        detail=report.detail, status=report.status, created_at=report.created_at,
    )


def report_post(
    db: Session, user: User, post_id: str, payload: CommunityReportCreate,
) -> CommunityReportRead:
    post = visible_post(db, post_id)
    if post.author_id == user.id:
        raise HTTPException(409, "You cannot report your own post")
    if db.scalar(select(CommunityReport.id).where(
        CommunityReport.post_id == post_id, CommunityReport.reporter_id == user.id,
    )):
        raise HTTPException(409, "Post already reported")
    report = CommunityReport(
        post_id=post_id, reporter_id=user.id, reason=payload.reason,
        detail=payload.detail, status="pending",
    )
    db.add(report)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Post already reported") from None
    db.refresh(report)
    return report_read(db, report)


def pending_reports(db: Session, user: User) -> list[CommunityReportRead]:
    if not user.is_moderator:
        raise HTTPException(403, "Moderator access required")
    reports = db.scalars(select(CommunityReport).where(
        CommunityReport.status == "pending"
    ).order_by(CommunityReport.created_at).limit(100)).all()
    return [report_read(db, row) for row in reports]


def resolve_report(
    db: Session, user: User, report_id: str, payload: CommunityReportResolve,
) -> CommunityReportRead:
    if not user.is_moderator:
        raise HTTPException(403, "Moderator access required")
    report = db.get(CommunityReport, report_id)
    if report is None:
        raise HTTPException(404, "Report not found")
    if report.status != "pending":
        raise HTTPException(409, "Report already resolved")
    post = db.get(CommunityPost, report.post_id)
    report.status = "removed" if payload.action == "remove" else "dismissed"
    report.resolved_by = user.id
    report.resolved_at = utcnow()
    if payload.action == "remove" and post.visibility == "visible":
        post.visibility = "hidden"
        reverse_share_award(db, post.author_id, post.id)
    db.commit()
    return report_read(db, report)
