from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.core.database import Base
from apps.api.core.models import IdMixin, TimestampMixin


class CommunityPost(Base, IdMixin, TimestampMixin):
    __tablename__ = "community_posts"

    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    meal_log_id: Mapped[str] = mapped_column(
        ForeignKey("meal_logs.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    caption: Mapped[str] = mapped_column(String(500), nullable=False)
