"""Create the governed AI Workforce revenue outcome ledger.

Revision ID: w10workforcerevenue
Revises: v1414workflowprincipal
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w10workforcerevenue"
down_revision = "v1414workflowprincipal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workforce_revenue_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["business_deals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["business_orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "provider_event_id",
            name="uq_workforce_revenue_event_provider_id",
        ),
    )
    op.create_index("ix_workforce_revenue_event_tenant", "workforce_revenue_events", ["tenant_id"])
    op.create_index("ix_workforce_revenue_event_deal", "workforce_revenue_events", ["deal_id"])


def downgrade() -> None:
    op.drop_index("ix_workforce_revenue_event_deal", table_name="workforce_revenue_events")
    op.drop_index("ix_workforce_revenue_event_tenant", table_name="workforce_revenue_events")
    op.drop_table("workforce_revenue_events")
