"""Enforce tenant-scoped business document number uniqueness.

Revision ID: d4e5f6a7b8c9
Revises: c7d8e9f0a1b2
"""

from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Do not silently rename historical documents. If legacy data already
    # contains duplicates, stop the migration with an actionable error.
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT tenant_id, number
                    FROM business_invoices
                    GROUP BY tenant_id, number
                    HAVING COUNT(*) > 1
                ) THEN
                    RAISE EXCEPTION
                        'Cannot add uq_business_invoices_tenant_number: duplicate tenant/number pairs exist';
                END IF;

                IF EXISTS (
                    SELECT tenant_id, number
                    FROM business_orders
                    GROUP BY tenant_id, number
                    HAVING COUNT(*) > 1
                ) THEN
                    RAISE EXCEPTION
                        'Cannot add uq_business_orders_tenant_number: duplicate tenant/number pairs exist';
                END IF;
            END $$;
            """
        )
    )
    op.create_unique_constraint(
        "uq_business_invoices_tenant_number",
        "business_invoices",
        ["tenant_id", "number"],
    )
    op.create_unique_constraint(
        "uq_business_orders_tenant_number",
        "business_orders",
        ["tenant_id", "number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_business_orders_tenant_number",
        "business_orders",
        type_="unique",
    )
    op.drop_constraint(
        "uq_business_invoices_tenant_number",
        "business_invoices",
        type_="unique",
    )
