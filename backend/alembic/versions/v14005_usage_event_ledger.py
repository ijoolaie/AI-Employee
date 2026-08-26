"""Add idempotent usage event ledger for V1.4-005.

Revision ID: v14005usage
Revises: v14004merge
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v14005usage"
down_revision = "v14004merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_key", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "event_key", name="uq_usage_event_tenant_key"),
    )
    op.create_index("ix_usage_event_tenant_created", "usage_events", ["tenant_id", "created_at"])
    op.create_index("ix_usage_event_source", "usage_events", ["source_type", "source_id"])


def downgrade() -> None:
    op.drop_index("ix_usage_event_source", table_name="usage_events")
    op.drop_index("ix_usage_event_tenant_created", table_name="usage_events")
    op.drop_table("usage_events")
