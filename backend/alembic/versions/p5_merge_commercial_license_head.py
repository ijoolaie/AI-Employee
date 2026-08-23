"""Merge Phase 5 commercial license head with the current release head.

This migration is intentionally empty. It only reconciles the Alembic graph
so the repository has one unambiguous migration head.
"""

revision = "p5merge01"
down_revision = ("p5license01", "rc9merge04")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
