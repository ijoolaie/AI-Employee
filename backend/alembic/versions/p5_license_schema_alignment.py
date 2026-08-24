"""Align the commercial license schema with the SQLAlchemy model.

Revision ID: p5license02
Revises: p5merge01
"""
from alembic import op

revision = "p5license02"
down_revision = "p5merge01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_commercial_licenses_status",
        "commercial_licenses",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_commercial_licenses_status",
        table_name="commercial_licenses",
    )
