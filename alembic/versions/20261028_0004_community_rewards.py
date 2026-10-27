"""Add community interactions, moderation and auditable habit rewards.

Revision ID: 20261028_0004
Revises: 20261027_0003
"""

import sqlalchemy as sa
from alembic import op

revision = "20261028_0004"
down_revision = "20261027_0003"
branch_labels = None
depends_on = None


def identity_columns():
    return sa.Column("id", sa.String(36), primary_key=True)


def owned_fk(name: str, target: str):
    return sa.Column(
        name, sa.String(36), sa.ForeignKey(target, ondelete="CASCADE"), nullable=False
    )


def timestamps():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("is_moderator", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.add_column(
        "community_posts",
        sa.Column("visibility", sa.String(20), server_default="visible", nullable=False),
    )
    op.create_table(
        "community_comments",
        identity_columns(),
        owned_fk("post_id", "community_posts.id"),
        owned_fk("author_id", "users.id"),
        sa.Column("body", sa.String(500), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_community_comments_post_id", "community_comments", ["post_id"])
    op.create_index("ix_community_comments_author_id", "community_comments", ["author_id"])
    op.create_table(
        "community_reactions",
        identity_columns(),
        owned_fk("post_id", "community_posts.id"),
        owned_fk("user_id", "users.id"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("post_id", "user_id"),
    )
    op.create_index("ix_community_reactions_post_id", "community_reactions", ["post_id"])
    op.create_index("ix_community_reactions_user_id", "community_reactions", ["user_id"])
    op.create_table(
        "community_reports",
        identity_columns(),
        owned_fk("post_id", "community_posts.id"),
        owned_fk("reporter_id", "users.id"),
        sa.Column("reason", sa.String(40), nullable=False),
        sa.Column("detail", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("resolved_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("post_id", "reporter_id"),
        *timestamps(),
    )
    op.create_index("ix_community_reports_post_id", "community_reports", ["post_id"])
    op.create_index("ix_community_reports_reporter_id", "community_reports", ["reporter_id"])
    op.create_table(
        "habit_definitions",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("description", sa.String(240), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("weekly_target", sa.Integer(), nullable=False),
    )
    op.create_table(
        "habit_events",
        identity_columns(),
        owned_fk("user_id", "users.id"),
        sa.Column("habit_id", sa.String(40), sa.ForeignKey("habit_definitions.id"), nullable=False),
        sa.Column("local_day", sa.Date(), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "habit_id", "local_day"),
    )
    op.create_index("ix_habit_events_user_id", "habit_events", ["user_id"])
    op.create_table(
        "reward_items",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("description", sa.String(240), nullable=False),
        sa.Column("cost", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "reward_redemptions",
        identity_columns(),
        owned_fk("user_id", "users.id"),
        sa.Column("reward_id", sa.String(40), sa.ForeignKey("reward_items.id"), nullable=False),
        sa.Column("cost_snapshot", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "reward_id"),
    )
    op.create_index("ix_reward_redemptions_user_id", "reward_redemptions", ["user_id"])
    op.create_table(
        "credit_transactions",
        identity_columns(),
        owned_fk("user_id", "users.id"),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(40), nullable=False),
        sa.Column("habit_event_id", sa.String(36), sa.ForeignKey("habit_events.id"), unique=True),
        sa.Column(
            "redemption_id", sa.String(36), sa.ForeignKey("reward_redemptions.id"), unique=True
        ),
        sa.Column(
            "reversal_of_id", sa.String(36), sa.ForeignKey("credit_transactions.id"),
            unique=True,
        ),
        sa.CheckConstraint("amount <> 0"),
        *timestamps(),
    )
    op.create_index("ix_credit_transactions_user_id", "credit_transactions", ["user_id"])


def downgrade() -> None:
    for table in (
        "credit_transactions", "reward_redemptions", "reward_items", "habit_events",
        "habit_definitions", "community_reports", "community_reactions", "community_comments",
    ):
        op.drop_table(table)
    op.drop_column("community_posts", "visibility")
    op.drop_column("users", "is_moderator")
