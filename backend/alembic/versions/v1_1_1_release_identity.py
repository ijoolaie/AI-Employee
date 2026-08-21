"""Align the vendor-root tenant identity with the v1.1.1 release line.

This is a data correction migration. The earlier edition-boundaries migration
intentionally remains immutable and seeded the historical v1.0.1 identity.
"""
from alembic import op
import sqlalchemy as sa

revision = "v111releaseidentity"
down_revision = "rc9merge01"
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
              AND vendor_release_tag = 'v1.0.1'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE tenants
            SET vendor_release_tag = 'v1.0.1',
                delivery_revision = 'v1.0.1'
            WHERE tenant_kind = 'vendor'
              AND vendor_release_tag = 'v1.1.1'
            """
        )
    )
