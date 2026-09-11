"""Add durable parallel branch execution lease and child identity.

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
"""
from alembic import op
import sqlalchemy as sa

revision = "f8a9b0c1d2e3"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workflow_parallel_branch_runs", sa.Column("employee_run_id", sa.UUID(), nullable=True))
    op.add_column("workflow_parallel_branch_runs", sa.Column("current_step_position", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("workflow_parallel_branch_runs", sa.Column("execution_lease_id", sa.UUID(), nullable=True))
    op.add_column("workflow_parallel_branch_runs", sa.Column("execution_lease_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workflow_parallel_branch_runs", sa.Column("execution_heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_parallel_branch_employee_run", "workflow_parallel_branch_runs", "runs", ["employee_run_id"], ["id"])
    op.create_index("ix_workflow_parallel_branch_runs_execution_lease_expires_at", "workflow_parallel_branch_runs", ["execution_lease_expires_at"])


def downgrade() -> None:
    op.drop_index("ix_workflow_parallel_branch_runs_execution_lease_expires_at", table_name="workflow_parallel_branch_runs")
    op.drop_constraint("fk_parallel_branch_employee_run", "workflow_parallel_branch_runs", type_="foreignkey")
    op.drop_column("workflow_parallel_branch_runs", "execution_heartbeat_at")
    op.drop_column("workflow_parallel_branch_runs", "execution_lease_expires_at")
    op.drop_column("workflow_parallel_branch_runs", "execution_lease_id")
    op.drop_column("workflow_parallel_branch_runs", "current_step_position")
    op.drop_column("workflow_parallel_branch_runs", "employee_run_id")
