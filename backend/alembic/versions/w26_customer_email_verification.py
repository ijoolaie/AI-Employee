"""Add verified email identity to public customer conversations."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w26_customer_email_verification"
down_revision = "w25_customer_conversation_slots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customer_conversations", sa.Column("verified_email", sa.String(length=320), nullable=True))
    op.add_column("customer_conversations", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "customer_email_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "conversation_id"],
            ["customer_conversations.tenant_id", "customer_conversations.id"],
            ondelete="CASCADE",
            name="fk_customer_email_verifications_conversation_tenant",
        ),
        sa.CheckConstraint("attempts >= 0 AND attempts <= 5", name="ck_customer_email_verifications_attempts"),
    )
    op.create_index(
        "ix_customer_email_verifications_conversation_created",
        "customer_email_verifications",
        ["tenant_id", "conversation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_customer_email_verifications_conversation_created", table_name="customer_email_verifications")
    op.drop_table("customer_email_verifications")
    op.drop_column("customer_conversations", "email_verified_at")
    op.drop_column("customer_conversations", "verified_email")
