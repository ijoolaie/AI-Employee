"""Runtime enforcement for vendor/reseller/customer edition boundaries.

Revision ID: editionruntime01
Revises: rc8p0p4pwd
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "editionruntime01"
down_revision = "rc8p0p4pwd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("tenant_kind", sa.String(length=20), nullable=False, server_default="customer"))
    op.add_column("tenants", sa.Column("parent_tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("tenants", sa.Column("vendor_release_tag", sa.String(length=80), nullable=True))
    op.add_column("tenants", sa.Column("delivery_revision", sa.String(length=120), nullable=True))

    # Preserve the current platform-control-plane tenant as the vendor root.
    op.execute(sa.text("UPDATE tenants SET tenant_kind = 'vendor', vendor_release_tag = 'v1.0.1', delivery_revision = 'v1.0.1' WHERE id IN (SELECT DISTINCT tenant_id FROM users WHERE is_platform_admin = true)"))

    op.create_foreign_key("fk_tenants_parent_tenant", "tenants", "tenants", ["parent_tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_tenants_parent_tenant_id", "tenants", ["parent_tenant_id"])
    op.create_index("ix_tenants_tenant_kind", "tenants", ["tenant_kind"])
    op.alter_column("tenants", "tenant_kind", server_default=None)

    op.create_table(
        "tenant_entitlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("delegated_from_tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("feature_code", sa.String(length=120), nullable=False),
        sa.Column("quota_limit", sa.BigInteger(), nullable=True),
        sa.Column("quota_used", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "feature_code", name="uq_tenant_entitlement_feature"),
    )
    op.create_index("ix_tenant_entitlements_tenant_id", "tenant_entitlements", ["tenant_id"])
    op.create_index("ix_tenant_entitlements_delegated_from", "tenant_entitlements", ["delegated_from_tenant_id"])

    op.create_table(
        "support_escalations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("from_tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("opened_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_support_escalations_from_tenant", "support_escalations", ["from_tenant_id"])
    op.create_index("ix_support_escalations_to_tenant", "support_escalations", ["to_tenant_id"])
    op.create_index("ix_support_escalations_status", "support_escalations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_support_escalations_status", table_name="support_escalations")
    op.drop_index("ix_support_escalations_to_tenant", table_name="support_escalations")
    op.drop_index("ix_support_escalations_from_tenant", table_name="support_escalations")
    op.drop_table("support_escalations")
    op.drop_index("ix_tenant_entitlements_delegated_from", table_name="tenant_entitlements")
    op.drop_index("ix_tenant_entitlements_tenant_id", table_name="tenant_entitlements")
    op.drop_table("tenant_entitlements")
    op.drop_index("ix_tenants_tenant_kind", table_name="tenants")
    op.drop_index("ix_tenants_parent_tenant_id", table_name="tenants")
    op.drop_constraint("fk_tenants_parent_tenant", "tenants", type_="foreignkey")
    op.drop_column("tenants", "delivery_revision")
    op.drop_column("tenants", "vendor_release_tag")
    op.drop_column("tenants", "parent_tenant_id")
    op.drop_column("tenants", "tenant_kind")
