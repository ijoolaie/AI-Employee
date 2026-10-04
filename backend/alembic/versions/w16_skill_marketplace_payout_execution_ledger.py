"""Extend W16 payout proposal ledger with explicit execution evidence states."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w16_skill_mkt_payout_execution"
down_revision = "w16_skill_mkt_payout_proposal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE skillmarketplacepayoutexecutionstatus ADD VALUE IF NOT EXISTS 'pending'")
    op.execute("ALTER TYPE skillmarketplacepayoutexecutionstatus ADD VALUE IF NOT EXISTS 'accepted'")
    op.execute("ALTER TYPE skillmarketplacepayoutexecutionstatus ADD VALUE IF NOT EXISTS 'failed'")
    op.execute("ALTER TYPE skillmarketplacepayoutexecutionstatus ADD VALUE IF NOT EXISTS 'unknown'")

    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("provider_payout_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("provider_event_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("failure_code", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("retryable", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("executed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("external_execution", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_unique_constraint(
        "uq_skill_marketplace_payout_proposal_idempotency_key",
        "skill_marketplace_payout_proposals",
        ["idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_skill_marketplace_payout_proposal_idempotency_key",
        "skill_marketplace_payout_proposals",
        type_="unique",
    )
    op.drop_column("skill_marketplace_payout_proposals", "external_execution")
    op.drop_column("skill_marketplace_payout_proposals", "executed")
    op.drop_column("skill_marketplace_payout_proposals", "retryable")
    op.drop_column("skill_marketplace_payout_proposals", "failure_code")
    op.drop_column("skill_marketplace_payout_proposals", "provider_event_id")
    op.drop_column("skill_marketplace_payout_proposals", "provider_payout_id")
    op.drop_column("skill_marketplace_payout_proposals", "idempotency_key")
