"""Add W16 platform-admin marketplace payout proposal ledger."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w16_skill_mkt_payout_proposal"
down_revision = "w16_skill_mkt_settlement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    proposal_enum = postgresql.ENUM(
        "proposed", "cancelled",
        name="skillmarketplacepayoutproposalstatus",
        create_type=False,
    )
    proposal_enum.create(op.get_bind(), checkfirst=True)
    execution_enum = postgresql.ENUM(
        "not_executed",
        name="skillmarketplacepayoutexecutionstatus",
        create_type=False,
    )
    execution_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "skill_marketplace_payout_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("settlement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_admin_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="none"),
        sa.Column("status", proposal_enum, nullable=False, server_default="proposed"),
        sa.Column("execution_status", execution_enum, nullable=False, server_default="not_executed"),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["settlement_id"], ["skill_marketplace_settlements.id"],
            name="fk_skill_marketplace_payout_proposal_settlement",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seller_tenant_id"], ["tenants.id"],
            name="fk_skill_marketplace_payout_proposal_seller",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["platform_admin_tenant_id"], ["tenants.id"],
            name="fk_skill_marketplace_payout_proposal_platform_admin",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"],
            name="fk_skill_marketplace_payout_proposal_user",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "settlement_id",
            name="uq_skill_marketplace_payout_proposal_settlement",
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="ck_skill_marketplace_payout_proposal_amount_positive",
        ),
        sa.CheckConstraint(
            "provider = 'none'",
            name="ck_skill_marketplace_payout_proposal_provider_none",
        ),
        sa.CheckConstraint(
            "execution_status = 'not_executed'",
            name="ck_skill_marketplace_payout_proposal_not_executed",
        ),
    )
    op.create_index(
        "ix_skill_marketplace_payout_proposals_seller",
        "skill_marketplace_payout_proposals", ["seller_tenant_id"],
    )
    op.create_index(
        "ix_skill_marketplace_payout_proposals_status",
        "skill_marketplace_payout_proposals", ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_skill_marketplace_payout_proposals_status", table_name="skill_marketplace_payout_proposals")
    op.drop_index("ix_skill_marketplace_payout_proposals_seller", table_name="skill_marketplace_payout_proposals")
    op.drop_table("skill_marketplace_payout_proposals")
    postgresql.ENUM(name="skillmarketplacepayoutexecutionstatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="skillmarketplacepayoutproposalstatus").drop(op.get_bind(), checkfirst=True)
