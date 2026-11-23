"""Add sourced menu listings and gym equipment.

Revision ID: 20261122_0010
Revises: 20261028_0009
"""

import sqlalchemy as sa
from alembic import op

revision = "20261122_0010"
down_revision = "20261028_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "published_dishes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("venue_id", sa.String(36), sa.ForeignKey("venues.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("price_hkd", sa.Float()),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("source_scope", sa.String(20), nullable=False),
        sa.Column("reference_note", sa.String(240), nullable=False),
        sa.Column("source_checked_at", sa.Date(), nullable=False),
    )
    op.create_index("ix_published_dishes_venue_id", "published_dishes", ["venue_id"])
    op.create_table(
        "gym_equipment",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("location", sa.String(160), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("source_checked_at", sa.Date(), nullable=False),
    )
    op.add_column("exercises", sa.Column("equipment_detail", sa.String(100)))


def downgrade() -> None:
    op.drop_column("exercises", "equipment_detail")
    op.drop_table("gym_equipment")
    op.drop_index("ix_published_dishes_venue_id", table_name="published_dishes")
    op.drop_table("published_dishes")
