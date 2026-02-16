"""add pricing config tables

Revision ID: 9f3c1b2a7d10
Revises: 2a0a2c5a8d4f
Create Date: 2026-02-14
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "9f3c1b2a7d10"
down_revision = "2a0a2c5a8d4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pricing_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("base_price", sa.Integer(), nullable=False),
        sa.Column("min_price", sa.Integer(), nullable=False),
        sa.Column("rounding_policy", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pricing_config_id", "pricing_config", ["id"], unique=False)
    op.create_index(
        "ix_pricing_config_active", "pricing_config", ["active"], unique=False
    )

    op.create_table(
        "pricing_style_coefficient",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pricing_config_id", sa.Integer(), nullable=False),
        sa.Column("style_id", sa.Integer(), nullable=False),
        sa.Column("coefficient", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.ForeignKeyConstraint(
            ["pricing_config_id"],
            ["pricing_config.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["style_id"], ["styles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "pricing_config_id",
            "style_id",
            name="uq_pricing_style_coefficient_config_style",
        ),
    )
    op.create_index(
        "ix_pricing_style_coefficient_id",
        "pricing_style_coefficient",
        ["id"],
        unique=False,
    )

    op.create_table(
        "pricing_body_zone_coefficient",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pricing_config_id", sa.Integer(), nullable=False),
        sa.Column("body_zone", sa.String(length=50), nullable=False),
        sa.Column("coefficient", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.ForeignKeyConstraint(
            ["pricing_config_id"],
            ["pricing_config.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "pricing_config_id",
            "body_zone",
            name="uq_pricing_body_zone_coefficient_config_zone",
        ),
    )
    op.create_index(
        "ix_pricing_body_zone_coefficient_id",
        "pricing_body_zone_coefficient",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pricing_body_zone_coefficient_id",
        table_name="pricing_body_zone_coefficient",
    )
    op.drop_table("pricing_body_zone_coefficient")

    op.drop_index(
        "ix_pricing_style_coefficient_id",
        table_name="pricing_style_coefficient",
    )
    op.drop_table("pricing_style_coefficient")

    op.drop_index("ix_pricing_config_active", table_name="pricing_config")
    op.drop_index("ix_pricing_config_id", table_name="pricing_config")
    op.drop_table("pricing_config")
