from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1 import tenant_admin


def _result(value=None, *, scalar=None):
    return SimpleNamespace(
        scalar_one_or_none=lambda: value,
        scalar_one=lambda: scalar,
    )


def _context(tenant_id, actor_id):
    admin_role = SimpleNamespace(
        tenant_id=tenant_id,
        name="Admin",
        permissions=[SimpleNamespace(code="tenant.users.manage")],
    )
    actor = SimpleNamespace(id=actor_id, roles=[admin_role])
    return SimpleNamespace(
        tenant_id=tenant_id,
        user_id=actor_id,
        user=actor,
    )


@pytest.mark.asyncio
async def test_tenant_admin_cannot_deactivate_last_active_admin(monkeypatch):
    tenant_id, actor_id, target_id = uuid4(), uuid4(), uuid4()
    ctx = _context(tenant_id, actor_id)
    target = SimpleNamespace(
        id=target_id, tenant_id=tenant_id, is_active=True,
        email="last-admin@example.com", full_name="Last Admin",
        roles=[SimpleNamespace(tenant_id=tenant_id, name="Owner")],
    )
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[_result(object()), _result(target), _result(scalar=1)]),
        commit=AsyncMock(), refresh=AsyncMock(),
    )
    monkeypatch.setattr(tenant_admin.audit_service, "record", AsyncMock())

    with pytest.raises(HTTPException) as exc:
        await tenant_admin.update_user_status(
            target_id, tenant_admin.UserStatusUpdate(is_active=False), ctx, db,
        )

    assert exc.value.status_code == 409
    assert target.is_active is True
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_tenant_admin_can_deactivate_one_of_two_active_admins(monkeypatch):
    tenant_id, actor_id, target_id = uuid4(), uuid4(), uuid4()
    ctx = _context(tenant_id, actor_id)
    target = SimpleNamespace(
        id=target_id, tenant_id=tenant_id, is_active=True,
        email="admin@example.com", full_name="Admin",
        roles=[SimpleNamespace(tenant_id=tenant_id, name="Admin")],
    )
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[_result(object()), _result(target), _result(scalar=2)]),
        commit=AsyncMock(), refresh=AsyncMock(),
    )
    monkeypatch.setattr(tenant_admin.audit_service, "record", AsyncMock())

    response = await tenant_admin.update_user_status(
        target_id, tenant_admin.UserStatusUpdate(is_active=False), ctx, db,
    )

    assert response.data.is_active is False
    assert target.is_active is False
    db.commit.assert_awaited_once()
