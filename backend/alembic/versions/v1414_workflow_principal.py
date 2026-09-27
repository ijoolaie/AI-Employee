"""Persist optional AgentInstance provenance on WorkflowRun.

Revision ID: v1414workflowprincipal
Revises: f6a7b8c9d0e1, v1413workforceprovenance
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "v1414workflowprincipal"
down_revision = ("f6a7b8c9d0e1", "v1413workforceprovenance")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow_runs",
        sa.Column(
            "agent_instance_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_instances.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_workflow_runs_agent_instance_id",
        "workflow_runs",
        ["agent_instance_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_workflow_runs_agent_instance_id", table_name="workflow_runs")
    op.drop_column("workflow_runs", "agent_instance_id")
