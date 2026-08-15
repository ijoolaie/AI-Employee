"""Workflow condition steps and durable schedules.
Revision ID: a7b8c9d0e123
Revises: f1b2c3d4e506
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "a7b8c9d0e123"
down_revision = "f1b2c3d4e506"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("workflow_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("cron_expression", sa.String(100), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_workflow_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_runs.id")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "workflow_id", "cron_expression", "timezone", name="uq_workflow_schedule_definition"))
    op.create_index("ix_workflow_schedules_tenant_id", "workflow_schedules", ["tenant_id"])
    op.create_index("ix_workflow_schedules_workflow_id", "workflow_schedules", ["workflow_id"])
    op.create_index("ix_workflow_schedules_is_active", "workflow_schedules", ["is_active"])
    op.create_index("ix_workflow_schedules_next_run_at", "workflow_schedules", ["next_run_at"])

def downgrade() -> None:
    op.drop_index("ix_workflow_schedules_next_run_at", table_name="workflow_schedules")
    op.drop_index("ix_workflow_schedules_is_active", table_name="workflow_schedules")
    op.drop_index("ix_workflow_schedules_workflow_id", table_name="workflow_schedules")
    op.drop_index("ix_workflow_schedules_tenant_id", table_name="workflow_schedules")
    op.drop_table("workflow_schedules")
