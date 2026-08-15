"""Workflow execution hardening: idempotency, parallel branches and retry state.
Revision ID: f5a6b7c8d901
Revises: e4f5a6b7c809
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f5a6b7c8d901"
down_revision = ("d4f5a6b7c809", "e4f5a6b7c809")
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("workflow_runs", sa.Column("idempotency_key", sa.String(200), nullable=True))
    op.create_index("ix_workflow_runs_idempotency_key", "workflow_runs", ["idempotency_key"])
    op.create_unique_constraint("uq_workflow_run_idempotency", "workflow_runs", ["tenant_id", "workflow_id", "idempotency_key"])
    op.add_column("workflow_step_runs", sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workflow_step_runs", sa.Column("last_error", postgresql.JSONB(), nullable=True))
    op.create_index("ix_workflow_step_runs_next_retry_at", "workflow_step_runs", ["next_retry_at"])
    op.create_unique_constraint("uq_workflow_step_run_key", "workflow_step_runs", ["workflow_run_id", "step_key"])
    op.add_column("outbox_messages", sa.Column("dedupe_key", sa.String(255), nullable=True))
    op.create_index("ix_outbox_messages_dedupe_key", "outbox_messages", ["dedupe_key"])
    op.create_index("uq_outbox_dedupe_key", "outbox_messages", ["dedupe_key"], unique=True, postgresql_where=sa.text("dedupe_key IS NOT NULL"))
    op.create_table(
        "workflow_parallel_branch_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_runs.id"), nullable=False),
        sa.Column("workflow_step_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_step_runs.id"), nullable=False),
        sa.Column("branch_key", sa.String(100), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("output_data", postgresql.JSONB(), nullable=True),
        sa.Column("error", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("workflow_step_run_id", "branch_key", name="uq_workflow_parallel_branch"),
    )
    op.create_index("ix_parallel_branch_workflow_run", "workflow_parallel_branch_runs", ["workflow_run_id"])
    op.create_index("ix_parallel_branch_step_run", "workflow_parallel_branch_runs", ["workflow_step_run_id"])

def downgrade() -> None:
    op.drop_index("ix_parallel_branch_step_run", table_name="workflow_parallel_branch_runs")
    op.drop_index("ix_parallel_branch_workflow_run", table_name="workflow_parallel_branch_runs")
    op.drop_table("workflow_parallel_branch_runs")
    op.drop_index("uq_outbox_dedupe_key", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_dedupe_key", table_name="outbox_messages")
    op.drop_column("outbox_messages", "dedupe_key")
    op.drop_constraint("uq_workflow_step_run_key", "workflow_step_runs", type_="unique")
    op.drop_index("ix_workflow_step_runs_next_retry_at", table_name="workflow_step_runs")
    op.drop_column("workflow_step_runs", "last_error")
    op.drop_column("workflow_step_runs", "next_retry_at")
    op.drop_constraint("uq_workflow_run_idempotency", "workflow_runs", type_="unique")
    op.drop_index("ix_workflow_runs_idempotency_key", table_name="workflow_runs")
    op.drop_column("workflow_runs", "idempotency_key")
