from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class HabitProgressRead(BaseModel):
    id: str
    title: str
    description: str
    points: int
    completed_today: bool
    streak_days: int
    completed_this_week: int
    weekly_target: int


class RewardRead(BaseModel):
    id: str
    title: str
    description: str
    cost: int
    redeemed: bool


class CreditTransactionRead(BaseModel):
    id: str
    amount: int
    reason: str
    created_at: datetime


class RewardOverviewRead(BaseModel):
    balance: int
    suggested_next_step: str
    habits: list[HabitProgressRead]
    rewards: list[RewardRead]
    transactions: list[CreditTransactionRead]


class RedemptionRead(BaseModel):
    id: str
    reward_id: str
    cost: int
    balance: int
