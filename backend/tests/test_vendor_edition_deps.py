from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.edition_deps import (
    EDITION_SCOPE_ALLOWLIST_BY_KIND,
    _enforce_api_key_scope,
    require_vendor_admin,
)


@pytest.mark.asyncio
async def test_vendor_superuser_does_not_need_platform_admin_flag():
    tenant_id = 'vendor-tenant-id'
    ctx = SimpleNamespace(
        tenant=SimpleNamespace(tenant_kind='vendor'),
        tenant_id=tenant_id,
        user=SimpleNamespace(is_superuser=True, is_platform_admin=False, roles=[]),
    )

    request = SimpleNamespace(
        scope={"route": SimpleNamespace(path="/edition/vendor/tenants")},
        method="GET",
    )
    assert await require_vendor_admin(ctx, request) is ctx


@pytest.mark.asyncio
async def test_vendor_admin_role_is_sufficient_without_platform_admin():
    tenant_id = 'vendor-tenant-id'
    ctx = SimpleNamespace(
        tenant=SimpleNamespace(tenant_kind='vendor'),
        tenant_id=tenant_id,
        user=SimpleNamespace(
            is_superuser=False,
            is_platform_admin=False,
            roles=[SimpleNamespace(tenant_id=tenant_id, name='Admin')],
        ),
    )

    request = SimpleNamespace(
        scope={"route": SimpleNamespace(path="/edition/vendor/tenants")},
        method="GET",
    )
    assert await require_vendor_admin(ctx, request) is ctx


@pytest.mark.asyncio
async def test_customer_tenant_cannot_use_vendor_control_plane():
    ctx = SimpleNamespace(
        tenant=SimpleNamespace(tenant_kind='customer'),
        tenant_id='customer-id',
        user=SimpleNamespace(is_superuser=True, is_platform_admin=True, roles=[]),
    )

    request = SimpleNamespace(
        scope={"route": SimpleNamespace(path="/edition/vendor/tenants")},
        method="GET",
    )
    with pytest.raises(HTTPException) as exc:
        await require_vendor_admin(ctx, request)
    assert exc.value.status_code == 403
    assert exc.value.detail == 'Vendor edition access required'


def test_edition_scope_allowlist_is_restricted_by_tenant_kind():
    assert "edition.vendor.resellers.create" in EDITION_SCOPE_ALLOWLIST_BY_KIND["vendor"]
    assert "edition.vendor.resellers.create" not in EDITION_SCOPE_ALLOWLIST_BY_KIND["customer"]
    assert "edition.licenses.revoke" not in EDITION_SCOPE_ALLOWLIST_BY_KIND["customer"]


def test_vendor_api_key_scope_is_enforced_even_for_superuser():
    ctx = SimpleNamespace(
        api_key_id="test-api-key",
        api_key_scopes=["edition.vendor.tenants.read"],
        user=SimpleNamespace(is_superuser=True),
    )
    request = SimpleNamespace(
        scope={"route": SimpleNamespace(path="/edition/vendor/tenants")},
        method="GET",
    )
    _enforce_api_key_scope(ctx, request, "vendor")


def test_vendor_api_key_without_required_scope_is_rejected_even_for_superuser():
    ctx = SimpleNamespace(
        api_key_id="test-api-key",
        api_key_scopes=["edition.vendor.tenants.read"],
        user=SimpleNamespace(is_superuser=True),
    )
    request = SimpleNamespace(
        scope={"route": SimpleNamespace(path="/edition/vendor/resellers")},
        method="POST",
    )
    with pytest.raises(HTTPException) as exc:
        _enforce_api_key_scope(ctx, request, "vendor")
    assert exc.value.status_code == 403
    assert "edition.vendor.resellers.create" in exc.value.detail


def test_unmapped_edition_api_key_route_fails_closed():
    ctx = SimpleNamespace(
        api_key_id="test-api-key",
        api_key_scopes=["*"],
        user=SimpleNamespace(is_superuser=True),
    )
    request = SimpleNamespace(
        scope={"route": SimpleNamespace(path="/edition/vendor/new-sensitive-route")},
        method="POST",
    )
    with pytest.raises(HTTPException) as exc:
        _enforce_api_key_scope(ctx, request, "vendor")
    assert exc.value.status_code == 403


def test_legacy_api_key_without_scopes_is_denied_not_treated_as_bearer():
    ctx = SimpleNamespace(
        api_key_id="legacy-api-key",
        api_key_scopes=None,
        user=SimpleNamespace(is_superuser=True),
    )
    request = SimpleNamespace(
        scope={"route": SimpleNamespace(path="/edition/vendor/tenants")},
        method="GET",
    )
    with pytest.raises(HTTPException) as exc:
        _enforce_api_key_scope(ctx, request, "vendor")
    assert exc.value.status_code == 403
    assert "without explicit scopes" in exc.value.detail


def test_bearer_context_keeps_existing_edition_scope_behavior():
    ctx = SimpleNamespace(
        api_key_id=None,
        api_key_scopes=None,
        user=SimpleNamespace(is_superuser=True),
    )
    request = SimpleNamespace(
        scope={"route": SimpleNamespace(path="/edition/vendor/tenants")},
        method="GET",
    )
    _enforce_api_key_scope(ctx, request, "vendor")
