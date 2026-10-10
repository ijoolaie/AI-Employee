"""Persist configured World room lease duration and entitlement expiry.

Revision ID: 20261010_world_room_lease
Revises: 20261010_world_support
"""
from alembic import op
import sqlalchemy as sa

revision = "20261010_world_room_lease"
down_revision = "20261010_world_support"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "world_catalogue_items",
        sa.Column("lease_duration_days", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        "ck_world_catalogue_lease_duration",
        "world_catalogue_items",
        "(lease_duration_days IS NULL OR lease_duration_days BETWEEN 1 AND 3650) "
        "AND (item_type = 'room' OR lease_duration_days IS NULL)",
    )
    op.add_column(
        "world_feature_entitlements",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_world_feature_entitlements_expires_at",
        "world_feature_entitlements",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_world_feature_entitlements_expires_at", table_name="world_feature_entitlements")
    op.drop_column("world_feature_entitlements", "expires_at")
    op.drop_constraint("ck_world_catalogue_lease_duration", "world_catalogue_items", type_="check")
    op.drop_column("world_catalogue_items", "lease_duration_days")
