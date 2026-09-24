"""Add explicit tenant RBAC for creating CRM customers.

Revision ID: customercustomelifecycle
Revises: rc9merge03
"""
from alembic import op
import sqlalchemy as sa

revision = "customercustomerlifecycle"
down_revision = "rc9merge03"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("customers.create", "Create tenant business customers"),
)


def upgrade() -> None:
    for code, description in PERMISSIONS:
        op.execute(
            sa.text(
                """
                INSERT INTO permissions (id, code, description)
                VALUES (gen_random_uuid(), :code, :description)
                ON CONFLICT (code) DO NOTHING
                """
            ).bindparams(code=code, description=description)
        )
    op.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE lower(r.name) IN ('owner', 'admin', 'tenant_admin')
              AND p.code = 'customers.create'
              AND NOT EXISTS (
                  SELECT 1 FROM role_permissions rp
                  WHERE rp.role_id = r.id AND rp.permission_id = p.id
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
                SELECT id FROM permissions WHERE code = 'customers.create'
            )
            """
        )
    )
    op.execute(sa.text("DELETE FROM permissions WHERE code = 'customers.create'"))
