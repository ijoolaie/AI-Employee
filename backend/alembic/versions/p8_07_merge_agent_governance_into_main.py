"""Merge the Stage 8 governance branch into the current migration line.

Revision ID: p8_07_gov_merge
Revises: p13_06_marketplace_import, p8_05_agent_gov
"""

revision = "p8_07_gov_merge"
down_revision = ("p13_06_marketplace_import", "p8_05_agent_gov")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
