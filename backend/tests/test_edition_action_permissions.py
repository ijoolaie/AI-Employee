from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.edition_deps import require_reseller_customer_create


def _context(*, permission_tenant_matches: bool, api_key_id=None, api_key_scopes=None):
    tenant_id = uuid4()
    permission = SimpleNamespace(code="reseller.customer.create")
    admin_role = SimpleNamespace(
        tenant_id=tenant_id,
        name="Admin",
        permissions=[permission] if permission_tenant_matches else [],
    )
    foreign_role = SimpleNamespace(
        tenant_id=uuid4(),
        name="Other tenant role",
        permissions=[permission],
    )
    return SimpleNamespace(
        tenant=SimpleNamespace(id=tenant_id, tenant_kind="reseller"),
        tenant_id=tenant_id,
        user=SimpleNamespace(is_superuser=False, roles=[admin_role, foreign_role]),
        api_key_id=api_key_id,
        api_key_scopes=api_key_scopes,
    )


def _request():
    return SimpleNamespace(
        scope={"route": SimpleNamespace(path="/edition/reseller/customers")},
        method="POST",
    )


@pytest.mark.asyncio
async def test_reseller_customer_create_requires_explicit_tenant_permission():
    ctx = _context(permission_tenant_matches=True)
    assert await require_reseller_customer_create(ctx, _request()) is ctx


@pytest.mark.asyncio
async def test_reseller_customer_create_denies_missing_permission():
    ctx = _context(permission_tenant_matches=False)
    with pytest.raises(HTTPException) as exc:
        await require_reseller_customer_create(ctx, _request())
    assert exc.value.status_code == 403
    assert exc.value.detail == "Missing permission: reseller.customer.create"


@pytest.mark.asyncio
async def test_reseller_superuser_flag_does_not_replace_action_permission():
    ctx = _context(permission_tenant_matches=False)
    ctx.user.is_superuser = True
    with pytest.raises(HTTPException) as exc:
        await require_reseller_customer_create(ctx, _request())
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_reseller_api_key_requires_both_route_scope_and_user_permission():
    ctx = _context(
        permission_tenant_matches=True,
        api_key_id=uuid4(),
        api_key_scopes=["edition.reseller.customers.create"],
    )
    assert await require_reseller_customer_create(ctx, _request()) is ctx

    ctx.api_key_scopes = ["edition.reseller.customers.read"]
    with pytest.raises(HTTPException) as exc:
        await require_reseller_customer_create(ctx, _request())
    assert exc.value.status_code == 403

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "permission_code",
    [
        "reseller.customer.read",
        "reseller.customer.manage",
        "reseller.entitlement.delegate",
    ],
)
async def test_reseller_customer_operations_require_their_own_action_grant(permission_code):
    from app.core.edition_deps import require_reseller_permission

    ctx = _context(permission_tenant_matches=True)
    ctx.user.roles[0].permissions = [SimpleNamespace(code=permission_code)]
    dependency = require_reseller_permission(permission_code)
    assert await dependency(ctx, _request()) is ctx

    ctx.user.roles[0].permissions = [SimpleNamespace(code="reseller.customer.create")]
    with pytest.raises(HTTPException) as exc:
        await dependency(ctx, _request())
    assert exc.value.status_code == 403


def _vendor_context(permission_code: str | None):
    tenant_id = uuid4()
    local_permissions = [SimpleNamespace(code=permission_code)] if permission_code else []
    foreign_permissions = [SimpleNamespace(code=permission_code)] if permission_code else []
    return SimpleNamespace(
        tenant=SimpleNamespace(id=tenant_id, tenant_kind="vendor"),
        tenant_id=tenant_id,
        user=SimpleNamespace(
            is_superuser=False,
            roles=[
                SimpleNamespace(tenant_id=tenant_id, name="Admin", permissions=local_permissions),
                SimpleNamespace(tenant_id=uuid4(), name="Foreign Admin", permissions=foreign_permissions),
            ],
        ),
        api_key_id=None,
        api_key_scopes=None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("permission_code", "route", "method"),
    [
        ("vendor.tenant.read", "/edition/vendor/tenants", "GET"),
        ("vendor.reseller.read", "/edition/vendor/resellers", "GET"),
        ("vendor.reseller.create", "/edition/vendor/resellers", "POST"),
        ("vendor.reseller.manage", "/edition/vendor/resellers/{reseller_id}/suspend", "POST"),
        ("vendor.customer.read", "/edition/vendor/customers", "GET"),
        ("vendor.customer.create", "/edition/vendor/customers", "POST"),
        ("vendor.customer.manage", "/edition/vendor/customers/{customer_id}/suspend", "POST"),
    ],
)
async def test_vendor_control_plane_requires_operation_specific_tenant_permission(permission_code, route, method):
    from app.core.edition_deps import require_vendor_permission

    ctx = _vendor_context(permission_code)
    request = SimpleNamespace(scope={"route": SimpleNamespace(path=route)}, method=method)
    dependency = require_vendor_permission(permission_code)
    assert await dependency(ctx, request) is ctx

    ctx.user.roles[0].permissions = []
    with pytest.raises(HTTPException) as exc:
        await dependency(ctx, request)
    assert exc.value.status_code == 403
    assert exc.value.detail == f"Missing permission: {permission_code}"


@pytest.mark.asyncio
async def test_vendor_permission_from_foreign_tenant_does_not_grant_access():
    from app.core.edition_deps import require_vendor_permission

    ctx = _vendor_context(None)
    ctx.user.roles[1].permissions = [SimpleNamespace(code="vendor.reseller.create")]
    request = SimpleNamespace(scope={"route": SimpleNamespace(path="/edition/vendor/resellers")}, method="POST")
    with pytest.raises(HTTPException) as exc:
        await require_vendor_permission("vendor.reseller.create")(ctx, request)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_vendor_superuser_does_not_bypass_action_permission():
    from app.core.edition_deps import require_vendor_permission

    ctx = _vendor_context(None)
    ctx.user.is_superuser = True
    request = SimpleNamespace(scope={"route": SimpleNamespace(path="/edition/vendor/customers")}, method="POST")
    with pytest.raises(HTTPException) as exc:
        await require_vendor_permission("vendor.customer.create")(ctx, request)
    assert exc.value.status_code == 403
