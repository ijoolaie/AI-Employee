"""Add governed marketplace payout execution state and approval ledger."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w16_skill_mkt_payout_exec"
down_revision = "w16_skill_mkt_payout_proposal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(
        "not_executed", "executed", "unknown",
        name="skillmarketplacepayoutexecutionstatus",
        create_type=False,
    ).create(bind, checkfirst=True)
    op.execute(
        "ALTER TYPE skillmarketplacepayoutexecutionstatus ADD VALUE IF NOT EXISTS 'executed'"
    )
    op.execute(
        "ALTER TYPE skillmarketplacepayoutexecutionstatus ADD VALUE IF NOT EXISTS 'unknown'"
    )
    approval_enum = postgresql.ENUM(
        "approved", "rejected",
        name="skillmarketplacepayoutapprovalstatus",
        create_type=False,
    )
    approval_enum.create(bind, checkfirst=True)
    op.execute(
        sa.text(
            "INSERT INTO permissions (id, code, description) VALUES "
            "(gen_random_uuid(), 'skill_marketplace.payout.approve', 'Core permission: skill_marketplace.payout.approve') "
            "ON CONFLICT (code) DO NOTHING"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO permissions (id, code, description) VALUES "
            "(gen_random_uuid(), 'skill_marketplace.payout.execute', 'Core permission: skill_marketplace.payout.execute') "
            "ON CONFLICT (code) DO NOTHING"
        )
    )

    op.drop_constraint(
        "ck_skill_marketplace_payout_proposal_provider_none",
        "skill_marketplace_payout_proposals",
        type_="check",
    )
    op.drop_constraint(
        "ck_skill_marketplace_payout_proposal_not_executed",
        "skill_marketplace_payout_proposals",
        type_="check",
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("provider_payout_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "skill_marketplace_payout_proposals",
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_skill_marketplace_payout_proposals_provider_payout_id",
        "skill_marketplace_payout_proposals",
        ["provider_payout_id"],
    )

    op.create_table(
        "skill_marketplace_payout_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_admin_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decided_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", approval_enum, nullable=False),
        sa.Column("reason", sa.String(length=2000), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["proposal_id"], ["skill_marketplace_payout_proposals.id"],
            name="fk_skill_marketplace_payout_approval_proposal",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["platform_admin_tenant_id"], ["tenants.id"],
            name="fk_skill_marketplace_payout_approval_admin_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["decided_by_user_id"], ["users.id"],
            name="fk_skill_marketplace_payout_approval_user",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "proposal_id",
            name="uq_skill_marketplace_payout_approval_proposal",
        ),
    )
    op.create_index(
        "ix_skill_marketplace_payout_approvals_admin",
        "skill_marketplace_payout_approvals",
        ["platform_admin_tenant_id"],
    )

