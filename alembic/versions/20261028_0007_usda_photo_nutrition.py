"""Cache USDA food densities and allow reviewed photo nutrition snapshots.

Revision ID: 20261028_0007
Revises: 20261028_0006
"""

import sqlalchemy as sa
from alembic import op

revision = "20261028_0007"
down_revision = "20261028_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nutrition_foods",
        sa.Column("fdc_id", sa.Integer(), primary_key=True),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("data_type", sa.String(30), nullable=False),
        sa.Column("calories_kcal", sa.Numeric(10, 3), nullable=False),
        sa.Column("protein_g", sa.Numeric(10, 3), nullable=False),
        sa.Column("carbs_g", sa.Numeric(10, 3), nullable=False),
        sa.Column("fat_g", sa.Numeric(10, 3), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_nutrition_foods_description", "nutrition_foods", ["description"])
    op.add_column("photo_meal_records", sa.Column("nutrition_snapshot", sa.JSON(), nullable=True))
    op.add_column("photo_meal_records", sa.Column("nutrition_items", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("photo_meal_records", "nutrition_items")
    op.drop_column("photo_meal_records", "nutrition_snapshot")
    op.drop_index("ix_nutrition_foods_description", "nutrition_foods")
    op.drop_table("nutrition_foods")
