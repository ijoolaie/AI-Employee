"""Fix workflow step timeout/cancellation schema.

Revision ID: 61661b7e79f8
Revises: fa1b2c3d4e56
"""
from alembic import op
import sqlalchemy as sa

revision = "61661b7e79f8"
down_revision = "fa1b2c3d4e56"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # e4f5a6b7c809 placed this index on workflow_runs.deadline_at.
    # The current model keeps the column but intentionally removes that index.
    op.drop_index(
        "ix_workflow_runs_deadline_at",
        table_name="workflow_runs",
    )

    # Timeout/cancellation state belongs to individual workflow step runs.
    op.add_column(
        "workflow_step_runs",
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "workflow_step_runs",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "workflow_step_runs",
        sa.Column("cancel_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workflow_step_runs", "cancel_reason")
    op.drop_column("workflow_step_runs", "cancelled_at")
    op.drop_column("workflow_step_runs", "deadline_at")

    op.create_index(
        "ix_workflow_runs_deadline_at",
        "workflow_runs",
        ["deadline_at"],
    )
