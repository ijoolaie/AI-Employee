"""remove stale tenant indexes"""

from alembic import op

revision = "rc8p0p5idx"
down_revision = "rc8p0p4pwd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "ix_onboarding_progress_tenant_id",
        table_name="onboarding_progress",
    )
    op.drop_index(
        "ix_shopify_webhook_events_tenant",
        table_name="shopify_webhook_events",
    )


def downgrade() -> None:
    op.create_index(
        "ix_shopify_webhook_events_tenant",
        "shopify_webhook_events",
        ["tenant_id"],
    )
    op.create_index(
        "ix_onboarding_progress_tenant_id",
        "onboarding_progress",
        ["tenant_id"],
        unique=True,
    )