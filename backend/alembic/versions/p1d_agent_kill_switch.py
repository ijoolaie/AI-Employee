"""Create durable Agent emergency kill switches.

Revision ID: p1dagentkillswitch
Revises: p1cagentdelegation
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p1dagentkillswitch"
down_revision = "p1cagentdelegation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_kill_switches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_instance_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope", sa.Enum("global", "tenant", "agent", name="agentkillscope"), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("asserted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asserted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["agent_instance_id"], ["agent_instances.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["asserted_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_kill_switches_active_tenant", "agent_kill_switches", ["tenant_id", "active"])
    op.create_index("ix_agent_kill_switches_active_agent", "agent_kill_switches", ["agent_instance_id", "active"])
    op.create_index("ix_agent_kill_switches_active_scope", "agent_kill_switches", ["scope", "active"])
    op.create_index("uq_agent_kill_switch_global_active", "agent_kill_switches", ["scope"], unique=True, postgresql_where=sa.text("scope = 'global' AND active = true"))
    op.create_index("uq_agent_kill_switch_tenant_active", "agent_kill_switches", ["scope", "tenant_id"], unique=True, postgresql_where=sa.text("scope = 'tenant' AND active = true"))
    op.create_index("uq_agent_kill_switch_agent_active", "agent_kill_switches", ["scope", "tenant_id", "agent_instance_id"], unique=True, postgresql_where=sa.text("scope = 'agent' AND active = true"))
    op.execute(sa.text("INSERT INTO permissions (id, code, description) VALUES (gen_random_uuid(), 'agent.emergency_kill', 'Assert and revoke tenant or Agent emergency execution kill switches') ON CONFLICT (code) DO NOTHING"))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM permissions WHERE code = 'agent.emergency_kill'"))
    op.drop_index("uq_agent_kill_switch_agent_active", table_name="agent_kill_switches")
    op.drop_index("uq_agent_kill_switch_tenant_active", table_name="agent_kill_switches")
    op.drop_index("uq_agent_kill_switch_global_active", table_name="agent_kill_switches")
    op.drop_index("ix_agent_kill_switches_active_scope", table_name="agent_kill_switches")
    op.drop_index("ix_agent_kill_switches_active_agent", table_name="agent_kill_switches")
    op.drop_index("ix_agent_kill_switches_active_tenant", table_name="agent_kill_switches")
    op.drop_table("agent_kill_switches")
    op.execute(sa.text("DROP TYPE IF EXISTS agentkillscope"))
