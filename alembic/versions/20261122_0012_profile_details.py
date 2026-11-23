"""Add optional personal information and meal budget to profiles.

Revision ID: 20261122_0012
Revises: 20261122_0011
"""

import sqlalchemy as sa
from alembic import op

revision = "20261122_0012"
down_revision = "20261122_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("age", sa.Integer()))
    op.add_column("user_profiles", sa.Column("height_cm", sa.Float()))
    op.add_column("user_profiles", sa.Column("weight_kg", sa.Float()))
    op.add_column("user_profiles", sa.Column("target_weight_kg", sa.Float()))
    op.add_column("user_profiles", sa.Column("activity_level", sa.String(16)))
    op.add_column("user_profiles", sa.Column("meal_budget_hkd", sa.Float()))


def downgrade() -> None:
    for field in (
        "meal_budget_hkd", "activity_level", "target_weight_kg", "weight_kg", "height_cm", "age",
    ):
        op.drop_column("user_profiles", field)
