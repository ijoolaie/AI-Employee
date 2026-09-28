"""Real PostgreSQL concurrency coverage for password-reset throttling."""

import asyncio
import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import delete

from app.core.database import AsyncSessionLocal
from app.models.password_reset_token import PasswordResetToken
from app.models.tenant import Tenant
from app.models.user import User
from app.services import password_reset_service


@pytest_asyncio.fixture
async def password_reset_race_setup(monkeypatch):
    settings = SimpleNamespace(
        password_reset_rate_limit=1,
        password_reset_rate_window_minutes=15,
        password_reset_token_expire_minutes=30,
        frontend_base_url="https://example.test",
    )
    monkeypatch.setattr(password_reset_service, "get_settings", lambda: settings)

    async with AsyncSessionLocal() as db:
        tenant = Tenant(
            name="Password Reset Race Test",
            slug=f"password-reset-race-{uuid.uuid4().hex[:12]}",
            status="active",
        )
        db.add(tenant)
        await db.flush()

        user = User(
            tenant_id=tenant.id,
            email=f"user-{uuid.uuid4().hex[:12]}@example.test",
            password_hash="test-hash",
            full_name="Password Reset Race User",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        tenant_id = tenant.id
        user_id = user.id
        email = user.email
        tenant_slug = tenant.slug

    yield tenant_id, user_id, email, tenant_slug

    async with AsyncSessionLocal() as db:
        await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await db.commit()


@pytest.mark.asyncio
async def test_concurrent_reset_requests_serialize_on_user_lock(
    password_reset_race_setup,
    monkeypatch,
):
    tenant_id, user_id, email, tenant_slug = password_reset_race_setup

    first_enqueued = asyncio.Event()
    second_enqueued = asyncio.Event()
    release_first = asyncio.Event()
    calls = []

    async def enqueue(db, *, kind, tenant_id, dedupe_key, payload):
        calls.append(dedupe_key)
        if len(calls) == 1:
            first_enqueued.set()
            await release_first.wait()
        else:
            second_enqueued.set()

    async def record(*_args, **_kwargs):
        return None

    monkeypatch.setattr(password_reset_service.outbox_service, "enqueue", enqueue)
    monkeypatch.setattr(password_reset_service.audit_service, "record", record)

    async def request_one():
        async with AsyncSessionLocal() as db:
            result = await password_reset_service.request_reset(
                db,
                email=email,
                tenant_slug=tenant_slug,
            )
            await db.commit()
            return result

    first = asyncio.create_task(request_one())
    await asyncio.wait_for(first_enqueued.wait(), timeout=2)

    second = asyncio.create_task(request_one())
    await asyncio.sleep(0.1)

    assert not second_enqueued.is_set(), (
        "a concurrent reset request reached email enqueue before the first "
        "transaction released the User lock"
    )

    release_first.set()
    await asyncio.gather(first, second)

    assert len(calls) == 1

    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                PasswordResetToken.__table__.select().where(
                    PasswordResetToken.user_id == user_id
                )
            )
        ).all()
        assert len(rows) == 1
