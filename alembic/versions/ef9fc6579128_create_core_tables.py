"""create core tables

Revision ID: ef9fc6579128
Revises: 
Create Date: 2026-02-05 07:11:13.405036
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "ef9fc6579128"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tg_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("tg_nickname", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_tg_id", "users", ["tg_id"], unique=False)

    op.create_table(
        "styles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("multiplyer", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("views", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_styles_id", "styles", ["id"], unique=False)
    op.create_index("ix_styles_name", "styles", ["name"], unique=False)

    op.create_table(
        "tattoos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("style_id", sa.Integer(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("views", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["style_id"], ["styles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tattoos_id", "tattoos", ["id"], unique=False)
    op.create_index("ix_tattoos_name", "tattoos", ["name"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tattoo_id", sa.Integer(), nullable=True),
        sa.Column("sessions", sa.Integer(), nullable=True),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tattoo_id"], ["tattoos.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orders_id", "orders", ["id"], unique=False)

    op.create_table(
        "discounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("multiplyer", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_discounts_id", "discounts", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_discounts_id", table_name="discounts")
    op.drop_table("discounts")

    op.drop_index("ix_orders_id", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_tattoos_name", table_name="tattoos")
    op.drop_index("ix_tattoos_id", table_name="tattoos")
    op.drop_table("tattoos")

    op.drop_index("ix_styles_name", table_name="styles")
    op.drop_index("ix_styles_id", table_name="styles")
    op.drop_table("styles")

    op.drop_index("ix_users_tg_id", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
