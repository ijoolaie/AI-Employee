"""Add durable tool side-effect execution fences.

Revision ID: c7d8e9f0a1b2
Revises: agentdelegationrbac
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c7d8e9f0a1b2"
down_revision = "agentdelegationrbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tool_execution_fences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_call_id", sa.String(length=150), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "run_id",
            "tool_call_id",
            name="uq_tool_execution_fence_identity",
        ),
    )
    op.create_index("ix_tool_execution_fences_tenant_id", "tool_execution_fences", ["tenant_id"])
    op.create_index("ix_tool_execution_fences_run_id", "tool_execution_fences", ["run_id"])
    op.create_index("ix_tool_execution_fences_status", "tool_execution_fences", ["status"])


def downgrade() -> None:
    op.drop_index("ix_tool_execution_fences_status", table_name="tool_execution_fences")
    op.drop_index("ix_tool_execution_fences_run_id", table_name="tool_execution_fences")
    op.drop_index("ix_tool_execution_fences_tenant_id", table_name="tool_execution_fences")
    op.drop_table("tool_execution_fences")
