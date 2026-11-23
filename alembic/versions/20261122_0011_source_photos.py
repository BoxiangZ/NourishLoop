"""Add photo attribution to published dishes and exercises.

Revision ID: 20261122_0011
Revises: 20261122_0010
"""

import sqlalchemy as sa
from alembic import op

revision = "20261122_0011"
down_revision = "20261122_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("published_dishes", "exercises"):
        op.add_column(table, sa.Column("source_photo", sa.JSON(none_as_null=True)))


def downgrade() -> None:
    for table in ("exercises", "published_dishes"):
        op.drop_column(table, "source_photo")
