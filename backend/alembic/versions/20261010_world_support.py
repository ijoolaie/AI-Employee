"""World Mode read-only vendor support diagnostics permission.

Revision ID: 20261010_world_support
Revises: 20261010_world_commerce
"""
from alembic import op
import sqlalchemy as sa

revision = "20261010_world_support"
down_revision = "20261010_world_commerce"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO permissions (id, code, description)
        VALUES (gen_random_uuid(), :code, :description)
        ON CONFLICT (code) DO NOTHING
    """).bindparams(
        code="world.support.view",
        description="View tenant-scoped World Mode diagnostics for support",
    ))
    op.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE lower(r.name) IN ('owner', 'admin', 'tenant_admin')
          AND p.code = 'world.support.view'
          AND NOT EXISTS (
              SELECT 1 FROM role_permissions rp
              WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DELETE FROM role_permissions
        WHERE permission_id IN (
            SELECT id FROM permissions WHERE code = 'world.support.view'
        )
    """))
    op.execute(sa.text("DELETE FROM permissions WHERE code = 'world.support.view'"))
