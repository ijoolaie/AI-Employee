from __future__ import annotations

import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.exceptions import TenantInactiveError
from app.models.outbox import OutboxMessage
from app.models.tenant import Tenant


async def _wait_for_lock(session_factory, pid: int) -> None:
    deadline = asyncio.get_running_loop().time() + 5
    async with session_factory() as observer:
        while asyncio.get_running_loop().time() < deadline:
            state = await observer.scalar(
                text("SELECT wait_event_type FROM pg_stat_activity WHERE pid = :pid"),
                {"pid": pid},
            )
            if state == "Lock":
                return
            await asyncio.sleep(0.02)
    raise AssertionError(f"PostgreSQL backend {pid} did not wait for tenant row lock")


@pytest.mark.asyncio
@pytest.mark.parametrize("channel", ["email", "whatsapp"])
async def test_suspended_tenant_outbox_is_dead_lettered_before_provider(monkeypatch, channel):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured; PostgreSQL integration test only")
    assert make_url(database_url).get_backend_name() == "postgresql"

    from app.workers import email_worker, whatsapp_worker

    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    tenant_id, outbox_id = uuid.uuid4(), uuid.uuid4()
    provider_calls = []

    @asynccontextmanager
    async def test_worker_session():
        async with sessions() as session:
            yield session

    try:
        async with sessions() as setup:
            async with setup.begin():
                setup.add(Tenant(
                    id=tenant_id,
                    name=f"Suspended {channel} delivery {tenant_id.hex[:8]}",
                    slug=f"suspended-{channel}-{tenant_id.hex[:16]}",
                    status="suspended",
                    tenant_kind="customer",
                ))
                setup.add(OutboxMessage(
                    id=outbox_id,
                    tenant_id=tenant_id,
                    kind="email.send" if channel == "email" else "whatsapp.send_text",
                    payload={"to": ["test@example.invalid"], "subject": "test", "body": "test"}
                    if channel == "email" else {"recipient": "+15550000000", "text": "test"},
                    status="processing",
                    attempts=1,
                ))

        if channel == "email":
            class FakeSMTP:
                def __init__(self, *args, **kwargs):
                    pass
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    return False
                def starttls(self):
                    pass
                def login(self, *args):
                    pass
                def send_message(self, message):
                    provider_calls.append(message)

            monkeypatch.setattr(email_worker, "worker_db_session", test_worker_session)
            monkeypatch.setattr(email_worker.smtplib, "SMTP", FakeSMTP)
            monkeypatch.setattr(email_worker, "get_settings", lambda: SimpleNamespace(
                smtp_host="localhost", smtp_port=25, smtp_use_starttls=False,
                smtp_username=None, smtp_password=None, smtp_from_email="test@example.invalid",
            ))
            await email_worker._send(str(outbox_id))
        else:
            async def fake_load(_db, row):
                return tenant_id, SimpleNamespace(channel_type="whatsapp", config={}), row.payload, None, uuid.uuid4(), uuid.uuid4(), None
            async def fake_deliver(**kwargs):
                provider_calls.append(kwargs)
                return SimpleNamespace(provider_message_id="should-not-send", status="accepted")
            monkeypatch.setattr(whatsapp_worker, "worker_db_session", test_worker_session)
            monkeypatch.setattr(whatsapp_worker, "_validate_and_load", fake_load)
            monkeypatch.setattr(whatsapp_worker, "deliver_text", fake_deliver)
            await whatsapp_worker._send(str(outbox_id))

        async with sessions() as check:
            row = await check.get(OutboxMessage, outbox_id)
            assert row is not None
            assert row.status == "dead"
            assert row.dead_at is not None
            assert "Tenant is not active" in (row.last_error or "")
        assert provider_calls == []
    finally:
        async with sessions() as cleanup:
            async with cleanup.begin():
                await cleanup.execute(delete(OutboxMessage).where(OutboxMessage.id == outbox_id))
                await cleanup.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await engine.dispose()


@pytest.mark.asyncio
async def test_outbound_tenant_lock_serializes_provider_window_with_suspension():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured; PostgreSQL integration test only")
    assert make_url(database_url).get_backend_name() == "postgresql"

    from app.services.tenant_access_service import assert_tenant_active_for_side_effect

    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    tenant_id = uuid.uuid4()
    suffix = uuid.uuid4().hex
    suspension_task = None
    try:
        async with sessions() as setup:
            async with setup.begin():
                setup.add(Tenant(
                    id=tenant_id,
                    name=f"Outbound lock race {suffix}",
                    slug=f"outbound-lock-race-{suffix}",
                    status="active",
                    tenant_kind="customer",
                ))

        async with sessions() as sender:
            sender_tx = await sender.begin()
            await assert_tenant_active_for_side_effect(sender, tenant_id=tenant_id)
            suspension_started = asyncio.Event()
            suspension_pid = None

            async def suspend():
                nonlocal suspension_pid
                async with sessions() as suspender:
                    async with suspender.begin():
                        suspension_pid = await suspender.scalar(text("SELECT pg_backend_pid()"))
                        suspension_started.set()
                        tenant = (await suspender.execute(
                            select(Tenant).where(Tenant.id == tenant_id).with_for_update()
                        )).scalar_one()
                        tenant.status = "suspended"

            suspension_task = asyncio.create_task(suspend())
            await asyncio.wait_for(suspension_started.wait(), timeout=5)
            await _wait_for_lock(sessions, suspension_pid)
            assert not suspension_task.done(), "suspension passed the in-flight provider lifecycle lock"
            await sender_tx.commit()
            await asyncio.wait_for(suspension_task, timeout=5)
            suspension_task = None

        async with sessions() as rejected:
            with pytest.raises(TenantInactiveError, match="Tenant is not active"):
                await assert_tenant_active_for_side_effect(rejected, tenant_id=tenant_id)
    finally:
        if suspension_task is not None and not suspension_task.done():
            suspension_task.cancel()
            await asyncio.gather(suspension_task, return_exceptions=True)
        async with sessions() as cleanup:
            async with cleanup.begin():
                await cleanup.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await engine.dispose()

@pytest.mark.asyncio
@pytest.mark.parametrize("channel", ["email", "whatsapp"])
async def test_worker_holds_tenant_lifecycle_lock_until_provider_finishes(monkeypatch, channel):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured; PostgreSQL integration test only")
    assert make_url(database_url).get_backend_name() == "postgresql"

    from app.workers import email_worker, whatsapp_worker

    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    tenant_id, outbox_id = uuid.uuid4(), uuid.uuid4()
    suffix = uuid.uuid4().hex
    provider_started = asyncio.Event()
    provider_release = asyncio.Event()
    suspender_task = None
    worker_task = None

    @asynccontextmanager
    async def test_worker_session():
        async with sessions() as session:
            yield session

    try:
        async with sessions() as setup:
            async with setup.begin():
                setup.add(Tenant(
                    id=tenant_id,
                    name=f"Provider lock {channel} {suffix}",
                    slug=f"provider-lock-{channel}-{suffix}",
                    status="active",
                    tenant_kind="customer",
                ))
                setup.add(OutboxMessage(
                    id=outbox_id,
                    tenant_id=tenant_id,
                    kind="email.send" if channel == "email" else "whatsapp.send_text",
                    payload={"to": ["test@example.invalid"], "subject": "test", "body": "test"}
                    if channel == "email" else {"recipient": "+15550000000", "text": "test"},
                    status="processing",
                    attempts=1,
                ))

        if channel == "email":
            import threading
            started = threading.Event()
            release = threading.Event()

            class BlockingSMTP:
                def __init__(self, *args, **kwargs):
                    pass
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    return False
                def starttls(self):
                    pass
                def login(self, *args):
                    pass
                def send_message(self, message):
                    started.set()
                    if not release.wait(8):
                        raise TimeoutError("test SMTP release timed out")

            monkeypatch.setattr(email_worker, "worker_db_session", test_worker_session)
            monkeypatch.setattr(email_worker.smtplib, "SMTP", BlockingSMTP)
            monkeypatch.setattr(email_worker, "get_settings", lambda: SimpleNamespace(
                smtp_host="localhost", smtp_port=25, smtp_use_starttls=False,
                smtp_username=None, smtp_password=None, smtp_from_email="test@example.invalid",
            ))
            worker_task = asyncio.create_task(asyncio.to_thread(lambda: asyncio.run(email_worker._send(str(outbox_id)))))
            assert await asyncio.to_thread(started.wait, 5), "SMTP provider boundary was not reached"
            release_provider = release.set
        else:
            async def fake_load(_db, row):
                return tenant_id, SimpleNamespace(channel_type="whatsapp", config={}), row.payload, None, uuid.uuid4(), uuid.uuid4(), None
            async def fake_deliver(**kwargs):
                provider_started.set()
                await provider_release.wait()
                return SimpleNamespace(provider_message_id="mock-provider-accepted", status="accepted")
            monkeypatch.setattr(whatsapp_worker, "worker_db_session", test_worker_session)
            monkeypatch.setattr(whatsapp_worker, "_validate_and_load", fake_load)
            monkeypatch.setattr(whatsapp_worker, "deliver_text", fake_deliver)
            worker_task = asyncio.create_task(whatsapp_worker._send(str(outbox_id)))
            await asyncio.wait_for(provider_started.wait(), timeout=5)
            release_provider = provider_release.set

        suspension_started = asyncio.Event()
        suspension_pid = None

        async def suspend_tenant():
            nonlocal suspension_pid
            async with sessions() as suspender:
                async with suspender.begin():
                    suspension_pid = await suspender.scalar(text("SELECT pg_backend_pid()"))
                    suspension_started.set()
                    tenant = (await suspender.execute(
                        select(Tenant).where(Tenant.id == tenant_id).with_for_update()
                    )).scalar_one()
                    tenant.status = "suspended"

        suspender_task = asyncio.create_task(suspend_tenant())
        await asyncio.wait_for(suspension_started.wait(), timeout=5)
        await _wait_for_lock(sessions, suspension_pid)
        assert not suspender_task.done(), "suspension passed an in-flight provider call"

        release_provider()
        await asyncio.wait_for(worker_task, timeout=8)
        await asyncio.wait_for(suspender_task, timeout=5)
        suspender_task = None

        async with sessions() as check:
            row = await check.get(OutboxMessage, outbox_id)
            tenant = await check.get(Tenant, tenant_id)
            assert row is not None and row.status == "dispatched"
            assert tenant is not None and tenant.status == "suspended"
    finally:
        if channel == "email" and 'release' in locals():
            release.set()
        provider_release.set()
        if worker_task is not None and not worker_task.done():
            worker_task.cancel()
            await asyncio.gather(worker_task, return_exceptions=True)
        if suspender_task is not None and not suspender_task.done():
            suspender_task.cancel()
            await asyncio.gather(suspender_task, return_exceptions=True)
        async with sessions() as cleanup:
            async with cleanup.begin():
                await cleanup.execute(delete(OutboxMessage).where(OutboxMessage.id == outbox_id))
                await cleanup.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await engine.dispose()
