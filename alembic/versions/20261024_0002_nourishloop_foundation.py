"""Add NourishLoop MVP tables alongside the historical starter tables.

Revision ID: 20261024_0002
Revises: 20260713_0001
"""

import sqlalchemy as sa
from alembic import op

revision = "20261024_0002"
down_revision = "20260713_0001"
branch_labels = None
depends_on = None


def id_column():
    return sa.Column("id", sa.String(36), primary_key=True)


def timestamps():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    op.create_table("users", id_column(), *timestamps())
    op.create_table(
        "user_profiles",
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("dietary_preferences", sa.JSON(), nullable=False),
        sa.Column("allergies", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "user_goals",
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("goal", sa.String(30), nullable=False),
        sa.Column("daily_calorie_target", sa.Float(), nullable=True),
        *timestamps(),
    )
    op.create_table(
        "user_consents",
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("analytics_opt_in", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "venues",
        id_column(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("campus_area", sa.String(120), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "menu_items",
        id_column(),
        sa.Column(
            "venue_id",
            sa.String(36),
            sa.ForeignKey("venues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("allergen_tags", sa.JSON(), nullable=False),
        sa.Column("price_hkd", sa.Float(), nullable=True),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column("source_label", sa.String(160), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_menu_items_venue_id", "menu_items", ["venue_id"])
    op.create_table(
        "nutrition_facts",
        sa.Column(
            "menu_item_id",
            sa.String(36),
            sa.ForeignKey("menu_items.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("calories_kcal", sa.Float(), nullable=False),
        sa.Column("protein_g", sa.Float(), nullable=False),
        sa.Column("carbs_g", sa.Float(), nullable=False),
        sa.Column("fat_g", sa.Float(), nullable=False),
        sa.Column("basis", sa.String(30), nullable=False),
        sa.Column("provenance", sa.String(30), nullable=False),
        sa.Column("uncertainty_note", sa.String(240), nullable=False),
    )
    op.create_table(
        "recommendation_runs",
        id_column(),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("meal_slot", sa.String(20), nullable=False),
        sa.Column("scoring_version", sa.String(30), nullable=False),
        sa.Column("scoring_config", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_recommendation_runs_user_id", "recommendation_runs", ["user_id"])
    op.create_table(
        "recommendation_items",
        id_column(),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("recommendation_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("menu_item_id", sa.String(36), sa.ForeignKey("menu_items.id"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.UniqueConstraint("run_id", "menu_item_id"),
    )
    op.create_index("ix_recommendation_items_run_id", "recommendation_items", ["run_id"])
    op.create_table(
        "recommendation_feedback",
        id_column(),
        sa.Column(
            "recommendation_item_id",
            sa.String(36),
            sa.ForeignKey("recommendation_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("helpful", sa.Boolean(), nullable=False),
        sa.Column("comment", sa.String(500), nullable=True),
        *timestamps(),
    )
    op.create_index(
        "ix_recommendation_feedback_recommendation_item_id",
        "recommendation_feedback",
        ["recommendation_item_id"],
    )
    op.create_index("ix_recommendation_feedback_user_id", "recommendation_feedback", ["user_id"])
    op.create_table(
        "user_decisions",
        id_column(),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("menu_item_id", sa.String(36), sa.ForeignKey("menu_items.id"), nullable=False),
        sa.Column(
            "recommendation_item_id",
            sa.String(36),
            sa.ForeignKey("recommendation_items.id"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_user_decisions_user_id", "user_decisions", ["user_id"])
    op.create_table(
        "meal_logs",
        id_column(),
        sa.Column(
            "decision_id",
            sa.String(36),
            sa.ForeignKey("user_decisions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("menu_item_id", sa.String(36), sa.ForeignKey("menu_items.id"), nullable=False),
        sa.Column("servings", sa.Float(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("nutrition_snapshot", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_meal_logs_user_id", "meal_logs", ["user_id"])
    op.create_index("ix_meal_logs_consumed_at", "meal_logs", ["consumed_at"])


def downgrade() -> None:
    for table in (
        "meal_logs",
        "user_decisions",
        "recommendation_feedback",
        "recommendation_items",
        "recommendation_runs",
        "nutrition_facts",
        "menu_items",
        "venues",
        "user_consents",
        "user_goals",
        "user_profiles",
        "users",
    ):
        op.drop_table(table)
