"""PostgreSQL rehearsal for the legacy Vendor Admin permission backfill.

All fixture tables are TEMP tables on one isolated support_test connection and
the transaction is rolled back. No persistent tenant, role, user or permission
records are changed.
"""

import os
import uuid
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool


MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "w29_vendor_admin_action_permissions.py"
)
SPEC = spec_from_file_location("w29_vendor_admin_action_permissions_pg", MIGRATION_PATH)
assert SPEC is not None and SPEC.loader is not None
migration = module_from_spec(SPEC)
SPEC.loader.exec_module(migration)


def _dedicated_test_database_url() -> str:
    url = os.environ.get("SUPPORT_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("Test database URL is required; refusing to run.")
    parsed = make_url(url)
    if (
        parsed.drivername != "postgresql+asyncpg"
        or parsed.username not in {"support_test_user", "aiep"}
        or parsed.host not in {"127.0.0.1", "localhost"}
        or parsed.port not in {5432, 15433}
        or parsed.database != "support_test"
        or not parsed.password
    ):
        raise RuntimeError("URL must target the dedicated local support_test database; refusing to run.")
    return url


@pytest.mark.asyncio
async def test_vendor_admin_backfill_postgres_scope_and_idempotency():
    engine = create_async_engine(_dedicated_test_database_url(), poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()

            def exercise(sync_connection):
                for ddl in (
                    "CREATE TEMP TABLE tenants (id uuid PRIMARY KEY, tenant_kind text NOT NULL, parent_tenant_id uuid NULL)",
                    "CREATE TEMP TABLE users (id uuid PRIMARY KEY, tenant_id uuid NOT NULL, is_platform_admin boolean NOT NULL)",
                    "CREATE TEMP TABLE roles (id uuid PRIMARY KEY, tenant_id uuid NOT NULL, name text NOT NULL)",
                    "CREATE TEMP TABLE user_roles (user_id uuid NOT NULL, role_id uuid NOT NULL)",
                    "CREATE TEMP TABLE permissions (id uuid PRIMARY KEY, code text UNIQUE NOT NULL, description text NULL)",
                    "CREATE TEMP TABLE role_permissions (role_id uuid NOT NULL, permission_id uuid NOT NULL, PRIMARY KEY (role_id, permission_id))",
                ):
                    sync_connection.exec_driver_sql(ddl)

                vendor_a, vendor_b, reseller, customer = (uuid.uuid4() for _ in range(4))
                eligible_a, eligible_b = uuid.uuid4(), uuid.uuid4()
                shared_role, child_role, customer_role = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
                admin_a, ordinary_a, admin_b, admin_reseller, admin_customer = (
                    uuid.uuid4() for _ in range(5)
                )
                sync_connection.execute(
                    text(
                        "INSERT INTO tenants (id, tenant_kind, parent_tenant_id) "
                        "VALUES (:a, 'vendor', NULL), (:b, 'vendor', NULL), "
                        "(:r, 'reseller', :a), (:c, 'customer', :a)"
                    ),
                    {"a": vendor_a, "b": vendor_b, "r": reseller, "c": customer},
                )
                sync_connection.execute(
                    text(
                        "INSERT INTO users (id, tenant_id, is_platform_admin) VALUES "
                        "(:aa, :a, TRUE), (:oa, :a, FALSE), (:ab, :b, TRUE), "
                        "(:ar, :r, TRUE), (:ac, :c, TRUE)"
                    ),
                    {
                        "aa": admin_a, "oa": ordinary_a, "ab": admin_b,
                        "ar": admin_reseller, "ac": admin_customer,
                        "a": vendor_a, "b": vendor_b, "r": reseller, "c": customer,
                    },
                )
                sync_connection.execute(
                    text(
                        "INSERT INTO roles (id, tenant_id, name) VALUES "
                        "(:ea, :a, 'Admin'), (:eb, :b, 'Owner'), "
                        "(:shared, :a, 'Tenant_Admin'), (:child, :r, 'Admin'), "
                        "(:customer, :c, 'Admin')"
                    ),
                    {
                        "ea": eligible_a, "eb": eligible_b, "shared": shared_role,
                        "child": child_role, "customer": customer_role,
                        "a": vendor_a, "b": vendor_b, "r": reseller, "c": customer,
                    },
                )
                sync_connection.execute(
                    text(
                        "INSERT INTO user_roles (user_id, role_id) VALUES "
                        "(:aa, :ea), (:ab, :eb), (:aa, :shared), (:oa, :shared), "
                        "(:ar, :child), (:ac, :customer)"
                    ),
                    {
                        "aa": admin_a, "ab": admin_b, "oa": ordinary_a,
                        "ar": admin_reseller, "ac": admin_customer,
                        "ea": eligible_a, "eb": eligible_b, "shared": shared_role,
                        "child": child_role, "customer": customer_role,
                    },
                )
                preserved_permission_id = uuid.uuid4()
                sync_connection.execute(
                    text(
                        "INSERT INTO permissions (id, code, description) "
                        "VALUES (:id, 'vendor.tenant.read', 'custom description preserved')"
                    ),
                    {"id": preserved_permission_id},
                )

                with Operations.context(MigrationContext.configure(sync_connection)):
                    migration.upgrade()

                eligible_codes = set(
                    sync_connection.execute(
                        text(
                            "SELECT p.code FROM role_permissions rp "
                            "JOIN permissions p ON p.id = rp.permission_id "
                            "WHERE rp.role_id = :role_id"
                        ),
                        {"role_id": eligible_a},
                    ).scalars()
                )
                expected_codes = set(migration.VENDOR_ADMIN_PERMISSIONS)
                assert eligible_codes == expected_codes

                second_vendor_codes = set(
                    sync_connection.execute(
                        text(
                            "SELECT p.code FROM role_permissions rp "
                            "JOIN permissions p ON p.id = rp.permission_id "
                            "WHERE rp.role_id = :role_id"
                        ),
                        {"role_id": eligible_b},
                    ).scalars()
                )
                assert second_vendor_codes == expected_codes

                for excluded_role in (shared_role, child_role, customer_role):
                    excluded_codes = set(
                        sync_connection.execute(
                            text(
                                "SELECT p.code FROM role_permissions rp "
                                "JOIN permissions p ON p.id = rp.permission_id "
                                "WHERE rp.role_id = :role_id "
                                "AND p.code LIKE 'vendor.%'"
                            ),
                            {"role_id": excluded_role},
                        ).scalars()
                    )
                    assert excluded_codes == set()

                preserved_description = sync_connection.execute(
                    text("SELECT description FROM permissions WHERE id = :id"),
                    {"id": preserved_permission_id},
                ).scalar_one()
                assert preserved_description == "custom description preserved"

                permission_count = sync_connection.execute(
                    text("SELECT count(*) FROM permissions WHERE code = ANY(:codes)"),
                    {"codes": list(expected_codes)},
                ).scalar_one()
                assert permission_count == len(expected_codes)

                with Operations.context(MigrationContext.configure(sync_connection)):
                    migration.upgrade()
                    migration.downgrade()

                repeated_count = sync_connection.execute(
                    text("SELECT count(*) FROM role_permissions WHERE role_id IN (:a, :b)"),
                    {"a": eligible_a, "b": eligible_b},
                ).scalar_one()
                assert repeated_count == 2 * len(expected_codes)

            await connection.run_sync(exercise)
            await transaction.rollback()
    finally:
        await engine.dispose()
