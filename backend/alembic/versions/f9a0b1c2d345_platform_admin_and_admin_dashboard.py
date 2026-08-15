"""platform admin flag for Phase 1 admin dashboard

Revision ID: f9a0b1c2d345
Revises: f8d9e0a1b234
"""
from alembic import op
import sqlalchemy as sa

revision = "f9a0b1c2d345"
down_revision = "f8d9e0a1b234"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_platform_admin", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("users", "is_platform_admin", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "is_platform_admin")
