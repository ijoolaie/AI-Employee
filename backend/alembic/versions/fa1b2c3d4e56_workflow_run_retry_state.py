"""Add workflow-run retry state fields.

Revision ID: fa1b2c3d4e56
Revises: f9a0b1c2d345
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "fa1b2c3d4e56"
down_revision = "f9a0b1c2d345"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow_runs",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("last_error", postgresql.JSONB(), nullable=True),
    )
    op.create_index(
        "ix_workflow_runs_next_retry_at",
        "workflow_runs",
        ["next_retry_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_workflow_runs_next_retry_at", table_name="workflow_runs")
    op.drop_column("workflow_runs", "last_error")
    op.drop_column("workflow_runs", "next_retry_at")
