"""Add product update RBAC permission.

Revision ID: customerproductlifecycle01
Revises: p12_06_test_definition_scope
"""
from alembic import op
import sqlalchemy as sa

revision = "customerproductlifecycle01"
down_revision = "p12_06_test_definition_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO permissions (id, code, description)
        VALUES (gen_random_uuid(), 'products.update', 'Update and activate/deactivate tenant business products')
        ON CONFLICT (code) DO NOTHING
    """))
    op.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE lower(r.name) IN ('owner', 'admin', 'tenant_admin')
          AND p.code = 'products.update'
          AND NOT EXISTS (
              SELECT 1 FROM role_permissions rp
              WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code = 'products.update')
    """))
    op.execute(sa.text("DELETE FROM permissions WHERE code = 'products.update'"))
