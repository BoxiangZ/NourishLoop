"""Add durable recommendation jobs and opt-in community posts.

Revision ID: 20261027_0003
Revises: 20261024_0002
"""

import sqlalchemy as sa
from alembic import op

revision = "20261027_0003"
down_revision = "20261024_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recommendation_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("meal_slot", sa.String(20), nullable=False),
        sa.Column("result_limit", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("error", sa.String(200), nullable=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("recommendation_runs.id"), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recommendation_jobs_user_id", "recommendation_jobs", ["user_id"])
    op.create_index("ix_recommendation_jobs_status", "recommendation_jobs", ["status"])
    op.create_table(
        "community_posts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "author_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "meal_log_id",
            sa.String(36),
            sa.ForeignKey("meal_logs.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("caption", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_community_posts_author_id", "community_posts", ["author_id"])


def downgrade() -> None:
    op.drop_table("community_posts")
    op.drop_table("recommendation_jobs")
