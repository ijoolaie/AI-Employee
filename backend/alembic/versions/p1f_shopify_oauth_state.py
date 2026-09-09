"""Persist Shopify OAuth state for replay prevention and shop binding.

Revision ID: p1fshopifyoauthstate
Revises: p1ecredentialboundary
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "p1fshopifyoauthstate"
down_revision = "p1ecredentialboundary"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shopify_oauth_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column("shop_domain", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state_hash"),
    )
    op.create_index("ix_shopify_oauth_states_expires", "shopify_oauth_states", ["expires_at"])
    op.create_index("ix_shopify_oauth_states_tenant", "shopify_oauth_states", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_shopify_oauth_states_tenant", table_name="shopify_oauth_states")
    op.drop_index("ix_shopify_oauth_states_expires", table_name="shopify_oauth_states")
    op.drop_table("shopify_oauth_states")
