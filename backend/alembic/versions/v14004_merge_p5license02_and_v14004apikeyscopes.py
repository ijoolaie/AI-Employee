"""Merge the existing migration heads for V1.4-004.

Revision ID: v14004merge
Revises: p5license02, v14004apikeyscopes
Create Date: 2026-08-26
"""
from alembic import op

revision = "v14004merge"
down_revision = ("p5license02", "v14004apikeyscopes")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
