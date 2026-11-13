"""PostgreSQL race coverage for paid subscription admission and lifecycle updates."""

import asyncio
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import delete, select, text
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

    from app.core.database import worker_db_session
    from app.models.ai_provider_call import AIProviderCall
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

        # Exercise the actual Celery worker session factory. _run_async commits
        # only after AgentRuntime.execute() returns, retaining this lock across runtime.
        async with worker_db_session() as admission:
            tx = await admission.begin()
            await billing_service.assert_run_execution_entitlement(admission, tenant_id=tenant_id)

            # The worker retains this Tenant lock while AIGateway writes its durable
            # AIProviderCall through an independent session. The tenant FK check must
            # not block behind the admission lock.
            async def write_durable_provider_call():
                async with sessions() as durable:
                    async with durable.begin():
                        durable.add(
                            AIProviderCall(
                                tenant_id=tenant_id,
                                run_id=None,
                                provider="lock-probe",
                                model="lock-probe",
                                status="success",
                            )
                        )

            await asyncio.wait_for(write_durable_provider_call(), timeout=2)
            update_task = asyncio.create_task(update_after_admission())
            try:
                await asyncio.wait_for(update_started.wait(), timeout=5)
                await _wait_for_lock(sessions, updater_pid)
                assert not update_task.done(), (
                    "subscription update passed active worker admission lock"
                )
                await tx.commit()
                await asyncio.wait_for(update_task, timeout=5)
            finally:
                if not update_task.done():
                    await admission.rollback()
                    update_task.cancel()
                    await asyncio.gather(update_task, return_exceptions=True)

        # Lifecycle update owns FOR UPDATE first. The paid-source snapshot may
        # see the old committed period end, but the post-lock entitlement check
        # must re-read the period and reject after the expiry update commits.
        async with sessions() as reset:
            async with reset.begin():
                sub = await billing_service.ensure_subscription(reset, tenant_id=tenant_id)
                sub.status = "active"
                sub.canceled_at = None

        async with sessions() as updater:
            update_tx = await updater.begin()
            sub = await billing_service.ensure_subscription(updater, tenant_id=tenant_id)
            sub.current_period_end = datetime.now(timezone.utc) - timedelta(days=1)
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
                sub.current_period_end = datetime.now(timezone.utc) - timedelta(days=1)
                await update_tx.commit()
                with pytest.raises(ConflictError, match="Tenant access requires"):
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
                    delete(AIProviderCall).where(AIProviderCall.tenant_id == tenant_id)
                )
                await cleanup.execute(
                    delete(Subscription).where(Subscription.tenant_id == tenant_id)
                )
                await cleanup.execute(delete(Tenant).where(Tenant.id == tenant_id))
                await cleanup.execute(delete(BillingPlan).where(BillingPlan.id == plan_id))
        await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_type",
    [
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.payment_failed",
    ],
)
async def test_stripe_subscription_webhook_serializes_with_paid_run_admission(
    monkeypatch, event_type
):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured; PostgreSQL integration test only")
    assert make_url(database_url).get_backend_name() == "postgresql"

    from app.models.billing import BillingPlan, Subscription
    from app.models.tenant import Tenant
    from app.services import billing_service, stripe_service

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
    provider_subscription_id = f"sub_race_{suffix}"

    try:
        async with sessions() as setup:
            async with setup.begin():
                setup.add(
                    Tenant(
                        id=tenant_id,
                        name=f"Stripe webhook race {suffix}",
                        slug=f"stripe-webhook-race-{suffix}",
                        tenant_kind="customer",
                        status="active",
                        access_grant_required=True,
                    )
                )
                setup.add(
                    BillingPlan(
                        id=plan_id,
                        code=f"stripe-race-{suffix[:12]}",
                        name="Stripe webhook race plan",
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
                        provider_subscription_id=provider_subscription_id,
                        current_period_start=datetime.now(timezone.utc) - timedelta(days=1),
                        current_period_end=datetime.now(timezone.utc) + timedelta(days=20),
                        cancel_at_period_end=False,
                    )
                )

        webhook_pid = None
        async with sessions() as webhook_db:
            webhook_tx = await webhook_db.begin()
            webhook_pid = await webhook_db.scalar(text("SELECT pg_backend_pid()"))
            if event_type == "customer.subscription.updated":
                event_object = {
                    "id": provider_subscription_id,
                    "object": "subscription",
                    "status": "past_due",
                    "metadata": {"tenant_id": str(tenant_id)},
                    "customer": f"cus_race_{suffix}",
                    "items": {"data": []},
                    "current_period_start": int(
                        (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
                    ),
                    "current_period_end": int(
                        (datetime.now(timezone.utc) + timedelta(days=20)).timestamp()
                    ),
                }
            elif event_type == "customer.subscription.deleted":
                event_object = {
                    "id": provider_subscription_id,
                    "object": "subscription",
                    "status": "canceled",
                }
            else:
                event_object = {
                    "id": f"in_race_{suffix}",
                    "object": "invoice",
                    "subscription": provider_subscription_id,
                    "status": "open",
                }
            event = {
                "id": f"evt_race_{suffix}_{event_type.replace('.', '_')}",
                "type": event_type,
                "created": int(time.time()) + 10,
                "data": {"object": event_object},
            }
            result = await stripe_service.apply_webhook_event(webhook_db, event)
            assert result["stale"] is False

            admission_started = asyncio.Event()
            admission_pid = None

            async def admit_after_webhook_lock():
                nonlocal admission_pid
                async with sessions() as admission:
                    async with admission.begin():
                        admission_pid = await admission.scalar(text("SELECT pg_backend_pid()"))
                        admission_started.set()
                        await billing_service.assert_run_execution_entitlement(
                            admission, tenant_id=tenant_id
                        )

            admission_task = asyncio.create_task(admit_after_webhook_lock())
            try:
                await asyncio.wait_for(admission_started.wait(), timeout=5)
                await _wait_for_lock(sessions, admission_pid)
                assert not admission_task.done(), (
                    "admission passed Stripe webhook Subscription lock"
                )
                await webhook_tx.commit()
                with pytest.raises(ConflictError, match="Tenant access requires"):
                    await asyncio.wait_for(admission_task, timeout=5)
            finally:
                if not admission_task.done():
                    await webhook_db.rollback()
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


@pytest.mark.asyncio
async def test_run_admission_serializes_with_tenant_suspension():
    """A suspension waits for an admitted Run; later admissions fail closed."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured; PostgreSQL integration test only")
    assert make_url(database_url).get_backend_name() == "postgresql"

    from app.models.ai_provider_call import AIProviderCall
    from app.models.tenant import Tenant
    from app.services import billing_service

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
                    name=f"Tenant suspension race {suffix}",
                    slug=f"tenant-suspension-race-{suffix}",
                    tenant_kind="vendor",
                    status="active",
                    access_grant_required=False,
                ))

        async with sessions() as admission:
            admission_tx = await admission.begin()
            await billing_service.assert_run_execution_entitlement(
                admission, tenant_id=tenant_id
            )

            # The durable AI-call transaction must pass its tenant FK check while
            # admission holds the Tenant lock; suspension must still wait below.
            async with sessions() as durable:
                async with durable.begin():
                    durable.add(
                        AIProviderCall(
                            tenant_id=tenant_id,
                            run_id=None,
                            provider="lock-probe",
                            model="lock-probe",
                            status="success",
                        )
                    )
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
            assert not suspension_task.done(), "tenant suspension passed active Run admission lock"
            await admission_tx.commit()
            await asyncio.wait_for(suspension_task, timeout=5)
            suspension_task = None

        async with sessions() as rejected:
            with pytest.raises(ConflictError, match="Tenant is not active"):
                await billing_service.assert_run_execution_entitlement(
                    rejected, tenant_id=tenant_id
                )
    finally:
        if suspension_task is not None and not suspension_task.done():
            suspension_task.cancel()
            await asyncio.gather(suspension_task, return_exceptions=True)
        async with sessions() as cleanup:
            async with cleanup.begin():
                await cleanup.execute(
                    delete(AIProviderCall).where(AIProviderCall.tenant_id == tenant_id)
                )
                await cleanup.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await engine.dispose()
