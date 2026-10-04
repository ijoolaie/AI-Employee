"""Allow governed W16 payout execution beyond proposal state."""

from alembic import op

revision = "w16_payout_exec_state"
down_revision = "w16_payout_dest_bind"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_skill_marketplace_payout_proposal_not_executed",
        "skill_marketplace_payout_proposals",
        type_="check",
    )
    op.create_check_constraint(
        "ck_skill_marketplace_payout_proposal_execution_consistency",
        "skill_marketplace_payout_proposals",
        "(execution_status = 'not_executed' AND executed = false AND external_execution = false)"
        " OR execution_status = 'pending'"
        " OR execution_status = 'accepted'"
        " OR execution_status = 'failed'"
        " OR execution_status = 'unknown'",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_skill_marketplace_payout_proposal_execution_consistency",
        "skill_marketplace_payout_proposals",
        type_="check",
    )
    op.create_check_constraint(
        "ck_skill_marketplace_payout_proposal_not_executed",
        "skill_marketplace_payout_proposals",
        "execution_status = 'not_executed'",
    )
