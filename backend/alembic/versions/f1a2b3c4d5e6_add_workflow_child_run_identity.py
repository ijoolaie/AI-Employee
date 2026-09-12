"""Persist durable workflow child Run ownership identity.

Revision ID: f1a2b3c4d5e6
Revises: f8a9b0c1d2e3
"""
from alembic import op
import sqlalchemy as sa

revision = "f1a2b3c4d5e6"
down_revision = "f8a9b0c1d2e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("workflow_step_run_id", sa.UUID(), nullable=True))
    op.add_column("runs", sa.Column("workflow_parallel_branch_run_id", sa.UUID(), nullable=True))
    op.add_column("runs", sa.Column("workflow_parallel_branch_step_key", sa.String(length=255), nullable=True))
    op.create_foreign_key("fk_runs_workflow_step_run_id", "runs", "workflow_step_runs", ["workflow_step_run_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_runs_workflow_parallel_branch_run_id", "runs", "workflow_parallel_branch_runs", ["workflow_parallel_branch_run_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_runs_workflow_step_run_id", "runs", ["workflow_step_run_id"])
    op.create_index("ix_runs_workflow_parallel_branch_run_id", "runs", ["workflow_parallel_branch_run_id"])
    op.create_index("ix_runs_workflow_parallel_branch_step_key", "runs", ["workflow_parallel_branch_step_key"])
    op.create_unique_constraint("uq_runs_workflow_step_run_id", "runs", ["workflow_step_run_id"])
    op.create_unique_constraint("uq_runs_workflow_parallel_branch_step_identity", "runs", ["workflow_parallel_branch_run_id", "workflow_parallel_branch_step_key"])


def downgrade() -> None:
    op.drop_constraint("uq_runs_workflow_parallel_branch_step_identity", "runs", type_="unique")
    op.drop_constraint("uq_runs_workflow_step_run_id", "runs", type_="unique")
    op.drop_index("ix_runs_workflow_parallel_branch_step_key", table_name="runs")
    op.drop_index("ix_runs_workflow_parallel_branch_run_id", table_name="runs")
    op.drop_index("ix_runs_workflow_step_run_id", table_name="runs")
    op.drop_constraint("fk_runs_workflow_parallel_branch_run_id", "runs", type_="foreignkey")
    op.drop_constraint("fk_runs_workflow_step_run_id", "runs", type_="foreignkey")
    op.drop_column("runs", "workflow_parallel_branch_step_key")
    op.drop_column("runs", "workflow_parallel_branch_run_id")
    op.drop_column("runs", "workflow_step_run_id")
