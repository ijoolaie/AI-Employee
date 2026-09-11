"""Add optimistic version fencing for parallel branch lease ownership.

Revision ID: f9a0b1c2d3e4
Revises: f8a9b0c1d2e3
"""
from alembic import op
import sqlalchemy as sa

revision = "f9a0b1c2d3e4"
down_revision = "f8a9b0c1d2e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow_parallel_branch_runs",
        sa.Column("execution_lease_version", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("workflow_parallel_branch_runs", "execution_lease_version")
