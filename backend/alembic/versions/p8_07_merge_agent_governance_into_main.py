"""Merge the Stage 8 governance branch into the current migration line.

Revision ID: p8_07_merge_agent_governance_into_main
Revises: p13_06_marketplace_import, p8_05_agent_governance_enforcement
"""

revision = "p8_07_merge_agent_governance_into_main"
down_revision = ("p13_06_marketplace_import", "p8_05_agent_governance_enforcement")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
