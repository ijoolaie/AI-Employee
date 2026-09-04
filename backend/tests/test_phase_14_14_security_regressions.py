import pytest

from app.ai.tool_registry import RegisteredTool, registry
from app.core.exceptions import ValidationAppError
from app.core.deps import TenantContext, has_permission


class _User:
    is_superuser = False
    roles = []


class _Tenant:
    def __init__(self, tenant_id):
        self.id = tenant_id


@pytest.mark.asyncio
async def test_permissions_are_tenant_scoped():
    import uuid

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    user = _User()
    role = type("Role", (), {"tenant_id": tenant_a, "permissions": [type("Permission", (), {"code": "privacy.customer.delete"})()]})()
    user.roles = [role]
    ctx = TenantContext(user=user, tenant=_Tenant(tenant_a))
    assert await has_permission(ctx, "privacy.customer.delete") is True
    cross_tenant_role = type("Role", (), {"tenant_id": tenant_b, "permissions": [type("Permission", (), {"code": "privacy.customer.delete"})()]})()
    user.roles = [cross_tenant_role]
    assert await has_permission(ctx, "privacy.customer.delete") is False


def test_side_effecting_tools_are_approval_gated_at_registration():
    name = "_phase_14_14_unsafe_side_effect"
    with pytest.raises(ValidationAppError, match="must require human approval"):
        registry.register(
            RegisteredTool(
                name=name,
                description="unsafe test tool",
                input_schema={"type": "object"},
                handler=lambda _: {"ok": True},
                side_effects=True,
                required_permission="run.execute",
                requires_approval=False,
            )
        )
    assert name not in {tool.name for tool in registry.list()}


def test_every_registered_tool_declares_permission_and_side_effects_are_approved():
    for tool in registry.list():
        assert tool.required_permission
        if tool.side_effects:
            assert tool.requires_approval is True


def test_privacy_permissions_remain_explicit():
    from app.core import deps

    assert "privacy.customer.read" in str(deps.PrivacyCustomerReadContext)
    assert "privacy.customer.export" in str(deps.PrivacyCustomerExportContext)
    assert "privacy.customer.delete" in str(deps.PrivacyCustomerDeleteContext)
