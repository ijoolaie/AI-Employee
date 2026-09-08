"""Create durable Agent-to-Agent delegation authority.

Revision ID: p1cagentdelegation
Revises: p0eimmutableaudit
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p1cagentdelegation"
down_revision = "p0eimmutableaudit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_delegations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delegator_agent_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delegate_agent_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_work_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delegated_work_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("chain_depth", sa.Integer(), nullable=False),
        sa.Column("max_chain_depth", sa.Integer(), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["delegator_agent_instance_id"], ["agent_instances.id"]),
        sa.ForeignKeyConstraint(["delegate_agent_instance_id"], ["agent_instances.id"]),
        sa.ForeignKeyConstraint(["source_work_item_id"], ["work_items.id"]),
        sa.ForeignKeyConstraint(["delegated_work_item_id"], ["work_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_delegations_tenant_status", "agent_delegations", ["tenant_id", "status"])
    op.create_index("ix_agent_delegations_target", "agent_delegations", ["tenant_id", "delegate_agent_instance_id"])
    op.create_index("ix_agent_delegations_source", "agent_delegations", ["tenant_id", "delegator_agent_instance_id"])
    op.create_index("ix_agent_delegations_correlation_id", "agent_delegations", ["correlation_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_delegations_correlation_id", table_name="agent_delegations")
    op.drop_index("ix_agent_delegations_source", table_name="agent_delegations")
    op.drop_index("ix_agent_delegations_target", table_name="agent_delegations")
    op.drop_index("ix_agent_delegations_tenant_status", table_name="agent_delegations")
    op.drop_table("agent_delegations")
