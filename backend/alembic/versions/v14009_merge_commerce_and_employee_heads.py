"""Merge commerce RBAC and employee-version migration heads.

Revision ID: v14009mergeheads
Revises: v14008commerce, p1hemployeesinglecurrent
"""

revision = "v14009mergeheads"
down_revision = ("v14008commerce", "p1hemployeesinglecurrent")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
