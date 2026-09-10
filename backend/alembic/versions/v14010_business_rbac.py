"""Add tenant RBAC for business orders and sales APIs.

Revision ID: v14010businessrbac
Revises: v14009mergeheads
"""
from alembic import op
import sqlalchemy as sa

revision = "v14010businessrbac"
down_revision = "v14009mergeheads"
branch_labels = None
depends_on = None

CODES = (
    "orders.read", "orders.create", "orders.update", "orders.invoice_link",
    "sales.read", "sales.create", "sales.update",
)
CODE_SQL = ", ".join(f"'{code}'" for code in CODES)


def upgrade() -> None:
    for code, description in (
        ("orders.read", "Read tenant business orders"),
        ("orders.create", "Create tenant business orders"),
        ("orders.update", "Update tenant business order status"),
        ("orders.invoice_link", "Link invoices to tenant business orders"),
        ("sales.read", "Read tenant sales deals and forecasts"),
        ("sales.create", "Create tenant sales deals"),
        ("sales.update", "Update tenant sales deal stages"),
    ):
        op.execute(sa.text("""
            INSERT INTO permissions (id, code, description)
            VALUES (gen_random_uuid(), :code, :description)
            ON CONFLICT (code) DO NOTHING
        """).bindparams(code=code, description=description))

    op.execute(sa.text(f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE lower(r.name) IN ('owner', 'admin', 'tenant_admin')
          AND p.code IN ({CODE_SQL})
          AND NOT EXISTS (
              SELECT 1 FROM role_permissions rp
              WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
    """))


def downgrade() -> None:
    op.execute(sa.text(f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (
            SELECT id FROM permissions WHERE code IN ({CODE_SQL})
        )
    """))
    op.execute(sa.text(f"DELETE FROM permissions WHERE code IN ({CODE_SQL})"))
