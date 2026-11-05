"""Add explicit user-bound portal access grants."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w32_portal_access_grants"
down_revision = "w31_tenant_demo_grants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portal_access_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("granted_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("actor_tenant_id <> target_tenant_id", name="ck_portal_access_grant_cross_tenant"),
        sa.CheckConstraint("length(trim(reason)) > 0", name="ck_portal_access_grant_reason"),
    )
    op.create_index(
        "uq_portal_access_grant_active",
        "portal_access_grants",
        ["actor_user_id", "target_tenant_id"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_index("ix_portal_access_grants_actor_tenant", "portal_access_grants", ["actor_tenant_id"])
    op.create_index("ix_portal_access_grants_target_tenant", "portal_access_grants", ["target_tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_portal_access_grants_target_tenant", table_name="portal_access_grants")
    op.drop_index("ix_portal_access_grants_actor_tenant", table_name="portal_access_grants")
    op.drop_index("uq_portal_access_grant_active", table_name="portal_access_grants")
    op.drop_table("portal_access_grants")
