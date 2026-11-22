"""PostgreSQL integration coverage for secure account email changes."""
import re
import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import hash_password
from app.models.email_change_token import EmailChangeToken
from app.models.outbox import OutboxMessage
from app.models.tenant import Tenant
from app.models.user import User
from app.services import email_change_service


@pytest_asyncio.fixture
async def email_change_setup(monkeypatch):
    settings = SimpleNamespace(
        smtp_host="smtp.test",
        smtp_from_email="noreply@test.invalid",
        frontend_base_url="https://app.test",
    )
    monkeypatch.setattr(email_change_service, "get_settings", lambda: settings)

    async with AsyncSessionLocal() as db:
        tenant = Tenant(
            name="Email Change Test",
            slug=f"email-change-{uuid.uuid4().hex[:12]}",
            status="active",
        )
        db.add(tenant)
        await db.flush()
        user = User(
            tenant_id=tenant.id,
            email=f"old-{uuid.uuid4().hex[:12]}@example.test",
            password_hash=hash_password("Current-password-123"),
            full_name="Email Change Test User",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        values = (tenant.id, user.id, user.email)

    yield values

    async with AsyncSessionLocal() as db:
        tenant_id, user_id, _ = values
        await db.execute(delete(EmailChangeToken).where(EmailChangeToken.user_id == user_id))
        await db.execute(delete(OutboxMessage).where(OutboxMessage.tenant_id == tenant_id, OutboxMessage.dedupe_key.like("email-change:%")))
        await db.execute(delete(User).where(User.id == user_id))
        await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await db.commit()


@pytest.mark.asyncio
async def test_email_change_requires_password_and_verified_token_invalidates_sessions(
    email_change_setup, monkeypatch
):
    tenant_id, user_id, old_email = email_change_setup
    audit_events = []

    async def capture_audit(db, **kwargs):
        audit_events.append(kwargs)
        return None

    monkeypatch.setattr(email_change_service.audit_service, "record", capture_audit)

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        with pytest.raises(UnauthorizedError):
            await email_change_service.request_email_change(
                db, user=user, current_password="wrong-password", new_email="new-address@example.test"
            )
        await db.rollback()

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        user.auth_token_version = 7
        await db.commit()

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        await email_change_service.request_email_change(
            db, user=user, current_password="Current-password-123", new_email="New-Address@example.test"
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        outbox = (await db.execute(
            select(OutboxMessage).where(
                OutboxMessage.tenant_id == tenant_id,
                OutboxMessage.dedupe_key.like("email-change:%"),
            )
        )).scalar_one()
        body = outbox.payload["body"]
    raw_token = re.search(r"confirm-email-change\?token=([^\s]+)", body).group(1)

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        assert user.email == old_email
        assert user.pending_email == "new-address@example.test"
        assert user.auth_token_version == 7

        await email_change_service.confirm_email_change(db, raw_token=raw_token)
        await db.commit()

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        assert user.email == "new-address@example.test"
        assert user.pending_email is None
        assert user.auth_token_version == 8
        with pytest.raises(UnauthorizedError):
            await email_change_service.confirm_email_change(db, raw_token=raw_token)
        await db.rollback()

    assert [event["action"] for event in audit_events] == [
        "auth.email_change_requested", "auth.email_change_completed"
    ]
    assert all("token" not in str(event.get("metadata", {})).lower() for event in audit_events)


@pytest.mark.asyncio
async def test_email_change_rejects_email_owned_by_another_user(email_change_setup):
    tenant_id, user_id, _ = email_change_setup
    async with AsyncSessionLocal() as db:
        owner = User(
            tenant_id=tenant_id,
            email=f"owned-{uuid.uuid4().hex[:12]}@example.test",
            password_hash=hash_password("Another-password-123"),
            is_active=True,
        )
        db.add(owner)
        await db.commit()
        target_email = owner.email

    try:
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
            with pytest.raises(ConflictError):
                await email_change_service.request_email_change(
                    db, user=user, current_password="Current-password-123", new_email=target_email
                )
            await db.rollback()
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.email == target_email, User.tenant_id == tenant_id))
            await db.commit()

@pytest.mark.asyncio
async def test_email_change_request_rate_limit_is_per_user(email_change_setup, monkeypatch):
    _, user_id, _ = email_change_setup

    async def capture_enqueue(*_args, **_kwargs):
        return None

    async def no_audit(*_args, **_kwargs):
        return None

    monkeypatch.setattr(email_change_service.outbox_service, "enqueue", capture_enqueue)
    monkeypatch.setattr(email_change_service.audit_service, "record", no_audit)

    for index in range(3):
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
            await email_change_service.request_email_change(
                db,
                user=user,
                current_password="Current-password-123",
                new_email=f"new-{index}-{uuid.uuid4().hex[:8]}@example.test",
            )
            await db.commit()
        async with AsyncSessionLocal() as db:
            from datetime import datetime, timedelta, timezone
            from sqlalchemy import update
            await db.execute(
                update(EmailChangeToken)
                .where(EmailChangeToken.user_id == user_id)
                .values(created_at=datetime.now(timezone.utc) - timedelta(minutes=2))
            )
            await db.commit()

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        with pytest.raises(ConflictError, match="Too many"):
            await email_change_service.request_email_change(
                db,
                user=user,
                current_password="Current-password-123",
                new_email="fourth@example.test",
            )
        await db.rollback()

@pytest.mark.asyncio
async def test_email_change_pending_address_is_tenant_scoped(email_change_setup, monkeypatch):
    tenant_id, user_id, _ = email_change_setup
    new_email = f"shared-{uuid.uuid4().hex[:10]}@example.test"
    async def no_audit(*_args, **_kwargs):
        return None
    monkeypatch.setattr(email_change_service.audit_service, "record", no_audit)

    async with AsyncSessionLocal() as db:
        other_tenant = Tenant(
            name="Second Email Tenant",
            slug=f"email-change-second-{uuid.uuid4().hex[:10]}",
            status="active",
        )
        db.add(other_tenant)
        await db.flush()
        other_user = User(
            tenant_id=other_tenant.id,
            email=f"other-{uuid.uuid4().hex[:10]}@example.test",
            password_hash=hash_password("Other-password-123"),
            is_active=True,
        )
        db.add(other_user)
        await db.commit()
        other_tenant_id, other_user_id = other_tenant.id, other_user.id

    try:
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
            await email_change_service.request_email_change(
                db, user=user, current_password="Current-password-123", new_email=new_email
            )
            await db.commit()
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.id == other_user_id))).scalar_one()
            await email_change_service.request_email_change(
                db, user=user, current_password="Other-password-123", new_email=new_email
            )
            await db.commit()
        async with AsyncSessionLocal() as db:
            rows = (await db.execute(
                select(User).where(User.pending_email == new_email)
            )).scalars().all()
            assert {row.tenant_id for row in rows} == {tenant_id, other_tenant_id}
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(EmailChangeToken).where(EmailChangeToken.user_id == other_user_id))
            await db.execute(delete(OutboxMessage).where(OutboxMessage.tenant_id == other_tenant_id))
            await db.execute(delete(User).where(User.id == other_user_id))
            await db.execute(delete(Tenant).where(Tenant.id == other_tenant_id))
            await db.commit()


@pytest.mark.asyncio
async def test_expired_email_change_token_does_not_promote_pending_address(email_change_setup, monkeypatch):
    _, user_id, old_email = email_change_setup
    async def no_audit(*_args, **_kwargs):
        return None
    monkeypatch.setattr(email_change_service.audit_service, "record", no_audit)

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        await email_change_service.request_email_change(
            db, user=user, current_password="Current-password-123", new_email="expired@example.test"
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        outbox = (await db.execute(
            select(OutboxMessage).where(OutboxMessage.dedupe_key.like("email-change:%"))
        )).scalar_one()
        raw_token = re.search(r"confirm-email-change\?token=([^\s]+)", outbox.payload["body"]).group(1)
        token = (await db.execute(
            select(EmailChangeToken).where(EmailChangeToken.user_id == user_id)
        )).scalar_one()
        from datetime import timedelta
        token.expires_at = token.created_at - timedelta(seconds=1)
        await db.commit()
        with pytest.raises(UnauthorizedError):
            await email_change_service.confirm_email_change(db, raw_token=raw_token)
        await db.rollback()

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        assert user.email == old_email
        assert user.pending_email == "expired@example.test"


@pytest.mark.asyncio
async def test_concurrent_requests_cannot_reserve_same_pending_email(email_change_setup, monkeypatch):
    import asyncio
    tenant_id, first_user_id, _ = email_change_setup
    new_email = f"race-{uuid.uuid4().hex[:10]}@example.test"
    async def no_audit(*_args, **_kwargs):
        return None
    monkeypatch.setattr(email_change_service.audit_service, "record", no_audit)

    async with AsyncSessionLocal() as db:
        second_user = User(
            tenant_id=tenant_id,
            email=f"second-{uuid.uuid4().hex[:10]}@example.test",
            password_hash=hash_password("Second-password-123"),
            is_active=True,
        )
        db.add(second_user)
        await db.commit()
        second_user_id = second_user.id

    async def request_for(user_id, password):
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
            try:
                await email_change_service.request_email_change(
                    db, user=user, current_password=password, new_email=new_email
                )
                await db.commit()
                return "accepted"
            except ConflictError:
                await db.rollback()
                return "conflict"

    try:
        outcomes = await asyncio.gather(
            request_for(first_user_id, "Current-password-123"),
            request_for(second_user_id, "Second-password-123"),
        )
        assert sorted(outcomes) == ["accepted", "conflict"]
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(EmailChangeToken).where(EmailChangeToken.user_id == second_user_id))
            await db.execute(delete(OutboxMessage).where(OutboxMessage.tenant_id == tenant_id, OutboxMessage.dedupe_key.like("email-change:%")))
            await db.execute(delete(User).where(User.id == second_user_id))
            await db.commit()