"""Merge all Phase 1 migration heads for v0.2.36.

Revision ID: f6b7c8d9e012
Revises: a1b2c3d4e507, d4f5a6b7c809, e4f5a6b7c809
"""
from alembic import op

revision = "f6b7c8d9e012"
down_revision = ("a1b2c3d4e507", "d4f5a6b7c809", "e4f5a6b7c809")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
