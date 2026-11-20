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


@pytest.mark.asyncio
async def test_fastapi_request_holds_demo_grant_lock_until_endpoint_commit(monkeypatch):
    """Exercise the real FastAPI dependency cache and get_db transaction boundary."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured; PostgreSQL integration test only")
    assert make_url(database_url).get_backend_name() == "postgresql"

    import httpx
    from fastapi import FastAPI
    from app.core import database, deps
    from app.core.deps import CurrentContext, DbSession
    from app.core.security import create_access_token
    from app.models.tenant import Tenant
    from app.models.tenant_demo_grant import TenantDemoGrant
    from app.models.user import User
    from app.services import tenant_access_service

    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    monkeypatch.setattr(database, "AsyncSessionLocal", sessions)
    monkeypatch.setattr(tenant_access_service.audit_service, "record", AsyncMock())

    suffix = uuid.uuid4().hex
    tenant_id, actor_id, grant_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    endpoint_entered = asyncio.Event()
    release_endpoint = asyncio.Event()
    revoke_started = asyncio.Event()
    access_sessions = []
    endpoint_sessions = []
    revoke_pid = None

    original_tenant_has_access = tenant_access_service.tenant_has_access

    async def recording_tenant_has_access(db, *, tenant, now=None):
        access_sessions.append(db)
        return await original_tenant_has_access(db, tenant=tenant, now=now)

    monkeypatch.setattr(deps, "tenant_has_access", recording_tenant_has_access)

    app = FastAPI()

    @app.get("/protected")
    async def protected_endpoint(ctx: CurrentContext, db: DbSession):
        endpoint_sessions.append(db)
        endpoint_entered.set()
        await release_endpoint.wait()
        return {"tenant_id": str(ctx.tenant_id)}

    async def revoke_after_request_gate():
        nonlocal revoke_pid
        async with sessions() as revoker:
            async with revoker.begin():
                revoke_pid = await revoker.scalar(text("SELECT pg_backend_pid()"))
                revoke_started.set()
                await tenant_access_service.revoke_demo_grant(
                    revoker,
                    tenant_id=tenant_id,
                    grant_id=grant_id,
                    actor_id=actor_id,
                )

    revoke_task = None
    try:
        async with sessions() as setup:
            async with setup.begin():
                setup.add(
                    Tenant(
                        id=tenant_id,
                        name=f"HTTP Demo lock {suffix}",
                        slug=f"http-demo-lock-{suffix}",
                        tenant_kind="customer",
                        status="active",
                        access_grant_required=True,
                    )
                )
                await setup.flush()
                setup.add(
                    User(
                        id=actor_id,
                        tenant_id=tenant_id,
                        email=f"http-demo-lock-{suffix}@example.test",
                        password_hash="test-only-not-used",
                        full_name="HTTP Demo lock actor",
                        is_active=True,
                        is_superuser=False,
                        is_platform_admin=False,
                        auth_token_version=0,
                    )
                )
                await setup.flush()
                setup.add(
                    TenantDemoGrant(
                        id=grant_id,
                        tenant_id=tenant_id,
                        granted_by_user_id=actor_id,
                        reason="FastAPI request transaction test",
                        expires_at=datetime.now(timezone.utc) + timedelta(days=2),
                    )
                )

        token = create_access_token(actor_id, tenant_id)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            request_task = asyncio.create_task(
                client.get("/protected", headers={"Authorization": f"Bearer {token}"})
            )
            await asyncio.wait_for(endpoint_entered.wait(), timeout=5)
            assert len(access_sessions) == 1
            assert len(endpoint_sessions) == 1
            assert access_sessions[0] is endpoint_sessions[0], (
                "FastAPI must reuse the same function-scoped get_db session "
                "for the request guard and endpoint"
            )

            revoke_task = asyncio.create_task(revoke_after_request_gate())
            await asyncio.wait_for(revoke_started.wait(), timeout=5)
            await _wait_until_postgres_lock(sessions, revoke_pid)
            assert not revoke_task.done(), (
                "DemoGrant revocation passed the request's active FOR SHARE lock"
            )

            release_endpoint.set()
            response = await asyncio.wait_for(request_task, timeout=5)
            assert response.status_code == 200, response.text
            assert response.json()["tenant_id"] == str(tenant_id)
            await asyncio.wait_for(revoke_task, timeout=5)
            revoke_task = None

            denied_response = await client.get(
                "/protected", headers={"Authorization": f"Bearer {token}"}
            )
            assert denied_response.status_code == 402, denied_response.text
            assert len(access_sessions) == 2
            assert len(endpoint_sessions) == 1, (
                "the protected endpoint must not run after DemoGrant revocation"
            )
    finally:
        release_endpoint.set()
        if revoke_task is not None and not revoke_task.done():
            revoke_task.cancel()
            await asyncio.gather(revoke_task, return_exceptions=True)
        async with sessions() as cleanup:
            async with cleanup.begin():
                await cleanup.execute(
                    delete(TenantDemoGrant).where(TenantDemoGrant.tenant_id == tenant_id)
                )
                await cleanup.execute(delete(User).where(User.id == actor_id))
                await cleanup.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await engine.dispose()
