"""Workflow Engine foundation: versioned linear Employee action workflows.
Revision ID: f1b2c3d4e506
Revises: e8a1c4d7b902
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "f1b2c3d4e506"
down_revision = "e8a1c4d7b902"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False), sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_workflow_tenant_slug"))
    op.create_index("ix_workflows_tenant_id", "workflows", ["tenant_id"])
    op.create_index("ix_workflows_slug", "workflows", ["slug"])
    op.create_table("workflow_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False), sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("trigger_type", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workflow_id", "version_number", name="uq_workflow_version_number"))
    op.create_index("ix_workflow_versions_workflow_id", "workflow_versions", ["workflow_id"])
    op.create_table("workflow_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("workflow_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_versions.id"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("context", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output_data", postgresql.JSONB()), sa.Column("error", postgresql.JSONB()),
        sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_workflow_runs_tenant_id", "workflow_runs", ["tenant_id"])
    op.create_index("ix_workflow_runs_workflow_id", "workflow_runs", ["workflow_id"])
    op.create_index("ix_workflow_runs_status", "workflow_runs", ["status"])
    op.create_table("workflow_step_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_runs.id"), nullable=False),
        sa.Column("step_key", sa.String(100), nullable=False), sa.Column("step_type", sa.String(30), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("input_data", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output_data", postgresql.JSONB()), sa.Column("error", postgresql.JSONB()),
        sa.Column("employee_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id")),
        sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_workflow_step_runs_workflow_run_id", "workflow_step_runs", ["workflow_run_id"])
    op.create_index("ix_workflow_step_runs_status", "workflow_step_runs", ["status"])
    for code, desc in [("workflow.read","Read workflows"),("workflow.write","Create and manage workflows"),("workflow.execute","Execute workflows")]:
        op.execute(sa.text("INSERT INTO permissions (id, code, description) VALUES (:id, :code, :description) ON CONFLICT (code) DO NOTHING").bindparams(id=str(__import__('uuid').uuid4()), code=code, description=desc))

def downgrade() -> None:
    for code in ("workflow.execute","workflow.write","workflow.read"):
        op.execute(sa.text("DELETE FROM permissions WHERE code=:code").bindparams(code=code))
    op.drop_index("ix_workflow_step_runs_status", table_name="workflow_step_runs")
    op.drop_index("ix_workflow_step_runs_workflow_run_id", table_name="workflow_step_runs")
    op.drop_table("workflow_step_runs")
    op.drop_index("ix_workflow_runs_status", table_name="workflow_runs")
    op.drop_index("ix_workflow_runs_workflow_id", table_name="workflow_runs")
    op.drop_index("ix_workflow_runs_tenant_id", table_name="workflow_runs")
    op.drop_table("workflow_runs")
    op.drop_index("ix_workflow_versions_workflow_id", table_name="workflow_versions")
    op.drop_table("workflow_versions")
    op.drop_index("ix_workflows_slug", table_name="workflows")
    op.drop_index("ix_workflows_tenant_id", table_name="workflows")
    op.drop_table("workflows")
