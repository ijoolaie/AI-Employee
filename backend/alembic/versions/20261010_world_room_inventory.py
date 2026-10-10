"""Persist tenant-scoped room inventory linked to World entitlements.

Revision ID: 20261010_world_room_inventory
Revises: 20261010_world_room_lease
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261010_world_room_inventory"
down_revision = "20261010_world_room_lease"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "world_room_inventory",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entitlement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_code", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="provisioned"),
        sa.Column("scene_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('provisioned', 'suspended')", name="ck_world_room_inventory_status"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["entitlement_id"], ["world_feature_entitlements.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "item_code", name="uq_world_room_inventory_tenant_item"),
        sa.UniqueConstraint("entitlement_id", name="uq_world_room_inventory_entitlement"),
    )
    op.create_index(
        "ix_world_room_inventory_tenant_status",
        "world_room_inventory",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_world_room_inventory_tenant_status", table_name="world_room_inventory")
    op.drop_table("world_room_inventory")
