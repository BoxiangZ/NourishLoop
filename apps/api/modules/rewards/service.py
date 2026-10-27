from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.core.models import utcnow
from apps.api.modules.identity.models import User
from apps.api.modules.rewards.models import (
    CreditTransaction, HabitDefinition, HabitEvent, RewardItem, RewardRedemption,
)
from apps.api.modules.rewards.schemas import (
    CreditTransactionRead, HabitProgressRead, RedemptionRead, RewardOverviewRead, RewardRead,
)

HK_ZONE = ZoneInfo("Asia/Hong_Kong")


def award_event(
    db: Session, user_id: str, habit_id: str, source_type: str, source_id: str,
    occurred_at: datetime,
) -> bool:
    """Add one daily habit event and its credits inside the caller's transaction."""
    db.scalar(select(User).where(User.id == user_id).with_for_update())
    habit = db.get(HabitDefinition, habit_id)
    if habit is None:
        raise RuntimeError(f"Habit definition missing: {habit_id}")
    local_day = occurred_at.astimezone(HK_ZONE).date()
    existing = db.scalar(select(HabitEvent.id).where(
        HabitEvent.user_id == user_id,
        HabitEvent.habit_id == habit_id,
        HabitEvent.local_day == local_day,
    ))
    if existing is not None:
        return False
    event = HabitEvent(
        user_id=user_id, habit_id=habit_id, local_day=local_day,
        source_type=source_type, source_id=source_id, created_at=utcnow(),
    )
    db.add(event)
    db.flush()
    db.add(CreditTransaction(
        user_id=user_id, amount=habit.points, reason=habit_id, habit_event_id=event.id,
    ))
    return True


def credit_balance(db: Session, user_id: str) -> int:
    return int(db.scalar(select(func.coalesce(func.sum(CreditTransaction.amount), 0)).where(
        CreditTransaction.user_id == user_id
    )) or 0)


def reverse_share_award(db: Session, user_id: str, post_id: str) -> None:
    """Reverse a share's credit when the author retracts the post; caller commits."""
    db.scalar(select(User).where(User.id == user_id).with_for_update())
    event = db.scalar(select(HabitEvent).where(
        HabitEvent.user_id == user_id,
        HabitEvent.habit_id == "share_meal",
        HabitEvent.source_id == post_id,
    ))
    if event is None or event.reversed_at is not None:
        return
    original = db.scalar(select(CreditTransaction).where(
        CreditTransaction.habit_event_id == event.id
    ))
    event.reversed_at = utcnow()
    db.add(CreditTransaction(
        user_id=user_id, amount=-original.amount,
        reason="share_retracted", reversal_of_id=original.id,
    ))


def overview(db: Session, user: User) -> RewardOverviewRead:
    today = datetime.now(HK_ZONE).date()
    week_start = today - timedelta(days=today.weekday())
    definitions = db.scalars(select(HabitDefinition).order_by(HabitDefinition.id)).all()
    events = db.scalars(select(HabitEvent).where(
        HabitEvent.user_id == user.id, HabitEvent.reversed_at.is_(None)
    )).all()
    days_by_habit: dict[str, set] = {habit.id: set() for habit in definitions}
    for event in events:
        days_by_habit.setdefault(event.habit_id, set()).add(event.local_day)
    habits = []
    for habit in definitions:
        days = days_by_habit[habit.id]
        cursor = today if today in days else today - timedelta(days=1)
        streak = 0
        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)
        habits.append(HabitProgressRead(
            id=habit.id, title=habit.title, description=habit.description,
            points=habit.points, completed_today=today in days, streak_days=streak,
            completed_this_week=sum(week_start <= day <= today for day in days),
            weekly_target=habit.weekly_target,
        ))
    redeemed = set(db.scalars(select(RewardRedemption.reward_id).where(
        RewardRedemption.user_id == user.id
    )).all())
    rewards = [RewardRead(
        id=item.id, title=item.title, description=item.description,
        cost=item.cost, redeemed=item.id in redeemed,
    ) for item in db.scalars(select(RewardItem).where(RewardItem.active.is_(True)).order_by(
        RewardItem.cost, RewardItem.id
    )).all()]
    transactions = [CreditTransactionRead.model_validate({
        "id": row.id, "amount": row.amount, "reason": row.reason,
        "created_at": row.created_at,
    }) for row in db.scalars(select(CreditTransaction).where(
        CreditTransaction.user_id == user.id
    ).order_by(CreditTransaction.created_at.desc()).limit(20)).all()]
    completed = {habit.id for habit in habits if habit.completed_today}
    if "confirm_meal" not in completed:
        suggestion = "Confirm a meal you actually ate to make progress today."
    elif "share_meal" not in completed:
        suggestion = "If you want, share one confirmed meal with Community."
    else:
        suggestion = "Today's demo habits are complete. Review your weekly progress."
    return RewardOverviewRead(
        balance=credit_balance(db, user.id), suggested_next_step=suggestion, habits=habits,
        rewards=rewards, transactions=transactions,
    )


def redeem(db: Session, user: User, reward_id: str) -> RedemptionRead:
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    reward = db.get(RewardItem, reward_id)
    if reward is None or not reward.active:
        raise HTTPException(404, "Reward not found")
    if db.scalar(select(RewardRedemption.id).where(
        RewardRedemption.user_id == user.id,
        RewardRedemption.reward_id == reward_id,
    )):
        raise HTTPException(409, "Reward already redeemed")
    balance = credit_balance(db, user.id)
    if balance < reward.cost:
        raise HTTPException(409, "Not enough credits")
    redemption = RewardRedemption(
        user_id=user.id, reward_id=reward.id,
        cost_snapshot=reward.cost, created_at=utcnow(),
    )
    db.add(redemption)
    db.flush()
    db.add(CreditTransaction(
        user_id=user.id, amount=-reward.cost,
        reason="reward_redemption", redemption_id=redemption.id,
    ))
    db.commit()
    return RedemptionRead(
        id=redemption.id, reward_id=reward.id,
        cost=reward.cost, balance=balance - reward.cost,
    )
