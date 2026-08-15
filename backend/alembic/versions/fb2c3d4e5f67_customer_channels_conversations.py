"""Add public customer channels and persistent B2C conversations."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "fb2c3d4e5f67"
down_revision = "fa1b2c3d4e56"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("customer_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("channel_type", sa.String(30), nullable=False, server_default="web_widget"),
        sa.Column("public_key", sa.String(80), nullable=False, unique=True),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),)
    op.create_index("ix_customer_channels_tenant_id", "customer_channels", ["tenant_id"])
    op.create_index("ix_customer_channels_employee_id", "customer_channels", ["employee_id"])
    op.create_table("customer_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customer_channels.id"), nullable=False),
        sa.Column("customer_token_hash", sa.String(64), nullable=False),
        sa.Column("customer_name", sa.String(160)), sa.Column("customer_email", sa.String(320)), sa.Column("customer_phone", sa.String(40)),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),)
    for name, table, cols in [("ix_customer_conversations_tenant_id","customer_conversations",["tenant_id"]),("ix_customer_conversations_employee_id","customer_conversations",["employee_id"]),("ix_customer_conversations_channel_id","customer_conversations",["channel_id"]),("ix_customer_conversations_customer_token_hash","customer_conversations",["customer_token_hash"])]: op.create_index(name, table, cols)
    op.create_table("customer_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customer_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="SET NULL")),
        sa.Column("role", sa.String(20), nullable=False), sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),)
    for name, cols in [("ix_customer_messages_tenant_id",["tenant_id"]),("ix_customer_messages_conversation_id",["conversation_id"]),("ix_customer_messages_run_id",["run_id"]),("ix_customer_messages_created_at",["created_at"])]: op.create_index(name,"customer_messages",cols)
    op.add_column("runs", sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_runs_conversation_id", "runs", "customer_conversations", ["conversation_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_runs_conversation_id", "runs", ["conversation_id"])

def downgrade() -> None:
    op.drop_index("ix_runs_conversation_id", table_name="runs"); op.drop_constraint("fk_runs_conversation_id", "runs", type_="foreignkey"); op.drop_column("runs", "conversation_id")
    op.drop_table("customer_messages"); op.drop_table("customer_conversations"); op.drop_table("customer_channels")
