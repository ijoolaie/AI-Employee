"""RC5 Shopify OAuth/webhooks and subscription trial metadata."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "fe5f6a7b8c90"
down_revision = "fd4e5f6a7b89"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("subscriptions", sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table("shopify_webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("commerce_integrations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("webhook_id", sa.String(255), nullable=False),
        sa.Column("topic", sa.String(120), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="received"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("integration_id", "webhook_id", name="uq_shopify_webhook_delivery"))
    op.create_index("ix_shopify_webhook_events_tenant", "shopify_webhook_events", ["tenant_id"])

def downgrade():
    op.drop_index("ix_shopify_webhook_events_tenant", table_name="shopify_webhook_events")
    op.drop_table("shopify_webhook_events")
    op.drop_column("subscriptions", "trial_ends_at")
