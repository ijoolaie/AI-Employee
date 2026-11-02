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
