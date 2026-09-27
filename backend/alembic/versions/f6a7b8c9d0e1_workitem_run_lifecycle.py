"""Bind canonical Agent WorkItems to their Run lifecycle.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "runs",
        sa.Column(
            "work_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("work_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_runs_work_item_id",
        "runs",
        ["work_item_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_runs_work_item_id", table_name="runs")
    op.drop_column("runs", "work_item_id")
