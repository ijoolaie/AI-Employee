"""Durable human approval/wait-resume for workflow steps.
Revision ID: c2d3e4f5a607
Revises: b8c9d0e1f234
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "c2d3e4f5a607"
down_revision = "b8c9d0e1f234"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("workflow_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_runs.id"), nullable=False),
        sa.Column("workflow_step_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_step_runs.id"), nullable=False),
        sa.Column("step_key", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("decision_reason", sa.Text()),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workflow_run_id", "workflow_step_run_id", name="uq_workflow_approval_step"))
    for idx, cols in [("ix_workflow_approvals_tenant_id", ["tenant_id"]),("ix_workflow_approvals_workflow_run_id", ["workflow_run_id"]),("ix_workflow_approvals_workflow_step_run_id", ["workflow_step_run_id"]),("ix_workflow_approvals_status", ["status"]),("ix_workflow_approvals_expires_at", ["expires_at"])]:
        op.create_index(idx, "workflow_approvals", cols)
    for code, desc in [("workflow.approval.read","Read workflow human approvals"),("workflow.approval.decide","Approve or reject workflow steps")]:
        op.execute(sa.text("INSERT INTO permissions (id, code, description) VALUES (:id, :code, :description) ON CONFLICT (code) DO NOTHING").bindparams(id=str(__import__('uuid').uuid4()), code=code, description=desc))

def downgrade() -> None:
    for code in ("workflow.approval.decide","workflow.approval.read"):
        op.execute(sa.text("DELETE FROM permissions WHERE code=:code").bindparams(code=code))
    for idx in ("ix_workflow_approvals_expires_at","ix_workflow_approvals_status","ix_workflow_approvals_workflow_step_run_id","ix_workflow_approvals_workflow_run_id","ix_workflow_approvals_tenant_id"):
        op.drop_index(idx, table_name="workflow_approvals")
    op.drop_table("workflow_approvals")
