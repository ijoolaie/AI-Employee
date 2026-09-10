"""Enforce one current EmployeeVersion per Employee.

Revision ID: p1hemployeesinglecurrent
Revises: p1gteaminstallnull
"""
from alembic import op
import sqlalchemy as sa

revision = "p1hemployeesinglecurrent"
down_revision = "p1gteaminstallnull"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The application contract requires at most one current version per
    # employee. Make that invariant database-enforced under concurrency.
    op.create_index(
        "uq_employee_single_current_version",
        "employee_versions",
        ["employee_id"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_employee_single_current_version",
        table_name="employee_versions",
    )
