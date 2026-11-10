"""PostgreSQL race coverage for paid subscription admission and lifecycle updates."""

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

from app.core.exceptions import ConflictError


async def _wait_for_lock(session_factory, pid: int) -> None:
    deadline = asyncio.get_running_loop().time() + 5
    async with session_factory() as observer:
        while asyncio.get_running_loop().time() < deadline:
            state = (
                await observer.execute(
                    text("SELECT wait_event_type FROM pg_stat_activity WHERE pid = :pid"),
                    {"pid": pid},
                )
            ).scalar_one_or_none()
            if state == "Lock":
                return
            await asyncio.sleep(0.02)
    raise AssertionError(f"PostgreSQL backend {pid} did not wait for a row lock")


@pytest.mark.asyncio
async def test_paid_run_admission_serializes_with_subscription_revocation(monkeypatch):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured; PostgreSQL integration test only")
    assert make_url(database_url).get_backend_name() == "postgresql"

    from app.models.billing import BillingPlan, Subscription
    from app.models.tenant import Tenant
    from app.services import billing_service

    monkeypatch.setattr(
        billing_service.license_service,
        "assert_execution_license",
        AsyncMock(return_value=object()),
    )
    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex
    tenant_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    subscription_id = uuid.uuid4()

    try:
        async with sessions() as setup:
            async with setup.begin():
                setup.add(
                    Tenant(
                        id=tenant_id,
                        name=f"Paid subscription race {suffix}",
                        slug=f"paid-subscription-race-{suffix}",
                        tenant_kind="customer",
                        status="active",
                        access_grant_required=True,
                    )
                )
                setup.add(
                    BillingPlan(
                        id=plan_id,
                        code=f"race-{suffix[:12]}",
                        name="Race test plan",
                        monthly_price_usd=49,
                        monthly_runs=100,
                        monthly_tokens=100_000,
                        max_employees=3,
                        max_workflows=3,
                        features={},
                        is_active=True,
                    )
                )
                await setup.flush()
                setup.add(
                    Subscription(
                        id=subscription_id,
                        tenant_id=tenant_id,
                        plan_id=plan_id,
                        status="active",
                        provider="stripe",
                        current_period_start=datetime.now(timezone.utc) - timedelta(days=1),
                        current_period_end=datetime.now(timezone.utc) + timedelta(days=20),
                        cancel_at_period_end=False,
                    )
                )

        # Admission owns the subscription FOR UPDATE lock first. A lifecycle
        # update must wait until the run-admission transaction commits.
        update_started = asyncio.Event()
        updater_pid = None

        async def update_after_admission():
            nonlocal updater_pid
            async with sessions() as updater:
                async with updater.begin():
                    updater_pid = await updater.scalar(text("SELECT pg_backend_pid()"))
                    update_started.set()
                    sub = await billing_service.ensure_subscription(updater, tenant_id=tenant_id)
                    sub.status = "canceled"
                    sub.canceled_at = datetime.now(timezone.utc)

        async with sessions() as admission:
            tx = await admission.begin()
            await billing_service.assert_run_execution_entitlement(admission, tenant_id=tenant_id)
            update_task = asyncio.create_task(update_after_admission())
            try:
                await asyncio.wait_for(update_started.wait(), timeout=5)
                await _wait_for_lock(sessions, updater_pid)
                assert not update_task.done(), "subscription update passed active admission lock"
                await tx.commit()
                await asyncio.wait_for(update_task, timeout=5)
            finally:
                if not update_task.done():
                    await admission.rollback()
                    update_task.cancel()
                    await asyncio.gather(update_task, return_exceptions=True)

        # Lifecycle update owns FOR UPDATE first. The paid-source snapshot may
        # see the old committed row, but get_subscription must wait and then
        # reject the newly committed canceled state.
        async with sessions() as reset:
            async with reset.begin():
                sub = await billing_service.ensure_subscription(reset, tenant_id=tenant_id)
                sub.status = "active"
                sub.canceled_at = None

        async with sessions() as updater:
            update_tx = await updater.begin()
            sub = await billing_service.ensure_subscription(updater, tenant_id=tenant_id)
            sub.status = "canceled"
            sub.canceled_at = datetime.now(timezone.utc)
            await updater.flush()
            update_started = asyncio.Event()
            admission_pid = None

            async def admission_after_update():
                nonlocal admission_pid
                async with sessions() as admission:
                    async with admission.begin():
                        admission_pid = await admission.scalar(text("SELECT pg_backend_pid()"))
                        update_started.set()
                        await billing_service.assert_run_execution_entitlement(
                            admission, tenant_id=tenant_id
                        )

            admission_task = asyncio.create_task(admission_after_update())
            try:
                await asyncio.wait_for(update_started.wait(), timeout=5)
                await _wait_for_lock(sessions, admission_pid)
                assert not admission_task.done(), "admission did not wait for lifecycle update"
                sub.status = "canceled"
                sub.canceled_at = datetime.now(timezone.utc)
                await update_tx.commit()
                with pytest.raises(ConflictError, match="Subscription is not active"):
                    await asyncio.wait_for(admission_task, timeout=5)
            finally:
                if not admission_task.done():
                    await updater.rollback()
                    admission_task.cancel()
                    await asyncio.gather(admission_task, return_exceptions=True)

    finally:
        async with sessions() as cleanup:
            async with cleanup.begin():
                await cleanup.execute(
                    delete(Subscription).where(Subscription.tenant_id == tenant_id)
                )
                await cleanup.execute(delete(Tenant).where(Tenant.id == tenant_id))
                await cleanup.execute(delete(BillingPlan).where(BillingPlan.id == plan_id))
        await engine.dispose()
