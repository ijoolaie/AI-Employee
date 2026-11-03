"""Backfill least-privilege action grants for existing root Vendor admins.

Revision ID: w29_vendor_admin_perms
Revises: w28_customer_slot_expiry_index

Only tenant-local Admin/Owner roles already assigned to an explicitly marked
platform administrator in a root Vendor tenant are eligible. This does not
grant permissions to arbitrary Vendor users or child tenants.
"""

from alembic import op
import sqlalchemy as sa

revision = "w29_vendor_admin_perms"
down_revision = "w28_customer_slot_expiry_index"
branch_labels = None
depends_on = None

VENDOR_ADMIN_PERMISSIONS = (
    "vendor.tenant.read",
    "vendor.reseller.read",
    "vendor.reseller.create",
    "vendor.reseller.manage",
    "vendor.customer.read",
    "vendor.customer.create",
    "vendor.customer.manage",
)


def upgrade() -> None:
    bind = op.get_bind()
    for code in VENDOR_ADMIN_PERMISSIONS:
        bind.execute(
            sa.text(
                """
                INSERT INTO permissions (id, code, description)
                VALUES (gen_random_uuid(), :code, :description)
                ON CONFLICT (code) DO NOTHING
                """
            ),
            {"code": code, "description": f"Vendor control-plane permission: {code}"},
        )

    bind.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT DISTINCT r.id, p.id
            FROM roles AS r
            JOIN tenants AS t
              ON t.id = r.tenant_id
             AND t.tenant_kind = 'vendor'
             AND t.parent_tenant_id IS NULL
            JOIN user_roles AS ur ON ur.role_id = r.id
            JOIN users AS u
              ON u.id = ur.user_id
             AND u.tenant_id = t.id
             AND u.is_platform_admin IS TRUE
            CROSS JOIN permissions AS p
            WHERE lower(r.name) IN ('admin', 'owner', 'tenant_admin')
              AND p.code IN (
                  'vendor.tenant.read',
                  'vendor.reseller.read',
                  'vendor.reseller.create',
                  'vendor.reseller.manage',
                  'vendor.customer.read',
                  'vendor.customer.create',
                  'vendor.customer.manage'
              )
            ON CONFLICT (role_id, permission_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    # Grants are intentionally retained on downgrade. Removing role grants
    # could revoke permissions that were subsequently relied upon or curated.
    pass
