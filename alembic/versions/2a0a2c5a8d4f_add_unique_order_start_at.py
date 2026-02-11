"""add unique constraint on orders.start_at

Revision ID: 2a0a2c5a8d4f
Revises: 7e3b4c2a9f10
Create Date: 2026-02-11
"""

from __future__ import annotations

from alembic import op

revision = "2a0a2c5a8d4f"
down_revision = "7e3b4c2a9f10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enforce "one order per slot" at DB level.
    op.create_index(
        "uq_orders_start_at",
        "orders",
        ["start_at"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_orders_start_at", table_name="orders")
