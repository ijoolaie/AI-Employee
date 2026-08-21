"""Merge the remaining RC8 and RC9 Alembic heads into one release head.

Revision ID: rc9merge04
Revises: rc8p0p5idx, rc9merge03
"""

from __future__ import annotations

revision = "rc9merge04"
down_revision = ("rc8p0p5idx", "rc9merge03")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
