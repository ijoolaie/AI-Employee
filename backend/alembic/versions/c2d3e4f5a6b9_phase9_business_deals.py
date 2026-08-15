"""phase9 business deals

Revision ID: c2d3e4f5a6b9
Revises: b1c2d3e4f5a8
Create Date: 2026-08-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c2d3e4f5a6b9"
down_revision: Union[str, None] = "b1c2d3e4f5a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "business_deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_email", sa.String(320), nullable=True),
        sa.Column("stage", sa.String(32), nullable=False, server_default="lead"),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="IRR"),
        sa.Column("probability", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("expected_close_date", sa.Date(), nullable=True),
        sa.Column("owner_name", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("business_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_business_deals_tenant_id", "business_deals", ["tenant_id"])
    op.create_index("ix_business_deals_tenant_stage", "business_deals", ["tenant_id", "stage"])


def downgrade() -> None:
    op.drop_index("ix_business_deals_tenant_stage", table_name="business_deals")
    op.drop_index("ix_business_deals_tenant_id", table_name="business_deals")
    op.drop_table("business_deals")
