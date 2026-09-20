"""Add WhatsApp webhook idempotency keys."""
from alembic import op
import sqlalchemy as sa


revision = "v148whatsappidempotency"
down_revision = "v147productsku"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customer_conversations",
        sa.Column("external_conversation_key", sa.String(length=160), nullable=True),
    )
    op.add_column(
        "customer_messages",
        sa.Column("channel_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_customer_messages_channel_id",
        "customer_messages",
        "customer_channels",
        ["channel_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "customer_messages",
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "uq_customer_conversations_external_key",
        "customer_conversations",
        ["channel_id", "external_conversation_key"],
        unique=True,
        postgresql_where=sa.text("external_conversation_key IS NOT NULL"),
    )
    op.create_index(
        "uq_customer_messages_provider_id",
        "customer_messages",
        ["tenant_id", "channel_id", "provider_message_id"],
        unique=True,
        postgresql_where=sa.text("provider_message_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_customer_messages_provider_id", table_name="customer_messages")
    op.drop_index("uq_customer_conversations_external_key", table_name="customer_conversations")
    op.drop_constraint(
        "fk_customer_messages_channel_id",
        "customer_messages",
        type_="foreignkey",
    )
    op.drop_column("customer_messages", "provider_message_id")
    op.drop_column("customer_messages", "channel_id")
    op.drop_column("customer_conversations", "external_conversation_key")
