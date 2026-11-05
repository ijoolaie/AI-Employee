"""Add expiring user-bound tenant action grants."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w33_tenant_action_grants"
down_revision = "w32_portal_access_grants"
branch_labels = None
depends_on = None

ACTION_CODES = (
    "vendor.tenant.read",
    "vendor.reseller.read",
    "vendor.reseller.create",
    "vendor.reseller.manage",
    "vendor.customer.read",
    "vendor.customer.create",
    "vendor.customer.manage",
    "reseller.customer.create",
    "reseller.customer.read",
    "reseller.customer.manage",
    "reseller.entitlement.delegate",
)


def upgrade() -> None:
    op.create_table(
        "tenant_action_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_code", sa.String(100), nullable=False),
        sa.Column("granted_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("length(trim(reason)) > 0", name="ck_tenant_action_grant_reason"),
        sa.CheckConstraint("expires_at > created_at", name="ck_tenant_action_grant_expiry"),
        sa.CheckConstraint(
            "action_code IN (" + ", ".join("'" + code + "'" for code in ACTION_CODES) + ")",
            name="ck_tenant_action_grant_action_code",
        ),
    )
    op.create_index(
        "uq_tenant_action_grant_active",
        "tenant_action_grants",
        ["user_id", "tenant_id", "action_code"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_index("ix_tenant_action_grants_tenant_user", "tenant_action_grants", ["tenant_id", "user_id"])


def downgrade() -> None:
    op.drop_index("ix_tenant_action_grants_tenant_user", table_name="tenant_action_grants")
    op.drop_index("uq_tenant_action_grant_active", table_name="tenant_action_grants")
    op.drop_table("tenant_action_grants")
