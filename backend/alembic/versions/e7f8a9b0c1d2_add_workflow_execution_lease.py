"""Add durable WorkflowRun execution lease fields.

Revision ID: e7f8a9b0c1d2
Revises: d5e6f7a8b9c0
"""
from alembic import op
import sqlalchemy as sa

revision = "e7f8a9b0c1d2"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workflow_runs", sa.Column("execution_lease_id", sa.UUID(), nullable=True))
    op.add_column("workflow_runs", sa.Column("execution_lease_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workflow_runs", sa.Column("execution_heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_workflow_runs_execution_lease_expires_at", "workflow_runs", ["execution_lease_expires_at"])


def downgrade() -> None:
    op.drop_index("ix_workflow_runs_execution_lease_expires_at", table_name="workflow_runs")
    op.drop_column("workflow_runs", "execution_heartbeat_at")
    op.drop_column("workflow_runs", "execution_lease_expires_at")
    op.drop_column("workflow_runs", "execution_lease_id")
