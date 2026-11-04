from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import uuid

import pytest
from pydantic import ValidationError

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import verify_password
from app.models.tenant_invitation import TenantInvitation
from app.models.role import Role
from app.models.user import User
from app.services import tenant_invitation_service as service
from app.schemas.edition import ChildTenantProvisionRequest


def _result(value=None, *, many=None):
    if many is not None:
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: many))
    return SimpleNamespace(scalar_one_or_none=lambda: value)


def _invitation(*, accepted_at=None, revoked_at=None, expires_at=None):
    return TenantInvitation(
        id=uuid.uuid4(), tenant_id=uuid.uuid4(), user_id=uuid.uuid4(),
        email="member@example.test", token_hash=service._token_hash("invite-token-value"),
        expires_at=expires_at or datetime.now(timezone.utc) + timedelta(days=1),
        accepted_at=accepted_at, revoked_at=revoked_at,
    )


@pytest.mark.asyncio
async def test_create_invitation_stores_only_hash_and_creates_inactive_user(monkeypatch):
    tenant_id = uuid.uuid4()
    tenant = SimpleNamespace(id=tenant_id, status="active")
    role = Role(id=uuid.uuid4(), tenant_id=tenant_id, name="Member")
    added = []
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[_result(tenant), _result(None), _result(many=[])]),
        add=Mock(side_effect=added.append), flush=AsyncMock(),
    )
    monkeypatch.setattr(service.audit_service, "record", AsyncMock())

    invitation, raw_token = await service.create_invitation(
        db, tenant_id=tenant_id, inviter_user_id=uuid.uuid4(),
        email="Member@Example.Test", full_name="New Member", roles=[role],
    )

    user = next(row for row in added if isinstance(row, User))
    assert invitation.token_hash == service._token_hash(raw_token)
    assert raw_token not in invitation.token_hash
    assert user.email == "member@example.test"
    assert user.is_active is False
    assert user.is_superuser is False
    assert user.roles == [role]
    assert invitation.user_id == user.id
    assert invitation.expires_at > datetime.now(timezone.utc)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invitation",
    [
        _invitation(accepted_at=datetime.now(timezone.utc)),
        _invitation(revoked_at=datetime.now(timezone.utc)),
        _invitation(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)),
    ],
)
async def test_accept_rejects_replayed_revoked_or_expired_invitation(monkeypatch, invitation):
    db = SimpleNamespace(execute=AsyncMock(return_value=_result(invitation)))
    with pytest.raises(UnauthorizedError):
        await service.accept_invitation(db, raw_token="invite-token-value", password="a-very-long-password")
    assert db.execute.await_count == 1


@pytest.mark.asyncio
async def test_acceptance_does_not_activate_without_paid_subscription(monkeypatch):
    invitation = _invitation()
    tenant = SimpleNamespace(id=invitation.tenant_id, status="active")
    user = SimpleNamespace(
        id=invitation.user_id, tenant_id=invitation.tenant_id, email=invitation.email,
        is_active=False, password_hash="old", password_changed_at=None, auth_token_version=0,
    )
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[_result(invitation), _result(tenant), _result(user), _result(None), _result(None)]),
    )
    monkeypatch.setattr(service.audit_service, "record", AsyncMock())

    accepted, activated = await service.accept_invitation(
        db, raw_token="invite-token-value", password="a-very-long-password",
    )

    assert accepted.accepted_at is not None
    assert activated is False
    assert user.is_active is False
    assert verify_password("a-very-long-password", user.password_hash)
    assert user.auth_token_version == 0


@pytest.mark.asyncio
async def test_acceptance_activates_only_with_positive_paid_stripe_subscription(monkeypatch):
    invitation = _invitation()
    tenant = SimpleNamespace(id=invitation.tenant_id, status="active")
    user = SimpleNamespace(
        id=invitation.user_id, tenant_id=invitation.tenant_id, email=invitation.email,
        is_active=False, password_hash="old", password_changed_at=None, auth_token_version=0,
    )
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[_result(invitation), _result(tenant), _result(user), _result(uuid.uuid4())]),
    )
    monkeypatch.setattr(service.audit_service, "record", AsyncMock())

    _, activated = await service.accept_invitation(
        db, raw_token="invite-token-value", password="a-very-long-password",
    )

    assert activated is True
    assert user.is_active is True
    assert user.auth_token_version == 1


@pytest.mark.asyncio
async def test_acceptance_rejects_cross_tenant_user_mismatch(monkeypatch):
    invitation = _invitation()
    tenant = SimpleNamespace(id=invitation.tenant_id, status="active")
    db = SimpleNamespace(execute=AsyncMock(side_effect=[_result(invitation), _result(tenant), _result(None)]))
    with pytest.raises(UnauthorizedError):
        await service.accept_invitation(db, raw_token="invite-token-value", password="a-very-long-password")


@pytest.mark.asyncio
async def test_payment_after_acceptance_activates_only_the_accepted_invitee(monkeypatch):
    invitation = _invitation(accepted_at=datetime.now(timezone.utc))
    user = SimpleNamespace(
        id=invitation.user_id, tenant_id=invitation.tenant_id, email=invitation.email,
        is_active=False, auth_token_version=0,
    )
    db = SimpleNamespace(execute=AsyncMock(side_effect=[_result(many=[invitation]), _result(user), _result(uuid.uuid4())]))
    monkeypatch.setattr(service.audit_service, "record", AsyncMock())

    activated = await service.activate_eligible_invited_users(db, tenant_id=invitation.tenant_id)

    assert activated == 1
    assert user.is_active is True
    assert user.auth_token_version == 1


@pytest.mark.asyncio
async def test_payment_after_acceptance_does_not_activate_when_invitation_not_accepted(monkeypatch):
    invitation = _invitation()
    db = SimpleNamespace(execute=AsyncMock(return_value=_result(many=[])))

    activated = await service.activate_eligible_invited_users(db, tenant_id=invitation.tenant_id)

    assert activated == 0
    assert db.execute.await_count == 1


def test_child_tenant_provision_request_no_longer_accepts_initial_password():
    payload = {
        "name": "New Customer", "slug": "new-customer",
        "admin_email": "admin@example.com",
    }
    assert ChildTenantProvisionRequest.model_validate(payload).admin_email == "admin@example.com"
    with pytest.raises(ValidationError):
        ChildTenantProvisionRequest.model_validate({**payload, "admin_password": "unsafe-initial-password"})



@pytest.mark.asyncio
async def test_reissuing_pending_invitation_revokes_previous_token(monkeypatch):
    tenant_id = uuid.uuid4()
    user = User(
        id=uuid.uuid4(), tenant_id=tenant_id, email="member@example.com",
        password_hash="placeholder", full_name="Member", is_active=False, roles=[],
    )
    previous = TenantInvitation(
        id=uuid.uuid4(), tenant_id=tenant_id, user_id=user.id, email=user.email,
        token_hash=service._token_hash("old-invitation-token"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    role = Role(id=uuid.uuid4(), tenant_id=tenant_id, name="Member")
    added = []
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[
            _result(SimpleNamespace(id=tenant_id, status="active")),
            _result(user), _result(many=[previous]), _result(many=[previous]),
        ]),
        add=Mock(side_effect=added.append), flush=AsyncMock(),
    )
    monkeypatch.setattr(service.audit_service, "record", AsyncMock())

    invitation, token = await service.create_invitation(
        db, tenant_id=tenant_id, inviter_user_id=uuid.uuid4(),
        email=user.email, full_name=None, roles=[role],
    )

    assert previous.revoked_at is not None
    assert invitation.user_id == user.id
    assert invitation.token_hash == service._token_hash(token)
    assert user.roles == [role]
    assert added == [invitation]


@pytest.mark.asyncio
async def test_revoke_invitation_is_tenant_scoped_and_audited(monkeypatch):
    invitation = _invitation()
    db = SimpleNamespace(execute=AsyncMock(return_value=_result(invitation)))
    audit = AsyncMock()
    monkeypatch.setattr(service.audit_service, "record", audit)

    revoked = await service.revoke_invitation(
        db, tenant_id=invitation.tenant_id, invitation_id=invitation.id, actor_id=uuid.uuid4(),
    )

    assert revoked.revoked_at is not None
    audit.assert_awaited_once()


@pytest.mark.asyncio
async def test_revoke_invitation_rejects_cross_tenant_identifier(monkeypatch):
    db = SimpleNamespace(execute=AsyncMock(return_value=_result(None)))
    with pytest.raises(NotFoundError):
        await service.revoke_invitation(
            db, tenant_id=uuid.uuid4(), invitation_id=uuid.uuid4(), actor_id=uuid.uuid4(),
        )
