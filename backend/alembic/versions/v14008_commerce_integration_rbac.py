"""Add tenant RBAC for commerce integration lifecycle.

Revision ID: v14008commerce
Revises: v14007refundauth
"""
from alembic import op
import sqlalchemy as sa

revision = "v14008commerce"
down_revision = "v14007refundauth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO permissions (id, code, description)
            VALUES (
                gen_random_uuid(),
                'commerce.integration.manage',
                'Manage tenant commerce integrations and provider synchronization'
            )
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
              AND p.code = 'commerce.integration.manage'
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
                SELECT id FROM permissions WHERE code = 'commerce.integration.manage'
            )
            """
        )
    )
    op.execute(sa.text("DELETE FROM permissions WHERE code = 'commerce.integration.manage'"))
