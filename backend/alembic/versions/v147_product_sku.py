"""Harden tenant-scoped product SKU uniqueness and normalization.

Revision ID: v147productsku
Revises: v14013billingmanagementrbac
"""
from alembic import op
import sqlalchemy as sa


revision = "v147productsku"
down_revision = "v14013billingmanagementrbac"
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
    op.create_index(
        INDEX_NAME,
        "products",
        ["tenant_id", sa.text("lower(btrim(sku))")],
        unique=True,
        postgresql_where=sa.text("sku IS NOT NULL AND btrim(sku) <> ''"),
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="products")
