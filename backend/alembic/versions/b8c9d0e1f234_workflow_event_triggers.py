"""Workflow event triggers and webhook deliveries.
Revision ID: b8c9d0e1f234
Revises: a7b8c9d0e123
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "b8c9d0e1f234"
down_revision = "a7b8c9d0e123"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("workflow_event_triggers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("webhook_secret", sa.String(255), nullable=False),
        sa.Column("webhook_secret_hash", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_workflow_event_triggers_tenant_id", "workflow_event_triggers", ["tenant_id"])
    op.create_index("ix_workflow_event_triggers_workflow_id", "workflow_event_triggers", ["workflow_id"])
    op.create_index("ix_workflow_event_triggers_event_type", "workflow_event_triggers", ["event_type"])
    op.create_index("ix_workflow_event_triggers_is_active", "workflow_event_triggers", ["is_active"])
    op.create_table("workflow_event_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("trigger_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_event_triggers.id"), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="received"),
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_runs.id")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", postgresql.JSONB()),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("trigger_id", "event_id", name="uq_workflow_event_delivery_trigger_event"))
    op.create_index("ix_workflow_event_deliveries_tenant_id", "workflow_event_deliveries", ["tenant_id"])
    op.create_index("ix_workflow_event_deliveries_trigger_id", "workflow_event_deliveries", ["trigger_id"])
    op.create_index("ix_workflow_event_deliveries_status", "workflow_event_deliveries", ["status"])
    for code, desc in [("workflow.event.read","Read workflow event triggers"),("workflow.event.write","Create and manage workflow event triggers"),("workflow.event.ingest","Receive workflow webhook events")]:
        op.execute(sa.text("INSERT INTO permissions (id, code, description) VALUES (:id, :code, :description) ON CONFLICT (code) DO NOTHING").bindparams(id=str(__import__('uuid').uuid4()), code=code, description=desc))

def downgrade() -> None:
    for code in ("workflow.event.ingest","workflow.event.write","workflow.event.read"):
        op.execute(sa.text("DELETE FROM permissions WHERE code=:code").bindparams(code=code))
    op.drop_index("ix_workflow_event_deliveries_status", table_name="workflow_event_deliveries")
    op.drop_index("ix_workflow_event_deliveries_trigger_id", table_name="workflow_event_deliveries")
    op.drop_index("ix_workflow_event_deliveries_tenant_id", table_name="workflow_event_deliveries")
    op.drop_table("workflow_event_deliveries")
    op.drop_index("ix_workflow_event_triggers_is_active", table_name="workflow_event_triggers")
    op.drop_index("ix_workflow_event_triggers_event_type", table_name="workflow_event_triggers")
    op.drop_index("ix_workflow_event_triggers_workflow_id", table_name="workflow_event_triggers")
    op.drop_index("ix_workflow_event_triggers_tenant_id", table_name="workflow_event_triggers")
    op.drop_table("workflow_event_triggers")
