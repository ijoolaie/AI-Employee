"""Phase 1 DLQ, replay and observability fields.

Revision ID: f7c8d9e0a123
Revises: f6b7c8d9e012
"""
from alembic import op
import sqlalchemy as sa

revision = "f7c8d9e0a123"
down_revision = "f6b7c8d9e012"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("outbox_messages", sa.Column("dead_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outbox_messages", sa.Column("replayed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_outbox_dead_at", "outbox_messages", ["dead_at"])

def downgrade() -> None:
    op.drop_index("ix_outbox_dead_at", table_name="outbox_messages")
    op.drop_column("outbox_messages", "replayed_at")
    op.drop_column("outbox_messages", "dead_at")
