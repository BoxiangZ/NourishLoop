from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.modules.community.models import CommunityPost
from apps.api.modules.community.schemas import CommunityPostCreate, CommunityPostRead
from apps.api.modules.identity.models import User, UserProfile
from apps.api.modules.tracking.models import MealLog
from apps.api.modules.tracking.service import meal_log_read


def post_read(db: Session, post: CommunityPost) -> CommunityPostRead:
    profile = db.get(UserProfile, post.author_id)
    meal = db.get(MealLog, post.meal_log_id)
    return CommunityPostRead(
        id=post.id,
        author_display_name=profile.display_name if profile else "NourishLoop member",
        meal_log_id=post.meal_log_id,
        caption=post.caption,
        created_at=post.created_at,
        meal=meal_log_read(db, meal),
    )


def create_post(db: Session, user: User, payload: CommunityPostCreate) -> CommunityPostRead:
    meal = db.get(MealLog, payload.meal_log_id)
    if meal is None or meal.user_id != user.id:
        raise HTTPException(404, "Confirmed meal not found")
    if db.scalar(select(CommunityPost).where(CommunityPost.meal_log_id == meal.id)):
        raise HTTPException(409, "Meal already shared")
    post = CommunityPost(
        author_id=user.id,
        meal_log_id=meal.id,
        caption=payload.caption.strip(),
    )
    db.add(post)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Meal already shared") from None
    db.refresh(post)
    return post_read(db, post)


def list_posts(db: Session, limit: int) -> list[CommunityPostRead]:
    posts = db.scalars(
        select(CommunityPost)
        .order_by(CommunityPost.created_at.desc(), CommunityPost.id.desc())
        .limit(limit)
    ).all()
    return [post_read(db, post) for post in posts]


def delete_post(db: Session, user: User, post_id: str) -> None:
    post = db.get(CommunityPost, post_id)
    if post is None or post.author_id != user.id:
        raise HTTPException(404, "Community post not found")
    db.delete(post)
    db.commit()
