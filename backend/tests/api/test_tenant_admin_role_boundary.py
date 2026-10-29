from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.tenant_admin import (
    HandoffNotificationSettingsUpdate,
    _assert_roles_within_authority,
    require_tenant_admin,
)


def _ctx(*permission_codes: str, superuser: bool = False):
    tenant_id = uuid4()
    permissions = [SimpleNamespace(code=code) for code in permission_codes]
    role = SimpleNamespace(tenant_id=tenant_id, permissions=permissions)
    user = SimpleNamespace(is_superuser=superuser, roles=[role])
    return SimpleNamespace(user=user, tenant_id=tenant_id)


def _role(tenant_id, *permission_codes: str):
    return SimpleNamespace(
        tenant_id=tenant_id,
        permissions=[SimpleNamespace(code=code) for code in permission_codes],
    )


def test_tenant_admin_cannot_assign_role_with_extra_permission():
    ctx = _ctx("employee.read", "employee.write")
    higher_role = _role(ctx.tenant_id, "employee.read", "employee.write", "agent.emergency_kill")

    with pytest.raises(HTTPException) as exc:
        _assert_roles_within_authority(ctx, [higher_role])

    assert exc.value.status_code == 403


def test_tenant_admin_can_assign_role_within_existing_authority():
    ctx = _ctx("employee.read", "employee.write")
    peer_role = _role(ctx.tenant_id, "employee.read")

    _assert_roles_within_authority(ctx, [peer_role])


def test_superuser_can_assign_any_role():
    ctx = _ctx(superuser=True)
    higher_role = _role(ctx.tenant_id, "platform.admin")

    _assert_roles_within_authority(ctx, [higher_role])


def test_handoff_notification_email_is_normalized():
    payload = HandoffNotificationSettingsUpdate(email="  Ops@Example.COM  ")

    assert payload.email == "ops@example.com"


@pytest.mark.parametrize("email", ["not-an-email", "ops@", "@example.com", "ops example@example.com"])
def test_handoff_notification_email_rejects_malformed_values(email):
    with pytest.raises(ValueError):
        HandoffNotificationSettingsUpdate(email=email)


def test_handoff_notification_email_can_be_cleared_with_blank_value():
    assert HandoffNotificationSettingsUpdate(email="  ").email is None
    assert HandoffNotificationSettingsUpdate(email=None).email is None


@pytest.mark.asyncio
async def test_handoff_notification_settings_require_tenant_admin():
    tenant_id = uuid4()
    ctx = SimpleNamespace(
        user=SimpleNamespace(
            is_superuser=False,
            roles=[SimpleNamespace(name="support_agent", tenant_id=tenant_id)],
        ),
        tenant_id=tenant_id,
    )

    with pytest.raises(HTTPException) as exc:
        await require_tenant_admin(ctx)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_handoff_notification_settings_allow_tenant_admin_role():
    tenant_id = uuid4()
    ctx = SimpleNamespace(
        user=SimpleNamespace(
            is_superuser=False,
            roles=[SimpleNamespace(name="tenant_admin", tenant_id=tenant_id)],
        ),
        tenant_id=tenant_id,
    )

    assert await require_tenant_admin(ctx) is ctx
