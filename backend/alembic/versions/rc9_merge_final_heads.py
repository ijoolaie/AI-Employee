"""Merge the remaining independent Alembic heads into one release head.

This migration is intentionally empty: the parent migrations already contain
all schema/data operations. It only reconciles the migration graph so fresh
installs and upgrades can target ``head`` unambiguously.

Revision ID: rc9merge03
Revises: rc9merge02, f5a6b7c8d901, c2d3e4f5a6b9
"""

revision = "rc9merge03"
down_revision = ("rc9merge02", "f5a6b7c8d901", "c2d3e4f5a6b9")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
