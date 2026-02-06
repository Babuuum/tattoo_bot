"""add tattoo photo file id

Revision ID: 6c2a3d4a1c9e
Revises: ef9fc6579128
Create Date: 2026-02-06
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "6c2a3d4a1c9e"
down_revision = "ef9fc6579128"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tattoos", sa.Column("photo_file_id", sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("tattoos", "photo_file_id")
