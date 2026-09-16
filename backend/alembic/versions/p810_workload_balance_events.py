"""Persist Stage 9 workload balancing recommendation evidence.

Revision ID: p810workloadbalance
Revises: p809agentwfreplace
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p810workloadbalance"
down_revision = "p809agentwfreplace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workload_balance_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_agent_instance_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ready_items", sa.Integer(), nullable=False),
        sa.Column("oldest_ready_age_seconds", sa.Float(), nullable=False),
        sa.Column("total_available_slots", sa.Integer(), nullable=False),
        sa.Column("queue_pressure", sa.Float(), nullable=False),
        sa.Column("candidates_considered", sa.Integer(), nullable=False),
        sa.Column("rationale", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("contract_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["target_agent_instance_id"], ["agent_instances.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workload_balance_events_tenant_created", "workload_balance_events", ["tenant_id", "created_at"])
    op.create_index("ix_workload_balance_events_tenant_target", "workload_balance_events", ["tenant_id", "target_agent_instance_id"])


def downgrade() -> None:
    op.drop_index("ix_workload_balance_events_tenant_target", table_name="workload_balance_events")
    op.drop_index("ix_workload_balance_events_tenant_created", table_name="workload_balance_events")
    op.drop_table("workload_balance_events")
