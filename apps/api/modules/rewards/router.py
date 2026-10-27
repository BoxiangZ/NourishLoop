from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.core.auth import current_user
from apps.api.core.database import get_db
from apps.api.modules.identity.models import User
from apps.api.modules.rewards.schemas import RedemptionRead, RewardOverviewRead
from apps.api.modules.rewards.service import overview, redeem

router = APIRouter(prefix="/api/v1/rewards", tags=["rewards"])


@router.get("/overview", response_model=RewardOverviewRead)
def read_overview(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return overview(db, user)


@router.post("/{reward_id}/redeem", response_model=RedemptionRead, status_code=201)
def redeem_reward(
    reward_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return redeem(db, user, reward_id)
