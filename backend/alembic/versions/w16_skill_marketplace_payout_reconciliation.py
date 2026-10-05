"""Persist explicit manual reconciliation provenance for UNKNOWN payouts."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "w16_payout_reconcile"
down_revision = "w16_payout_exec_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("reconciliation_evidence_ref", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("reconciliation_outcome", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column(
            "reconciled_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_skill_marketplace_payout_proposal_reconciliation_outcome",
        "skill_marketplace_payout_proposals",
        "(reconciliation_outcome IS NULL AND reconciliation_evidence_ref IS NULL AND reconciled_by_user_id IS NULL AND reconciled_at IS NULL)"
        " OR (reconciliation_outcome IN ('accepted', 'failed', 'unknown') AND reconciliation_evidence_ref IS NOT NULL AND reconciled_by_user_id IS NOT NULL AND reconciled_at IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_skill_marketplace_payout_proposal_reconciliation_outcome",
        "skill_marketplace_payout_proposals",
        type_="check",
    )
    op.drop_column("skill_marketplace_payout_proposals", "reconciled_at")
    op.drop_column("skill_marketplace_payout_proposals", "reconciled_by_user_id")
    op.drop_column("skill_marketplace_payout_proposals", "reconciliation_outcome")
    op.drop_column("skill_marketplace_payout_proposals", "reconciliation_evidence_ref")
