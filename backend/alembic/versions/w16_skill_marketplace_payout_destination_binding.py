"""Bind marketplace payout proposals to an immutable seller destination snapshot."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w16_skill_mkt_payout_destination_binding"
down_revision = "w16_skill_mkt_payout_destination"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("destination_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("destination_provider", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("destination_ref", sa.String(length=255), nullable=True),
    )
    op.create_foreign_key(
        "fk_skill_marketplace_payout_proposal_destination",
        "skill_marketplace_payout_proposals",
        "skill_marketplace_payout_destinations",
        ["destination_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_skill_marketplace_payout_proposal_destination",
        "skill_marketplace_payout_proposals",
        type_="foreignkey",
    )
    op.drop_column("skill_marketplace_payout_proposals", "destination_ref")
    op.drop_column("skill_marketplace_payout_proposals", "destination_provider")
    op.drop_column("skill_marketplace_payout_proposals", "destination_id")
