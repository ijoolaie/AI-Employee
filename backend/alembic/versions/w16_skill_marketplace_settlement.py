"""Add W16 marketplace financial allocation ledger."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w16_skill_mkt_settlement"
down_revision = "w16_skill_mkt_cross_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    settlement_enum = postgresql.ENUM(
        "recorded",
        name="skillmarketplacesettlementstatus",
        create_type=False,
    )
    settlement_enum.create(op.get_bind(), checkfirst=True)
    payout_enum = postgresql.ENUM(
        "not_executed",
        name="skillmarketplacepayoutstatus",
        create_type=False,
    )
    payout_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "skill_marketplace_settlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revenue_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("gross_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("platform_fee_bps", sa.Integer(), nullable=False),
        sa.Column("platform_fee_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("seller_net_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("status", settlement_enum, nullable=False, server_default="recorded"),
        sa.Column("payout_status", payout_enum, nullable=False, server_default="not_executed"),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["purchase_id"], ["skill_marketplace_purchases.id"],
            name="fk_skill_marketplace_settlement_purchase",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["revenue_event_id"], ["workforce_revenue_events.id"],
            name="fk_skill_marketplace_settlement_revenue",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["buyer_tenant_id"], ["tenants.id"],
            name="fk_skill_marketplace_settlement_buyer",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seller_tenant_id"], ["tenants.id"],
            name="fk_skill_marketplace_settlement_seller",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "purchase_id",
            name="uq_skill_marketplace_settlement_purchase",
        ),
        sa.UniqueConstraint(
            "provider", "provider_event_id",
            name="uq_skill_marketplace_settlement_provider_event",
        ),
    )
    op.create_index(
        "ix_skill_marketplace_settlements_buyer",
        "skill_marketplace_settlements", ["buyer_tenant_id"],
    )
    op.create_index(
        "ix_skill_marketplace_settlements_seller",
        "skill_marketplace_settlements", ["seller_tenant_id"],
    )
    op.create_index(
        "ix_skill_marketplace_settlements_status",
        "skill_marketplace_settlements", ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_skill_marketplace_settlements_status", table_name="skill_marketplace_settlements")
    op.drop_index("ix_skill_marketplace_settlements_seller", table_name="skill_marketplace_settlements")
    op.drop_index("ix_skill_marketplace_settlements_buyer", table_name="skill_marketplace_settlements")
    op.drop_table("skill_marketplace_settlements")
    postgresql.ENUM(name="skillmarketplacepayoutstatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="skillmarketplacesettlementstatus").drop(op.get_bind(), checkfirst=True)
