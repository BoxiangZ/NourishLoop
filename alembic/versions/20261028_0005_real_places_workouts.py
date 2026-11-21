"""Add sourced place directory, external discussion notes and workout tracking.

Revision ID: 20261028_0005
Revises: 20261028_0004
"""

import sqlalchemy as sa
from alembic import op

revision = "20261028_0005"
down_revision = "20261028_0004"
branch_labels = None
depends_on = None


def timestamps():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    op.add_column(
        "venues",
        sa.Column(
            "scope",
            sa.String(20),
            server_default="demo",
            nullable=False,
        ),
    )
    op.add_column("venues", sa.Column("source_url", sa.String(500), nullable=True))
    op.add_column("venues", sa.Column("source_checked_at", sa.Date(), nullable=True))
    op.create_table(
        "external_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("source_platform", sa.String(40), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("source_checked_at", sa.Date(), nullable=False),
    )
    op.create_table(
        "exercises",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("muscle_group", sa.String(30), nullable=False),
        sa.Column("equipment", sa.String(30), nullable=False),
        sa.Column("difficulty", sa.String(30), nullable=False),
        sa.Column("instructions", sa.String(500), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=False),
    )
    op.create_index("ix_exercises_muscle_group", "exercises", ["muscle_group"])
    op.create_table(
        "workout_profiles",
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("stage", sa.String(20), nullable=False),
        sa.Column("equipment", sa.JSON(), nullable=False),
        sa.Column("days_per_week", sa.Integer(), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "workout_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("requested_focus", sa.String(30), nullable=False),
        sa.Column("focus", sa.String(30), nullable=False),
        sa.Column("stage", sa.String(20), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("prescription", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("explanation_source", sa.String(20), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_workout_plans_user_id", "workout_plans", ["user_id"])
    op.create_table(
        "workout_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "plan_id",
            sa.String(36),
            sa.ForeignKey("workout_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("plan_id"),
    )
    op.create_index("ix_workout_sessions_user_id", "workout_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_workout_sessions_user_id", "workout_sessions")
    op.drop_table("workout_sessions")
    op.drop_index("ix_workout_plans_user_id", "workout_plans")
    op.drop_table("workout_plans")
    op.drop_table("workout_profiles")
    op.drop_index("ix_exercises_muscle_group", "exercises")
    op.drop_table("exercises")
    op.drop_table("external_notes")
    op.drop_column("venues", "source_checked_at")
    op.drop_column("venues", "source_url")
    op.drop_column("venues", "scope")
