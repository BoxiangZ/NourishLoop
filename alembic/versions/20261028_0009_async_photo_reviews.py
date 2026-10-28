"""Add asynchronous photo reviews to existing photo meals.

Revision ID: 20261028_0009
Revises: 20261028_0008
"""

import sqlalchemy as sa
from alembic import op

revision = "20261028_0009"
down_revision = "20261028_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = [
        sa.Column("review_status", sa.String(20), nullable=False, server_default="not_requested"),
        sa.Column("review_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_claimed_at", sa.DateTime(timezone=True)),
        sa.Column("review_claim_token", sa.String(36)),
        sa.Column("review_error", sa.String(120)),
        sa.Column("review_log", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("image_path", sa.String(500)),
        sa.Column("image_type", sa.String(30)),
        sa.Column("ai_review", sa.JSON()),
        sa.Column("review_questions", sa.JSON(), nullable=False, server_default="[]"),
    ]
    for column in columns:
        op.add_column("photo_meal_records", column)


def downgrade() -> None:
    for name in (
        "review_questions", "ai_review", "image_type", "image_path", "review_log",
        "review_error", "review_claim_token", "review_claimed_at", "review_attempts", "review_status",
    ):
        op.drop_column("photo_meal_records", name)
