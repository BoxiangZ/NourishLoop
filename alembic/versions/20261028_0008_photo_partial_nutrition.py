"""Preserve partial photo nutrition without counting it as a whole meal.

Revision ID: 20261028_0008
Revises: 20261028_0007
"""

import sqlalchemy as sa
from alembic import op

revision = "20261028_0008"
down_revision = "20261028_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("photo_meal_records", sa.Column(
        "nutrition_status", sa.String(20), nullable=False, server_default="none",
    ))
    op.add_column("photo_meal_records", sa.Column(
        "unresolved_foods", sa.JSON(), nullable=False, server_default="[]",
    ))
    op.execute("UPDATE photo_meal_records SET nutrition_status = 'complete' "
               "WHERE nutrition_snapshot IS NOT NULL "
               "AND CAST(nutrition_snapshot AS TEXT) != 'null'")


def downgrade() -> None:
    op.drop_column("photo_meal_records", "unresolved_foods")
    op.drop_column("photo_meal_records", "nutrition_status")
