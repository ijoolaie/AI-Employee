from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.tenant_admin import _assert_roles_within_authority


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
