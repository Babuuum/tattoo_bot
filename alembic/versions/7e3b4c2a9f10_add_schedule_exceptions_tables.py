"""add schedule exceptions tables (day_off, blocked_slot)

Revision ID: 7e3b4c2a9f10
Revises: 6c2a3d4a1c9e
Create Date: 2026-02-11
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "7e3b4c2a9f10"
down_revision = "6c2a3d4a1c9e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "day_off",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("date"),
    )
    op.create_index("ix_day_off_date", "day_off", ["date"], unique=False)

    op.create_table(
        "blocked_slot",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time", sa.Time(), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("date", "time"),
    )
    op.create_index("ix_blocked_slot_date", "blocked_slot", ["date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_blocked_slot_date", table_name="blocked_slot")
    op.drop_table("blocked_slot")

    op.drop_index("ix_day_off_date", table_name="day_off")
    op.drop_table("day_off")
