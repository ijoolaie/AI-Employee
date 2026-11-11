"""PostgreSQL regression for run-admission locks and durable AI-call FK inserts."""

import asyncio
import os
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


async def _wait_for_lock(session_factory, pid: int) -> None:
    deadline = asyncio.get_running_loop().time() + 5
    async with session_factory() as observer:
        while asyncio.get_running_loop().time() < deadline:
            wait_type = await observer.scalar(
                text("SELECT wait_event_type FROM pg_stat_activity WHERE pid = :pid"),
                {"pid": pid},
            )
            if wait_type == "Lock":
                return
            await asyncio.sleep(0.02)
    raise AssertionError(f"PostgreSQL backend {pid} did not wait for tenant lifecycle lock")


@pytest.mark.parametrize("tenant_kind", ["vendor", "customer"])
@pytest.mark.asyncio
async def test_run_admission_allows_durable_fk_insert_and_serializes_suspension(tenant_kind, monkeypatch):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured; PostgreSQL integration test only")
    assert make_url(database_url).get_backend_name() == "postgresql"

    from app.core.exceptions import ConflictError
    from app.models.ai_provider_call import AIProviderCall
    from app.models.tenant import Tenant
    from app.services import billing_service

    if tenant_kind == "customer":
        monkeypatch.setattr(
            billing_service, "_require_tenant_access_source", AsyncMock(return_value="legacy")
        )
        monkeypatch.setattr(
            billing_service.license_service, "assert_execution_license", AsyncMock()
        )
        monkeypatch.setattr(
            billing_service, "get_subscription", AsyncMock(return_value=SimpleNamespace(status="active"))
        )
        monkeypatch.setattr(
            billing_service, "_revalidate_tenant_access_after_subscription_lock", AsyncMock()
        )

    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex
    tenant_id = uuid.uuid4()
    call_id = uuid.uuid4()
    admission = None
    suspension_task = None

    try:
        async with sessions() as setup:
            async with setup.begin():
                setup.add(Tenant(
                    id=tenant_id,
                    name=f"Run admission FK lock regression {suffix}",
                    slug=f"run-fk-lock-{suffix[:20]}",
                    tenant_kind=tenant_kind,
                    status="active",
                ))

        # The worker keeps this transaction open across AgentRuntime execution.
        admission = sessions()
        await admission.begin()
        await billing_service.assert_run_execution_entitlement(admission, tenant_id=tenant_id)

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

        suspension_task = asyncio.create_task(suspend_tenant())
        await asyncio.wait_for(suspension_started.wait(), timeout=5)
        await _wait_for_lock(sessions, suspension_pid)
        assert not suspension_task.done(), "suspension passed the active run-admission fence"

        # Mirrors AIGateway._prepare_durable_call(): another session inserts a
        # row whose tenant_id FK must acquire KEY SHARE on the tenant row.
        async with sessions() as durable:
            async with durable.begin():
                durable.add(AIProviderCall(
                    id=call_id,
                    tenant_id=tenant_id,
                    run_id=None,
                    provider="test-provider",
                    model="test-model",
                    status="in_flight",
                ))
                await asyncio.wait_for(durable.flush(), timeout=5)

        assert not suspension_task.done(), "suspension must wait for active run transaction"
        await admission.commit()
        await asyncio.wait_for(suspension_task, timeout=5)
        suspension_task = None

        async with sessions() as check:
            tenant = await check.get(Tenant, tenant_id)
            call = await check.get(AIProviderCall, call_id)
            assert tenant is not None and tenant.status == "suspended"
            assert call is not None and call.tenant_id == tenant_id

        # Once suspension commits, a new admission must fail closed.
        async with sessions() as denied:
            async with denied.begin():
                with pytest.raises(ConflictError, match="Tenant is not active"):
                    await billing_service.assert_run_execution_entitlement(
                        denied, tenant_id=tenant_id
                    )
    finally:
        if admission is not None:
            if admission.in_transaction():
                await admission.rollback()
            await admission.close()
        if suspension_task is not None and not suspension_task.done():
            suspension_task.cancel()
            await asyncio.gather(suspension_task, return_exceptions=True)
        async with sessions() as cleanup:
            async with cleanup.begin():
                await cleanup.execute(
                    text("DELETE FROM ai_provider_calls WHERE id = :call_id"),
                    {"call_id": call_id},
                )
                await cleanup.execute(
                    text("DELETE FROM tenants WHERE id = :tenant_id"),
                    {"tenant_id": tenant_id},
                )
        await engine.dispose()
