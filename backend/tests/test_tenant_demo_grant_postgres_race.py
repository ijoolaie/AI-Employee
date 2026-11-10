"""PostgreSQL race coverage for Demo grant authorization and revocation."""

import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import delete, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


async def _wait_until_postgres_lock(session_factory, pid: int) -> None:
    deadline = asyncio.get_running_loop().time() + 5
    async with session_factory() as observer:
        while asyncio.get_running_loop().time() < deadline:
            row = await observer.execute(
                text("SELECT wait_event_type, wait_event FROM pg_stat_activity WHERE pid = :pid"),
                {"pid": pid},
            )
            state = row.one_or_none()
            if state is not None and state.wait_event_type == "Lock":
                return
            await asyncio.sleep(0.02)
    raise AssertionError(f"PostgreSQL backend {pid} did not enter a lock wait")


@pytest.mark.asyncio
async def test_demo_grant_authorization_and_revocation_serialize_across_sessions(monkeypatch):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured; PostgreSQL integration test only")
    assert make_url(database_url).get_backend_name() == "postgresql"

    from app.models.tenant import Tenant
    from app.models.tenant_demo_grant import TenantDemoGrant
    from app.models.user import User
    from app.services import tenant_access_service

    monkeypatch.setattr(tenant_access_service.audit_service, "record", AsyncMock())
    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    grant_admission_first_id = uuid.uuid4()
    grant_revoke_first_id = uuid.uuid4()

    try:
        async with sessions() as setup:
            async with setup.begin():
                tenant = Tenant(
                    id=tenant_id,
                    name=f"Demo grant race {suffix}",
                    slug=f"demo-grant-race-{suffix}",
                    tenant_kind="customer",
                    status="active",
                    access_grant_required=True,
                )
                setup.add(tenant)
                await setup.flush()
                actor = User(
                    id=actor_id,
                    tenant_id=tenant_id,
                    email=f"demo-grant-race-{suffix}@example.test",
                    password_hash="test-only-not-used",
                    full_name="Demo grant race actor",
                    is_active=True,
                    is_superuser=False,
                    is_platform_admin=False,
                    auth_token_version=0,
                )
                setup.add(actor)
                await setup.flush()
                setup.add_all(
                    [
                        TenantDemoGrant(
                            id=grant_admission_first_id,
                            tenant_id=tenant_id,
                            granted_by_user_id=actor_id,
                            reason="PostgreSQL concurrency test",
                            expires_at=datetime.now(timezone.utc) + timedelta(days=2),
                        ),
                        TenantDemoGrant(
                            id=grant_revoke_first_id,
                            tenant_id=tenant_id,
                            granted_by_user_id=actor_id,
                            reason="PostgreSQL concurrency test",
                            expires_at=datetime.now(timezone.utc) + timedelta(days=2),
                        ),
                    ]
                )

        # Admission gets FOR SHARE first: revocation must wait until the
        # authorization transaction ends.
        revoke_started = asyncio.Event()
        revoke_pid = None

        async def revoke_after_admission_lock():
            nonlocal revoke_pid
            async with sessions() as revoker:
                async with revoker.begin():
                    revoke_pid = await revoker.scalar(text("SELECT pg_backend_pid()"))
                    revoke_started.set()
                    await tenant_access_service.revoke_demo_grant(
                        revoker,
                        tenant_id=tenant_id,
                        grant_id=grant_admission_first_id,
                        actor_id=actor_id,
                    )

        async with sessions() as admission:
            transaction = await admission.begin()
            tenant = await admission.get(Tenant, tenant_id)
            assert (
                await tenant_access_service.tenant_access_source(admission, tenant=tenant) == "demo"
            )
            revoke_task = asyncio.create_task(revoke_after_admission_lock())
            try:
                await asyncio.wait_for(revoke_started.wait(), timeout=5)
                await _wait_until_postgres_lock(sessions, revoke_pid)
                assert not revoke_task.done(), "revocation passed an active authorization lock"
                await transaction.commit()
                await asyncio.wait_for(revoke_task, timeout=5)
            finally:
                if not revoke_task.done():
                    await admission.rollback()
                    revoke_task.cancel()
                    await asyncio.gather(revoke_task, return_exceptions=True)

        # Revocation gets FOR UPDATE first: authorization waits, rechecks
        # revoked_at under READ COMMITTED, and denies access.
        async with sessions() as revoker:
            revoke_tx = await revoker.begin()
            await tenant_access_service.revoke_demo_grant(
                revoker,
                tenant_id=tenant_id,
                grant_id=grant_revoke_first_id,
                actor_id=actor_id,
            )
            auth_started = asyncio.Event()
            auth_pid = None

            async def authorize_after_revoke_lock():
                nonlocal auth_pid
                async with sessions() as admission:
                    async with admission.begin():
                        auth_pid = await admission.scalar(text("SELECT pg_backend_pid()"))
                        auth_started.set()
                        tenant = await admission.get(Tenant, tenant_id)
                        return await tenant_access_service.tenant_access_source(
                            admission, tenant=tenant
                        )

            auth_task = asyncio.create_task(authorize_after_revoke_lock())
            try:
                await asyncio.wait_for(auth_started.wait(), timeout=5)
                await _wait_until_postgres_lock(sessions, auth_pid)
                assert not auth_task.done(), "authorization did not wait for in-flight revocation"
                await revoke_tx.commit()
                result = await asyncio.wait_for(auth_task, timeout=5)
                assert result is None, (
                    "authorization accepted a Demo grant after revocation committed"
                )
            finally:
                if not auth_task.done():
                    await revoker.rollback()
                    auth_task.cancel()
                    await asyncio.gather(auth_task, return_exceptions=True)

    finally:
        async with sessions() as cleanup:
            async with cleanup.begin():
                await cleanup.execute(
                    delete(TenantDemoGrant).where(TenantDemoGrant.tenant_id == tenant_id)
                )
                await cleanup.execute(delete(User).where(User.id == actor_id))
                await cleanup.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await engine.dispose()
