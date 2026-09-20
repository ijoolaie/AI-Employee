"""Harden tenant-scoped product SKU uniqueness and normalization.

Revision ID: v147productsku
Revises: v14013billingmanagementrbac
"""
from alembic import op
import sqlalchemy as sa


revision = "v147productsku"
down_revision = "p810workloadbalance"
branch_labels = None
depends_on = None


INDEX_NAME = "uq_products_tenant_normalized_sku"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE products
            SET sku = NULL
            WHERE sku IS NOT NULL
              AND btrim(sku) = ''
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE products
            SET sku = upper(btrim(sku))
            WHERE sku IS NOT NULL
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            CREATE UNIQUE INDEX {INDEX_NAME}
            ON products (tenant_id, lower(btrim(sku)))
            WHERE sku IS NOT NULL AND btrim(sku) <> ''
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text(f"DROP INDEX IF EXISTS {INDEX_NAME}"))
