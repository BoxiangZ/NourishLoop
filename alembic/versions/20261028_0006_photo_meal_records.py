"""Store user-confirmed photo meal names without retaining images or estimated nutrition.

Revision ID: 20261028_0006
Revises: 20261028_0005
"""

import sqlalchemy as sa
from alembic import op

revision = "20261028_0006"
down_revision = "20261028_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "photo_meal_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("foods", sa.JSON(), nullable=False),
        sa.Column("notes", sa.String(500), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_photo_meal_records_user_id", "photo_meal_records", ["user_id"])
    op.create_index("ix_photo_meal_records_consumed_at", "photo_meal_records", ["consumed_at"])


def downgrade() -> None:
    op.drop_index("ix_photo_meal_records_consumed_at", "photo_meal_records")
    op.drop_index("ix_photo_meal_records_user_id", "photo_meal_records")
    op.drop_table("photo_meal_records")
