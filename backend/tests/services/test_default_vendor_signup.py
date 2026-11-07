from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services import auth_service


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return self

    def all(self):
        return self.rows


class _ResolverDb:
    def __init__(self, rows):
        self.rows = rows
        self.calls = 0

    async def execute(self, statement):
        self.calls += 1
        return _Result(self.rows)


@pytest.mark.asyncio
async def test_default_vendor_resolver_fails_closed_when_slug_is_unset(monkeypatch):
    monkeypatch.setattr(auth_service, "get_settings", lambda: SimpleNamespace(default_vendor_tenant_slug=None))
    db = _ResolverDb([])

    with pytest.raises(HTTPException) as exc:
        await auth_service._resolve_default_vendor(db)

    assert exc.value.status_code == 503
    assert db.calls == 0


@pytest.mark.asyncio
async def test_default_vendor_resolver_accepts_only_one_active_root_vendor(monkeypatch):
    vendor = SimpleNamespace(id=uuid4(), slug="primary-vendor", tenant_kind="vendor", parent_tenant_id=None, status="active")
    monkeypatch.setattr(auth_service, "get_settings", lambda: SimpleNamespace(default_vendor_tenant_slug=" primary-vendor "))
    resolved = await auth_service._resolve_default_vendor(_ResolverDb([vendor]))
    assert resolved is vendor


@pytest.mark.asyncio
@pytest.mark.parametrize("rows", [[], [object(), object()]])
async def test_default_vendor_resolver_fails_closed_for_missing_or_ambiguous_vendor(monkeypatch, rows):
    monkeypatch.setattr(auth_service, "get_settings", lambda: SimpleNamespace(default_vendor_tenant_slug="primary-vendor"))
    with pytest.raises(HTTPException) as exc:
        await auth_service._resolve_default_vendor(_ResolverDb(rows))
    assert exc.value.status_code == 503


class _Nested:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _CaptureDb:
    def __init__(self):
        self.added = []

    def begin_nested(self):
        return _Nested()

    def add(self, row):
        self.added.append(row)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_public_signup_customer_inherits_default_vendor_hierarchy_and_release():
    parent = SimpleNamespace(id=uuid4(), vendor_release_tag="vendor-release-7", delivery_revision="delivery-12")
    payload = SimpleNamespace(tenant_name="New Customer", tenant_slug="new-customer")
    db = _CaptureDb()

    tenant = await auth_service._create_tenant(db, payload, parent=parent)

    assert tenant.tenant_kind == "customer"
    assert tenant.parent_tenant_id == parent.id
    assert tenant.vendor_release_tag == parent.vendor_release_tag
    assert tenant.delivery_revision == parent.delivery_revision
    assert tenant.settings["control_plane_parent"] == str(parent.id)

@pytest.mark.asyncio
async def test_operator_bootstrap_refuses_unconfigured_default_vendor(monkeypatch):
    from scripts import bootstrap_default_vendor

    monkeypatch.setattr(bootstrap_default_vendor, "get_settings", lambda: SimpleNamespace(default_vendor_tenant_slug=None))

    def unexpected_database_access():
        raise AssertionError("bootstrap must fail before opening a database session")

    monkeypatch.setattr(bootstrap_default_vendor, "AsyncSessionLocal", unexpected_database_access)
    with pytest.raises(SystemExit, match="DEFAULT_VENDOR_TENANT_SLUG"):
        await bootstrap_default_vendor.bootstrap()

def test_new_edition_admin_roles_have_explicit_marketplace_purchase_permission():
    from app.services.auth_service import DEFAULT_TENANT_ADMIN_PERMISSIONS
    from app.services.edition_service import CUSTOMER_PERMISSIONS, RESELLER_PERMISSIONS

    for permissions in (DEFAULT_TENANT_ADMIN_PERMISSIONS, RESELLER_PERMISSIONS, CUSTOMER_PERMISSIONS):
        assert {"tenant.users.read", "tenant.users.create", "tenant.users.roles.assign", "tenant.users.manage"} <= set(permissions)
        assert "skill_marketplace.purchase" in permissions
        assert "marketplace.install" in permissions
        assert "employee_marketplace.publish" in permissions
        assert "employee_marketplace.install" in permissions
        assert "employee_marketplace.revoke" in permissions

@pytest.mark.asyncio
async def test_vendor_bootstrap_refuses_to_escalate_users_on_shared_admin_role():
    from scripts.bootstrap_default_vendor import _assert_bootstrap_role_is_exclusive

    user_id = uuid4()
    other_user_id = uuid4()
    role = SimpleNamespace(id=uuid4())

    class _AssignedUsers:
        def scalars(self):
            return self

        def __iter__(self):
            return iter([user_id, other_user_id])

    class _Db:
        async def execute(self, _statement):
            return _AssignedUsers()

    with pytest.raises(SystemExit, match="shared with other users"):
        await _assert_bootstrap_role_is_exclusive(
            _Db(), role=role, user=SimpleNamespace(id=user_id)
        )


@pytest.mark.asyncio
async def test_vendor_bootstrap_allows_admin_role_assigned_only_to_bootstrap_user():
    from scripts.bootstrap_default_vendor import _assert_bootstrap_role_is_exclusive

    user_id = uuid4()
    role = SimpleNamespace(id=uuid4())

    class _AssignedUsers:
        def scalars(self):
            return self

        def __iter__(self):
            return iter([user_id])

    class _Db:
        async def execute(self, _statement):
            return _AssignedUsers()

    await _assert_bootstrap_role_is_exclusive(
        _Db(), role=role, user=SimpleNamespace(id=user_id)
    )
