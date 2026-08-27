"""Authorize and audit the V1.4 refund/reversal lifecycle.

Revision ID: v14007refundauth
Revises: v14006refund
"""
from alembic import op
import sqlalchemy as sa

revision = "v14007refundauth"
down_revision = "v14006refund"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO permissions (id, code, description)
            VALUES (gen_random_uuid(), 'billing.refund', 'Request tenant-scoped refunds and payment reversals')
            ON CONFLICT (code) DO NOTHING
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE lower(r.name) IN ('owner', 'admin', 'tenant_admin')
              AND p.code = 'billing.refund'
              AND NOT EXISTS (
                  SELECT 1
                  FROM role_permissions rp
                  WHERE rp.role_id = r.id
                    AND rp.permission_id = p.id
              )
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id IN (
                SELECT id FROM permissions WHERE code = 'billing.refund'
            )
            """
        )
    )
    op.execute(sa.text("DELETE FROM permissions WHERE code = 'billing.refund'"))
