"""Add explicit tenant access gating and operator Demo grants."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w31_tenant_demo_grants"
down_revision = "w30_tenant_invitations"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("tenants", sa.Column("access_grant_required", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table(
        "tenant_demo_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("granted_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tenant_demo_grants_tenant_id", "tenant_demo_grants", ["tenant_id"])

def downgrade() -> None:
    op.drop_index("ix_tenant_demo_grants_tenant_id", table_name="tenant_demo_grants")
    op.drop_table("tenant_demo_grants")
    op.drop_column("tenants", "access_grant_required")
