"""Add provider-neutral refund/reversal lifecycle state.

Revision ID: v14006refund
Revises: v14006merge
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v14006refund"
down_revision = "v14006merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_refunds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation", sa.String(length=20), nullable=False, server_default="refund"),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="stripe"),
        sa.Column("provider_refund_id", sa.String(length=255), nullable=True),
        sa.Column("provider_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column("provider_charge_id", sa.String(length=255), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="usd"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_payment_refund_tenant_idempotency"),
        sa.UniqueConstraint("provider", "provider_refund_id", name="uq_payment_refund_provider_id"),
    )
    op.create_index("ix_payment_refund_tenant_status", "payment_refunds", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_payment_refund_tenant_status", table_name="payment_refunds")
    op.drop_table("payment_refunds")
