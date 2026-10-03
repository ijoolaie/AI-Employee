"""Merge the Workforce revenue and delegation migration heads.

Revision ID: w12_merge_revenue_delegation
Revises: w10workforcerevenue, v1415agentdelegationrun
"""
revision = "w12_merge_revenue_delegation"
down_revision = ("w10workforcerevenue", "v1415agentdelegationrun")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
