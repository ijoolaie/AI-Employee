"""Add tenant RBAC for customer, invoice, and product business APIs.

Revision ID: v14011businessentityrbac
Revises: v14010businessrbac
"""
from alembic import op
import sqlalchemy as sa

revision = "v14011businessentityrbac"
down_revision = "v14010businessrbac"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("customers.read", "Read tenant business customers"),
    ("customers.update", "Update tenant business customers"),
    ("invoices.read", "Read tenant business invoices"),
    ("invoices.create", "Create tenant business invoices"),
    ("invoices.update", "Update tenant business invoice status"),
    ("invoices.export_pdf", "Export tenant business invoices as PDF"),
    ("products.read", "Read tenant business products"),
    ("products.create", "Create tenant business products"),
    ("products.inventory_update", "Update tenant product inventory"),
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

    codes = ", ".join(f"'{code}'" for code, _ in PERMISSIONS)
    op.execute(
        sa.text(
            f"""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE lower(r.name) IN ('owner', 'admin', 'tenant_admin')
              AND p.code IN ({codes})
              AND NOT EXISTS (
                  SELECT 1 FROM role_permissions rp
                  WHERE rp.role_id = r.id AND rp.permission_id = p.id
              )
            """
        )
    )


def downgrade() -> None:
    codes = ", ".join(f"'{code}'" for code, _ in PERMISSIONS)
    op.execute(
        sa.text(
            f"""
            DELETE FROM role_permissions
            WHERE permission_id IN (
                SELECT id FROM permissions WHERE code IN ({codes})
            )
            """
        )
    )
    op.execute(sa.text(f"DELETE FROM permissions WHERE code IN ({codes})"))
