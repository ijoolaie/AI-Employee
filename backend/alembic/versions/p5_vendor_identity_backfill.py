"""Backfill v1.1.1 release identity for existing vendor tenants.

Revision ID: p5vendoridentity01
Revises: p5license02
"""
from alembic import op
import sqlalchemy as sa

revision = "p5vendoridentity01"
down_revision = "p5license02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE tenants
            SET vendor_release_tag = 'v1.1.1',
                delivery_revision = 'v1.1.1'
            WHERE tenant_kind = 'vendor'
              AND (
                  vendor_release_tag IS NULL
                  OR vendor_release_tag = ''
                  OR delivery_revision IS NULL
                  OR delivery_revision = ''
              )
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE tenants
            SET vendor_release_tag = NULL,
                delivery_revision = NULL
            WHERE tenant_kind = 'vendor'
              AND vendor_release_tag = 'v1.1.1'
              AND delivery_revision = 'v1.1.1'
            """
        )
    )
