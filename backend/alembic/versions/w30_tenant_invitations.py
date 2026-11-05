"""Add tenant-scoped, single-use invitations.

Revision ID: w30_tenant_invitations
Revises: w29_vendor_admin_perms
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w30_tenant_invitations"
down_revision = "w29_vendor_admin_perms"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invited_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tenant_invitations_tenant_email", "tenant_invitations", ["tenant_id", "email"])
    op.create_index("ix_tenant_invitations_expires_at", "tenant_invitations", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_tenant_invitations_expires_at", table_name="tenant_invitations")
    op.drop_index("ix_tenant_invitations_tenant_email", table_name="tenant_invitations")
    op.drop_table("tenant_invitations")
