"""Persist Agent delegation provenance on canonical Runs."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v1415agentdelegationrun"
down_revision = "merge_workforce_customer_rc9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "runs",
        sa.Column(
            "delegation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_delegations.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.create_index("ix_runs_delegation_id", "runs", ["delegation_id"])


def downgrade() -> None:
    op.drop_index("ix_runs_delegation_id", table_name="runs")
    op.drop_column("runs", "delegation_id")
