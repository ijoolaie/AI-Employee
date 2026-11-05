from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.portal_access_service import _assert_direct_portal_edge


@pytest.mark.parametrize(
    ("actor_kind", "target_kind", "parent_matches"),
    [
        ("vendor", "reseller", True),
        ("vendor", "customer", True),
        ("reseller", "customer", True),
    ],
)
def test_portal_grant_accepts_only_supported_direct_edges(actor_kind, target_kind, parent_matches):
    actor_id = "actor-tenant"
    actor = SimpleNamespace(id=actor_id, tenant_kind=actor_kind)
    target = SimpleNamespace(
        id="target-tenant",
        tenant_kind=target_kind,
        parent_tenant_id=actor_id if parent_matches else "another-parent",
    )

    _assert_direct_portal_edge(actor, target)


@pytest.mark.parametrize(
    ("actor_kind", "target_kind", "parent_id"),
    [
        ("vendor", "reseller", "sibling-vendor"),
        ("vendor", "customer", "reseller-parent"),
        ("reseller", "vendor", "reseller"),
        ("reseller", "reseller", "reseller"),
        ("customer", "customer", "customer"),
        ("customer", "vendor", "customer"),
    ],
)
def test_portal_grant_rejects_sibling_indirect_and_invalid_edges(actor_kind, target_kind, parent_id):
    actor = SimpleNamespace(id="actor-tenant", tenant_kind=actor_kind)
    target = SimpleNamespace(
        id="target-tenant",
        tenant_kind=target_kind,
        parent_tenant_id=parent_id,
    )

    with pytest.raises(HTTPException) as exc:
        _assert_direct_portal_edge(actor, target)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_portal_context_permissions_are_evaluated_on_actor_home_tenant():
    from app.core.deps import TenantContext, has_permission

    permission = SimpleNamespace(code="employee.read")
    home_role = SimpleNamespace(tenant_id="home-tenant", permissions=[permission])
    target_role = SimpleNamespace(tenant_id="target-tenant", permissions=[SimpleNamespace(code="billing.manage")])
    user = SimpleNamespace(id="user-1", tenant_id="home-tenant", roles=[home_role, target_role])
    ctx = TenantContext(user=user, tenant=SimpleNamespace(id="target-tenant"))

    assert ctx.tenant_id == "target-tenant"
    assert ctx.actor_tenant_id == "home-tenant"
    assert await has_permission(ctx, "employee.read")
    assert not await has_permission(ctx, "billing.manage")


def test_api_keys_cannot_activate_portal_context():
    from app.api.v1.portal_access import _reject_api_key

    with pytest.raises(HTTPException) as exc:
        _reject_api_key(SimpleNamespace(api_key_id="key-1"))

    assert exc.value.status_code == 403
