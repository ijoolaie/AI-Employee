"""Prevent multiple Shopify stores per tenant while catalog identity is tenant-global.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""

from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing Shopify rows cannot be merged safely because synced customer,
    # product and order identities currently have no integration_id. Fail closed
    # instead of silently selecting one store as the surviving identity.
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT tenant_id
                    FROM commerce_integrations
                    WHERE provider = 'shopify'
                    GROUP BY tenant_id
                    HAVING COUNT(*) > 1
                ) THEN
                    RAISE EXCEPTION
                        'Cannot add uq_commerce_integrations_tenant_shopify: multiple Shopify integrations exist for one or more tenants';
                END IF;
            END $$;
            """
        )
    )
    op.create_index(
        "uq_commerce_integrations_tenant_shopify",
        "commerce_integrations",
        ["tenant_id"],
        unique=True,
        postgresql_where=sa.text("provider = 'shopify'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_commerce_integrations_tenant_shopify",
        table_name="commerce_integrations",
    )
