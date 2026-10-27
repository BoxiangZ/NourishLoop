from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, event,
)
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.core.database import Base
from apps.api.core.models import IdMixin, TimestampMixin


class HabitDefinition(Base):
    __tablename__ = "habit_definitions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    weekly_target: Mapped[int] = mapped_column(Integer, nullable=False)


class HabitEvent(Base, IdMixin):
    __tablename__ = "habit_events"
    __table_args__ = (UniqueConstraint("user_id", "habit_id", "local_day"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    habit_id: Mapped[str] = mapped_column(ForeignKey("habit_definitions.id"), nullable=False)
    local_day: Mapped[date] = mapped_column(Date, nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RewardItem(Base):
    __tablename__ = "reward_items"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)


class RewardRedemption(Base, IdMixin):
    __tablename__ = "reward_redemptions"
    __table_args__ = (UniqueConstraint("user_id", "reward_id"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    reward_id: Mapped[str] = mapped_column(ForeignKey("reward_items.id"), nullable=False)
    cost_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CreditTransaction(Base, IdMixin, TimestampMixin):
    __tablename__ = "credit_transactions"
    __table_args__ = (CheckConstraint("amount <> 0"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(40), nullable=False)
    habit_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("habit_events.id"), unique=True, nullable=True
    )
    redemption_id: Mapped[str | None] = mapped_column(
        ForeignKey("reward_redemptions.id"), unique=True, nullable=True
    )
    reversal_of_id: Mapped[str | None] = mapped_column(
        ForeignKey("credit_transactions.id"), unique=True, nullable=True
    )


@event.listens_for(CreditTransaction, "before_update")
@event.listens_for(CreditTransaction, "before_delete")
def reject_ledger_mutation(_mapper, _connection, _target) -> None:
    raise ValueError("Credit ledger rows are append-only")
