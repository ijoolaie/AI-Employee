from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def _support_test_url() -> str:
    url = os.getenv("SUPPORT_TEST_DATABASE_URL") or os.getenv("DATABASE_URL", "")
    if not url:
        pytest.skip("dedicated support_test PostgreSQL database is not configured")
    parsed = make_url(url)
    local_host = parsed.host in {"localhost", "127.0.0.1"}
    local_test = parsed.username == "support_test_user" and parsed.port == 15433 and bool(parsed.password)
    ci_test = os.getenv("CI", "").lower() == "true" and parsed.username == "aiep" and parsed.port == 5432 and parsed.password == "aiep"
    if parsed.drivername != "postgresql+asyncpg" or not local_host or parsed.database != "support_test" or not (local_test or ci_test):
        raise RuntimeError("URL must target the dedicated isolated support_test database; refusing to run")
    return url


@pytest.mark.asyncio
async def test_stale_run_sweep_recovers_multiple_tenants_with_tenant_bound_audit(monkeypatch):
    db_url = _support_test_url()
    from app.models.audit_log import AuditLog
    from app.models.employee import Employee, EmployeeVersion
    from app.models.run import Run
    from app.models.tenant import Tenant
    from app.workers import run_recovery_worker

    engine = create_async_engine(db_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    tenant_ids = [uuid.uuid4(), uuid.uuid4()]
    run_ids = [uuid.uuid4(), uuid.uuid4()]
    now = datetime.now(timezone.utc)

    try:
        async with sessions() as setup:
            async with setup.begin():
                for index, (tenant_id, run_id) in enumerate(zip(tenant_ids, run_ids, strict=True)):
                    tenant = Tenant(
                        id=tenant_id,
                        name=f"Recovery sweep tenant {index} {uuid.uuid4().hex[:8]}",
                        slug=f"recovery-sweep-{index}-{uuid.uuid4().hex[:12]}",
                        tenant_kind="customer",
                        status="active",
                        access_grant_required=True,
                    )
                    setup.add(tenant)
                    await setup.flush()
                    employee = Employee(
                        tenant_id=tenant_id,
                        slug=f"recovery-{uuid.uuid4().hex[:12]}",
                        name=f"Recovery employee {index}",
                        kind="custom",
                        is_active=True,
                    )
                    setup.add(employee)
                    await setup.flush()
                    version = EmployeeVersion(
                        employee_id=employee.id,
                        version_number=1,
                        is_current=True,
                        input_schema={},
                        output_schema={},
                        prompt_template="",
                        allowed_tools=[],
                        rules={},
                    )
                    setup.add(version)
                    await setup.flush()
                    setup.add(
                        Run(
                            id=run_id,
                            tenant_id=tenant_id,
                            employee_id=employee.id,
                            employee_version_id=version.id,
                            status="running",
                            input_data={},
                            started_at=now - timedelta(hours=1),
                        )
                    )

        @asynccontextmanager
        async def worker_session():
            async with sessions() as session:
                yield session

        monkeypatch.setattr(run_recovery_worker, "worker_db_session", worker_session)
        recovered = await run_recovery_worker._recover_stale_runs_async()
        assert recovered == 2

        async with sessions() as verify:
            runs = (await verify.execute(select(Run).where(Run.id.in_(run_ids)))).scalars().all()
            assert {run.id for run in runs if run.status == "failed"} == set(run_ids)
            audits = (
                await verify.execute(
                    select(AuditLog).where(
                        AuditLog.action == "run.execution_recovered",
                        AuditLog.resource_id.in_([str(run_id) for run_id in run_ids]),
                    )
                )
            ).scalars().all()
            assert {(entry.tenant_id, entry.resource_id) for entry in audits} == {
                (tenant_id, str(run_id)) for tenant_id, run_id in zip(tenant_ids, run_ids, strict=True)
            }
    finally:
        await engine.dispose()
