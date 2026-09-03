"""PostgreSQL integration coverage for Test Center isolation and row-lock races."""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.test_definition import TestDefinition
from app.models.test_run import TestRun, TestRunStatus
from app.services.test_center import TestCenterError, TestCenterService


@pytest.fixture
async def test_center_setup():
    async with AsyncSessionLocal() as db:
        tenant_a = Tenant(name="TC Tenant A", slug=f"tc-a-{uuid4().hex}", status="active")
        tenant_b = Tenant(name="TC Tenant B", slug=f"tc-b-{uuid4().hex}", status="active")
        db.add_all([tenant_a, tenant_b])
        await db.flush()

        definition_a = TestDefinition(
            tenant_id=tenant_a.id,
            code=f"smoke-{uuid4().hex}",
            name="Tenant A smoke",
            workspace_key="ops",
            enabled=True,
        )
        db.add(definition_a)
        await db.flush()
        await db.commit()

        data = {
            "tenant_a": tenant_a.id,
            "tenant_b": tenant_b.id,
            "definition_a": definition_a.id,
        }

    try:
        yield data
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(TestRun).where(TestRun.tenant_id.in_([data["tenant_a"], data["tenant_b"]])))
            await db.execute(delete(TestDefinition).where(TestDefinition.id == data["definition_a"]))
            await db.execute(delete(Tenant).where(Tenant.id.in_([data["tenant_a"], data["tenant_b"]])))
            await db.commit()


@pytest.mark.asyncio
async def test_cross_tenant_and_cross_workspace_boundaries_are_enforced(test_center_setup):
    data = test_center_setup

    async with AsyncSessionLocal() as db:
        service = TestCenterService(db)
        with pytest.raises(TestCenterError, match="test definition not found"):
            await service.create_run(
                tenant_id=data["tenant_b"],
                actor_id=None,
                test_definition_id=data["definition_a"],
                workspace_key="ops",
            )

        with pytest.raises(TestCenterError, match="workspace boundary mismatch"):
            await service.create_run(
                tenant_id=data["tenant_a"],
                actor_id=None,
                test_definition_id=data["definition_a"],
                workspace_key="finance",
            )


@pytest.mark.asyncio
async def test_concurrent_start_has_single_winner_via_postgresql_row_lock(test_center_setup):
    data = test_center_setup

    async with AsyncSessionLocal() as db:
        run = TestRun(
            tenant_id=data["tenant_a"],
            test_definition_id=data["definition_a"],
            workspace_key="ops",
            status=TestRunStatus.QUEUED,
            executor_type="backend",
            fixtures={},
            evidence={},
        )
        db.add(run)
        await db.commit()
        run_id = run.id

    first_started = asyncio.Event()

    async def first_worker():
        async with AsyncSessionLocal() as db:
            started = await TestCenterService(db).start_run(
                run_id=run_id, tenant_id=data["tenant_a"]
            )
            assert started.status is TestRunStatus.RUNNING
            first_started.set()
            await asyncio.sleep(0.2)
            await db.commit()

    async def second_worker():
        await first_started.wait()
        async with AsyncSessionLocal() as db:
            with pytest.raises(TestCenterError, match="only queued"):
                await TestCenterService(db).start_run(
                    run_id=run_id, tenant_id=data["tenant_a"]
                )
            await db.rollback()

    await asyncio.gather(first_worker(), second_worker())

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TestRun).where(TestRun.id == run_id))
        persisted = result.scalar_one()
        assert persisted.status is TestRunStatus.RUNNING
        assert persisted.started_at is not None


@pytest.mark.asyncio
async def test_expired_transition_is_persisted_and_blocks_finish(test_center_setup):
    data = test_center_setup
    queued_at = datetime.now(timezone.utc) - timedelta(minutes=10)

    async with AsyncSessionLocal() as db:
        run = TestRun(
            tenant_id=data["tenant_a"],
            test_definition_id=data["definition_a"],
            workspace_key="ops",
            status=TestRunStatus.QUEUED,
            executor_type="backend",
            fixtures={},
            evidence={},
            queued_at=queued_at,
        )
        db.add(run)
        await db.flush()
        run_id = run.id
        await db.commit()

    async with AsyncSessionLocal() as db:
        expired = await TestCenterService(db).expire_run(
            run_id=run_id,
            tenant_id=data["tenant_a"],
            timeout_seconds=60,
            now=datetime.now(timezone.utc),
        )
        assert expired.status is TestRunStatus.EXPIRED
        await db.commit()

    async with AsyncSessionLocal() as db:
        with pytest.raises(TestCenterError, match="only running"):
            await TestCenterService(db).finish_run(
                run_id=run_id,
                tenant_id=data["tenant_a"],
                passed=True,
            )
