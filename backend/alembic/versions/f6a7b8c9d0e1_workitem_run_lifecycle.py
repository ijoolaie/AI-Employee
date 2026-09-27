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
        "work_items",
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "uq_work_items_run_id",
        "work_items",
        ["run_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_work_items_run_id", table_name="work_items")
    op.drop_column("work_items", "run_id")
