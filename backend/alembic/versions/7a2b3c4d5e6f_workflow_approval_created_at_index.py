"""Align workflow approval created_at index with the SQLAlchemy model.

Revision ID: 7a2b3c4d5e6f
Revises: 61661b7e79f8
"""
from alembic import op

revision = "7a2b3c4d5e6f"
down_revision = "61661b7e79f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_workflow_approvals_created_at",
        "workflow_approvals",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workflow_approvals_created_at",
        table_name="workflow_approvals",
    )
