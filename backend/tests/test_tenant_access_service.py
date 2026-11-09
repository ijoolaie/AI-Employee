from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest
from app.core.exceptions import ConflictError
from app.services import tenant_access_service as service

class Result:
    def __init__(self, value): self.value = value
    def scalar_one_or_none(self): return self.value

@pytest.mark.asyncio
async def test_legacy_tenant_access_remains_unchanged_without_database_lookup():
    db = SimpleNamespace(execute=AsyncMock())
    tenant = SimpleNamespace(id=uuid4(), access_grant_required=False)
    assert await service.tenant_has_access(db, tenant=tenant) is True
    db.execute.assert_not_awaited()

@pytest.mark.asyncio
async def test_required_tenant_accepts_verified_active_paid_subscription():
    db = SimpleNamespace(execute=AsyncMock(return_value=Result(uuid4())))
    tenant = SimpleNamespace(id=uuid4(), access_grant_required=True)
    assert await service.tenant_has_access(db, tenant=tenant) is True
    query = db.execute.await_args.args[0]
    assert "stripe" in query.compile().params.values()
    assert "subscriptions.current_period_end" in str(query)

@pytest.mark.asyncio
async def test_required_tenant_accepts_valid_demo_grant_after_no_paid_subscription():
    db = SimpleNamespace(execute=AsyncMock(side_effect=[Result(None), Result(uuid4())]))
    tenant = SimpleNamespace(id=uuid4(), access_grant_required=True)
    assert await service.tenant_has_access(db, tenant=tenant) is True
    assert db.execute.await_count == 2

@pytest.mark.asyncio
async def test_required_tenant_denies_without_paid_subscription_or_demo_grant():
    db = SimpleNamespace(execute=AsyncMock(side_effect=[Result(None), Result(None)]))
    tenant = SimpleNamespace(id=uuid4(), access_grant_required=True)
    assert await service.tenant_has_access(db, tenant=tenant) is False
    assert db.execute.await_count == 2

@pytest.mark.asyncio
async def test_demo_grant_is_not_payment_and_is_time_bounded():
    now = datetime.now(timezone.utc)
    db = SimpleNamespace(execute=AsyncMock(side_effect=[Result(None), Result(uuid4())]))
    tenant = SimpleNamespace(id=uuid4(), access_grant_required=True)
    assert await service.tenant_has_access(db, tenant=tenant, now=now) is True
    paid_query = db.execute.await_args_list[0].args[0]
    grant_query = db.execute.await_args_list[1].args[0]
    assert "stripe" in paid_query.compile().params.values()
    assert "tenant_demo_grants" in str(grant_query)

@pytest.mark.asyncio
async def test_demo_grant_rejects_legacy_tenant_without_changing_legacy_gate():
    tenant = SimpleNamespace(id=uuid4(), access_grant_required=False)
    db = SimpleNamespace(execute=AsyncMock(return_value=Result(tenant)), add=MagicMock(), flush=AsyncMock())
    with pytest.raises(ConflictError):
        await service.create_demo_grant(db, tenant_id=tenant.id, actor_id=uuid4(), reason="Approved evaluation", expires_in_days=14)
    assert tenant.access_grant_required is False
    db.add.assert_not_called()

@pytest.mark.asyncio
async def test_demo_grant_is_audited_and_activates_eligible_accounts(monkeypatch):
    tenant = SimpleNamespace(id=uuid4(), access_grant_required=True)
    actor_id = uuid4()
    db = SimpleNamespace(execute=AsyncMock(return_value=Result(tenant)), add=MagicMock(), flush=AsyncMock())
    public_activation = AsyncMock(return_value=1)
    invited_activation = AsyncMock(return_value=2)
    audit = AsyncMock()
    monkeypatch.setattr(service, "activate_pending_public_signup_users", public_activation)
    monkeypatch.setattr(service.audit_service, "record", audit)
    monkeypatch.setattr("app.services.tenant_invitation_service.activate_eligible_invited_users", invited_activation)
    grant = await service.create_demo_grant(db, tenant_id=tenant.id, actor_id=actor_id, reason="Approved customer evaluation", expires_in_days=14)
    assert grant.tenant_id == tenant.id
    assert grant.granted_by_user_id == actor_id
    assert grant.expires_at > datetime.now(timezone.utc)
    public_activation.assert_awaited_once_with(db, tenant_id=tenant.id)
    invited_activation.assert_awaited_once_with(db, tenant_id=tenant.id)
    assert audit.await_args.kwargs["action"] == "tenant.demo_grant_created"
    assert audit.await_args.kwargs["metadata"]["activated_public_users"] == 1
    assert audit.await_args.kwargs["metadata"]["activated_invited_users"] == 2

@pytest.mark.asyncio
async def test_demo_grant_revocation_is_tenant_bound_and_audited_once(monkeypatch):
    tenant_id = uuid4()
    grant = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, revoked_at=None, expires_at=datetime.now(timezone.utc))
    db = SimpleNamespace(execute=AsyncMock(return_value=Result(grant)))
    audit = AsyncMock()
    monkeypatch.setattr(service.audit_service, "record", audit)

    first = await service.revoke_demo_grant(db, tenant_id=tenant_id, grant_id=grant.id, actor_id=uuid4())
    second = await service.revoke_demo_grant(db, tenant_id=tenant_id, grant_id=grant.id, actor_id=uuid4())

    assert first is grant and second is grant
    assert grant.revoked_at is not None
    assert audit.await_count == 1
    assert audit.await_args.kwargs["action"] == "tenant.demo_grant_revoked"
    for call in db.execute.await_args_list:
        sql = str(call.args[0])
        assert "tenant_demo_grants.tenant_id" in sql
        assert "tenant_demo_grants.id" in sql


@pytest.mark.asyncio
async def test_demo_grant_revocation_rejects_cross_tenant_grant(monkeypatch):
    from app.core.exceptions import NotFoundError

    db = SimpleNamespace(execute=AsyncMock(return_value=Result(None)))
    audit = AsyncMock()
    monkeypatch.setattr(service.audit_service, "record", audit)

    with pytest.raises(NotFoundError):
        await service.revoke_demo_grant(db, tenant_id=uuid4(), grant_id=uuid4(), actor_id=uuid4())

    query = db.execute.await_args.args[0]
    assert "tenant_demo_grants.tenant_id" in str(query)
    assert "tenant_demo_grants.id" in str(query)
    audit.assert_not_awaited()

@pytest.mark.asyncio
async def test_expired_paid_period_and_expired_demo_grant_deny_existing_tenant_access():
    now = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
    db = SimpleNamespace(execute=AsyncMock(side_effect=[Result(None), Result(None)]))
    tenant = SimpleNamespace(id=uuid4(), access_grant_required=True)

    assert await service.tenant_has_access(db, tenant=tenant, now=now) is False
    assert db.execute.await_count == 2

    paid_query = db.execute.await_args_list[0].args[0]
    demo_query = db.execute.await_args_list[1].args[0]
    assert 'subscriptions.status' in str(paid_query)
    assert 'subscriptions.current_period_end' in str(paid_query)
    assert 'tenant_demo_grants.expires_at' in str(demo_query)
    assert 'tenant_demo_grants.revoked_at' in str(demo_query)
    assert now in paid_query.compile().params.values()
    assert now in demo_query.compile().params.values()


@pytest.mark.asyncio
async def test_already_issued_portal_grant_is_denied_after_commercial_access_expires(monkeypatch):
    from fastapi import HTTPException
    from app.services import portal_access_service

    actor_tenant_id = uuid4()
    target_tenant_id = uuid4()
    actor_user_id = uuid4()
    grant_id = uuid4()
    grant = SimpleNamespace(id=grant_id, revoked_at=None)
    actor_tenant = SimpleNamespace(id=actor_tenant_id, tenant_kind='vendor', status='active')
    target_tenant = SimpleNamespace(
        id=target_tenant_id, tenant_kind='reseller', parent_tenant_id=actor_tenant_id, status='active'
    )

    class _Result:
        def __init__(self, value): self.value = value
        def scalar_one_or_none(self): return self.value

    db = SimpleNamespace(execute=AsyncMock(side_effect=[
        _Result(grant), _Result(actor_tenant), _Result(target_tenant)
    ]))
    commercial_access = AsyncMock(return_value=False)
    monkeypatch.setattr(portal_access_service, 'tenant_has_access', commercial_access)

    with pytest.raises(HTTPException) as exc:
        await portal_access_service.validate_portal_access_grant(
            db,
            actor_user_id=actor_user_id,
            actor_tenant_id=actor_tenant_id,
            target_tenant_id=target_tenant_id,
            grant_id=grant_id,
        )

    assert exc.value.status_code == 402
    assert exc.value.detail == 'Target tenant commercial entitlement is inactive'
    commercial_access.assert_awaited_once_with(db, tenant=target_tenant)
