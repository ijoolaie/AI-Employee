"""Persist delegated actor provenance for asynchronous Workflow Runs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w35_workflow_delegated_context"
down_revision = "w34_run_delegated_actor_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow_runs",
        sa.Column(
            "actor_tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "workflow_runs",
        sa.Column(
            "portal_access_grant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("portal_access_grants.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_workflow_runs_actor_tenant_id", "workflow_runs", ["actor_tenant_id"])
    op.create_index("ix_workflow_runs_portal_access_grant_id", "workflow_runs", ["portal_access_grant_id"])


def downgrade() -> None:
    op.drop_index("ix_workflow_runs_portal_access_grant_id", table_name="workflow_runs")
    op.drop_index("ix_workflow_runs_actor_tenant_id", table_name="workflow_runs")
    op.drop_column("workflow_runs", "portal_access_grant_id")
    op.drop_column("workflow_runs", "actor_tenant_id")
