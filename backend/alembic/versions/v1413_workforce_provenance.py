"""Add Internal Manager attribution to workforce proposals.

Revision ID: v1413workforceprovenance
Revises: v1412workforcedelegations
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v1413workforceprovenance"
down_revision = "v1412workforcedelegations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_workforce_proposals",
        sa.Column(
            "source_type",
            sa.String(length=32),
            nullable=False,
            server_default="human",
        ),
    )
    op.add_column(
        "agent_workforce_proposals",
        sa.Column("manager_operation", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "agent_workforce_proposals",
        sa.Column(
            "proposed_by_agent_instance_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_instances.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "agent_workforce_proposals",
        sa.Column(
            "delegation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_delegations.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_agent_workforce_proposals_tenant_source",
        "agent_workforce_proposals",
        ["tenant_id", "source_type"],
    )
    op.create_index(
        "ix_agent_workforce_proposals_tenant_manager",
        "agent_workforce_proposals",
        ["tenant_id", "proposed_by_agent_instance_id"],
    )
    op.create_index(
        "ix_agent_workforce_proposals_tenant_delegation",
        "agent_workforce_proposals",
        ["tenant_id", "delegation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_workforce_proposals_tenant_delegation",
        table_name="agent_workforce_proposals",
    )
    op.drop_index(
        "ix_agent_workforce_proposals_tenant_manager",
        table_name="agent_workforce_proposals",
    )
    op.drop_index(
        "ix_agent_workforce_proposals_tenant_source",
        table_name="agent_workforce_proposals",
    )
    op.drop_column("agent_workforce_proposals", "delegation_id")
    op.drop_column("agent_workforce_proposals", "manager_operation")
    op.drop_column("agent_workforce_proposals", "proposed_by_agent_instance_id")
    op.drop_column("agent_workforce_proposals", "source_type")
