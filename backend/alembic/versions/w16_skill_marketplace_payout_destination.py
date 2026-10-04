"""Add tenant-scoped seller payout destination bindings."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w16_skill_mkt_payout_destination"
down_revision = "w16_skill_mkt_payout_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    destination_enum = postgresql.ENUM(
        "active", "revoked",
        name="skillmarketplacepayoutdestinationstatus",
        create_type=False,
    )
    destination_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "skill_marketplace_payout_destinations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("seller_tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("destination_ref", sa.String(length=255), nullable=False),
        sa.Column("status", destination_enum, nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revoked_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["seller_tenant_id"], ["tenants.id"], name="fk_skill_marketplace_payout_destination_seller", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_skill_marketplace_payout_destination_created_by", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["users.id"], name="fk_skill_marketplace_payout_destination_revoked_by", ondelete="RESTRICT"),
    )
    op.create_index(
        "uq_skill_marketplace_payout_destination_active_seller",
        "skill_marketplace_payout_destinations",
        ["seller_tenant_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_skill_marketplace_payout_destinations_seller",
        "skill_marketplace_payout_destinations",
        ["seller_tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_skill_marketplace_payout_destinations_seller", table_name="skill_marketplace_payout_destinations")
    op.drop_index("uq_skill_marketplace_payout_destination_active_seller", table_name="skill_marketplace_payout_destinations")
    op.drop_table("skill_marketplace_payout_destinations")
    postgresql.ENUM(name="skillmarketplacepayoutdestinationstatus").drop(op.get_bind(), checkfirst=True)
