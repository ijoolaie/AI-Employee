"""Transactional outbox for durable post-commit dispatch.
Revision ID: d3e4f5a6b708
Revises: c2d3e4f5a607
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "d3e4f5a6b708"
down_revision = "c2d3e4f5a607"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "outbox_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("kind", sa.String(80), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("dispatched_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_outbox_messages_tenant_id", "outbox_messages", ["tenant_id"])
    op.create_index("ix_outbox_messages_kind", "outbox_messages", ["kind"])
    op.create_index("ix_outbox_messages_status", "outbox_messages", ["status"])
    op.create_index("ix_outbox_messages_available_at", "outbox_messages", ["available_at"])
    op.create_index("ix_outbox_pending_available", "outbox_messages", ["status", "available_at"])

def downgrade() -> None:
    op.drop_index("ix_outbox_pending_available", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_available_at", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_status", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_kind", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_tenant_id", table_name="outbox_messages")
    op.drop_table("outbox_messages")
