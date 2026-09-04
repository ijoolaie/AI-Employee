import uuid

import pytest

from app.ai.tool_registry import registry
from app.core.deps import TenantContext, has_permission


class _User:
    is_superuser = False
    roles = []


class _Tenant:
    def __init__(self, tenant_id):
        self.id = tenant_id


@pytest.mark.asyncio
async def test_permissions_are_tenant_scoped():
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    user = _User()
    role = type(
        "Role",
        (),
        {
            "tenant_id": tenant_a,
            "permissions": [type("Permission", (), {"code": "privacy.customer.delete"})()],
        },
    )()
    user.roles = [role]
    ctx = TenantContext(user=user, tenant=_Tenant(tenant_a))
    assert await has_permission(ctx, "privacy.customer.delete") is True

    cross_tenant_role = type(
        "Role",
        (),
        {
            "tenant_id": tenant_b,
            "permissions": [type("Permission", (), {"code": "privacy.customer.delete"})()],
        },
    )()
    user.roles = [cross_tenant_role]
    assert await has_permission(ctx, "privacy.customer.delete") is False


def test_every_registered_tool_declares_permission_and_side_effects_are_approved():
    for tool in registry.list():
        assert tool.required_permission
        if tool.side_effects:
            assert tool.requires_approval is True
