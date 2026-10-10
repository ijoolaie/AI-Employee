"""Add tenant-safe file attachments to support escalation messages."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w23_support_message_attachments"
down_revision = "w22_support_escalation_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_escalation_message_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_escalation_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("files.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("file_id", name="uq_support_message_attachment_file"),
    )
    op.create_index(
        "ix_support_message_attachments_message",
        "support_escalation_message_attachments",
        ["message_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_support_message_attachments_message",
        table_name="support_escalation_message_attachments",
    )
    op.drop_table("support_escalation_message_attachments")
