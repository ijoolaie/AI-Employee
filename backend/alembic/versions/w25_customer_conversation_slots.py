"""Persist tenant-scoped customer support slots with source-message provenance."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w25_customer_conversation_slots"
down_revision = "w24_customer_handoff_ack"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite unique keys make tenant/conversation/source consistency a
    # database invariant, not merely an application-level query convention.
    op.create_unique_constraint(
        "uq_customer_conversations_tenant_id_id",
        "customer_conversations",
        ["tenant_id", "id"],
    )
    op.create_unique_constraint(
        "uq_customer_messages_tenant_conversation_id",
        "customer_messages",
        ["tenant_id", "conversation_id", "id"],
    )
    op.create_table(
        "customer_conversation_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slot_name", sa.String(length=40), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "slot_name IN ('city', 'order_id', 'payment_reference', 'product', 'color', 'size', 'quantity', 'reason', 'issue_details')",
            name="ck_customer_conversation_slots_name",
        ),
        sa.CheckConstraint(
            "(slot_name = 'quantity' AND jsonb_typeof(value) = 'number') OR "
            "(slot_name <> 'quantity' AND jsonb_typeof(value) = 'string')",
            name="ck_customer_conversation_slots_value_type",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "conversation_id"],
            ["customer_conversations.tenant_id", "customer_conversations.id"],
            ondelete="CASCADE",
            name="fk_customer_conversation_slots_conversation_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "conversation_id", "source_message_id"],
            ["customer_messages.tenant_id", "customer_messages.conversation_id", "customer_messages.id"],
            ondelete="CASCADE",
            name="fk_customer_conversation_slots_source_message",
        ),
        sa.UniqueConstraint(
            "tenant_id", "conversation_id", "slot_name",
            name="uq_customer_conversation_slots_current",
        ),
    )
    op.create_index(
        "ix_customer_conversation_slots_expiry",
        "customer_conversation_slots",
        ["tenant_id", "conversation_id", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_customer_conversation_slots_expiry", table_name="customer_conversation_slots")
    op.drop_table("customer_conversation_slots")
    op.drop_constraint(
        "uq_customer_messages_tenant_conversation_id",
        "customer_messages",
        type_="unique",
    )
    op.drop_constraint(
        "uq_customer_conversations_tenant_id_id",
        "customer_conversations",
        type_="unique",
    )
