"""Add durable acknowledgement fields to customer human handoffs."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w24_customer_handoff_ack"
down_revision = "w23_support_message_attachments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customer_conversations",
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "customer_conversations",
        sa.Column(
            "acknowledged_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_customer_conversations_acknowledged_by_user_id",
        "customer_conversations",
        ["acknowledged_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_customer_conversations_acknowledged_by_user_id",
        table_name="customer_conversations",
    )
    op.drop_column("customer_conversations", "acknowledged_by_user_id")
    op.drop_column("customer_conversations", "acknowledged_at")
