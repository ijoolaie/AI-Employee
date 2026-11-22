"""Add secure, verified account email changes."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w36_secure_account_email_change"
down_revision = "w35_workflow_delegated_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("pending_email", sa.String(length=320), nullable=True))
    op.create_table(
        "email_change_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("new_email", sa.String(length=320), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_email_change_tokens_user_created", "email_change_tokens", ["user_id", "created_at"])
    op.create_index("uq_email_change_tokens_hash", "email_change_tokens", ["token_hash"], unique=True)
    # Enforce tenant-scoped case-insensitive uniqueness for all new and existing identities.
    op.create_index("uq_users_tenant_lower_email", "users", ["tenant_id", sa.text("lower(email)")], unique=True)
    op.create_index(
        "uq_users_tenant_lower_pending_email", "users",
        ["tenant_id", sa.text("lower(pending_email)")], unique=True,
        postgresql_where=sa.text("pending_email IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_users_tenant_lower_pending_email", table_name="users")
    op.drop_index("uq_users_tenant_lower_email", table_name="users")
    op.drop_index("uq_email_change_tokens_hash", table_name="email_change_tokens")
    op.drop_index("ix_email_change_tokens_user_created", table_name="email_change_tokens")
    op.drop_table("email_change_tokens")
    op.drop_column("users", "pending_email")
