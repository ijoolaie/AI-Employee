"""Add append-only tenant-scoped support escalation messages."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w22_support_escalation_messages"
down_revision = "20261010_world_room_inventory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_escalation_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("escalation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("support_escalations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_support_escalation_messages_thread_created",
        "support_escalation_messages",
        ["escalation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_support_escalation_messages_thread_created", table_name="support_escalation_messages")
    op.drop_table("support_escalation_messages")
