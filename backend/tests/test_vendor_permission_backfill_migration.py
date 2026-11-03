"""Contract tests for the legacy Vendor Admin permission backfill."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "w29_vendor_admin_action_permissions.py"
)
SPEC = spec_from_file_location("w29_vendor_admin_action_permissions", MIGRATION_PATH)
assert SPEC is not None and SPEC.loader is not None
migration = module_from_spec(SPEC)
SPEC.loader.exec_module(migration)


class RecordingBind:
    def __init__(self):
        self.executed = []

    def execute(self, statement, parameters=None):
        self.executed.append((str(statement), parameters))


def test_backfill_seeds_catalog_and_only_grants_existing_root_vendor_admin_roles(monkeypatch):
    assert len(migration.revision) <= 32
    bind = RecordingBind()
    monkeypatch.setattr(migration.op, "get_bind", lambda: bind)

    migration.upgrade()

    assert len(bind.executed) == len(migration.VENDOR_ADMIN_PERMISSIONS) + 1
    for (statement, parameters), code in zip(
        bind.executed[:-1], migration.VENDOR_ADMIN_PERMISSIONS, strict=True
    ):
        assert "INSERT INTO permissions" in statement
        assert "ON CONFLICT (code) DO NOTHING" in statement
        assert parameters == {
            "code": code,
            "description": f"Vendor control-plane permission: {code}",
        }

    grant_sql, grant_parameters = bind.executed[-1]
    assert "INSERT INTO role_permissions" in grant_sql
    assert "t.tenant_kind = 'vendor'" in grant_sql
    assert "t.parent_tenant_id IS NULL" in grant_sql
    assert "u.is_platform_admin IS TRUE" in grant_sql
    assert "u.tenant_id = t.id" in grant_sql
    assert "lower(r.name) IN ('admin', 'owner', 'tenant_admin')" in grant_sql
    assert "ON CONFLICT (role_id, permission_id) DO NOTHING" in grant_sql
    assert grant_parameters is None


def test_backfill_does_not_revoke_grants_on_downgrade():
    # Downgrade intentionally preserves grants that may have been relied upon
    # or curated after the migration was applied.
    migration.downgrade()
