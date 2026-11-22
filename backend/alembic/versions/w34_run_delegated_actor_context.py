"""Persist delegated actor provenance for asynchronous Runs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w34_run_delegated_actor_context"
down_revision = "w33_tenant_action_grants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "runs",
        sa.Column(
            "actor_tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "runs",
        sa.Column(
            "portal_access_grant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("portal_access_grants.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_runs_actor_tenant_id", "runs", ["actor_tenant_id"])
    op.create_index("ix_runs_portal_access_grant_id", "runs", ["portal_access_grant_id"])


def downgrade() -> None:
    op.drop_index("ix_runs_portal_access_grant_id", table_name="runs")
    op.drop_index("ix_runs_actor_tenant_id", table_name="runs")
    op.drop_column("runs", "portal_access_grant_id")
    op.drop_column("runs", "actor_tenant_id")
