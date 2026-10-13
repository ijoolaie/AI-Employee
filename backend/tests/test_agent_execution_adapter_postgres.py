"""PostgreSQL proof that failed Agent outbox enqueue rolls back the Run row."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.tenant import Tenant
from app.services import agent_execution_adapter


@pytest.mark.asyncio
async def test_agent_adapter_outbox_failure_does_not_persist_run_postgres(monkeypatch):
    tenant_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    version_id = uuid.uuid4()
    run_id = uuid.uuid4()
    agent_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        tenant = Tenant(
            id=tenant_id,
            name="Agent Savepoint Rollback Test",
            slug=f"agent-savepoint-{uuid.uuid4().hex[:12]}",
            status="active",
        )
        employee = Employee(
            id=employee_id,
            tenant_id=tenant_id,
            slug=f"agent-savepoint-employee-{uuid.uuid4().hex[:12]}",
            name="Agent Savepoint Rollback Employee",
            kind="custom",
            is_active=True,
        )
        version = EmployeeVersion(
            id=version_id,
            employee_id=employee_id,
            version_number=1,
            is_current=True,
            input_schema={},
            output_schema={},
            prompt_template="",
            allowed_tools=[],
            rules={},
        )
        db.add_all([tenant, employee, version])
        await db.commit()

        async def authorize(*_args, **_kwargs):
            return None

        async def resolve(*_args, **_kwargs):
            return (
                SimpleNamespace(id=None),
                SimpleNamespace(id=uuid.uuid4()),
                SimpleNamespace(id=version_id, employee_id=employee_id),
            )

        async def create_run_in_database(session, **kwargs):
            run = Run(
                id=run_id,
                tenant_id=kwargs["tenant_id"],
                employee_id=kwargs["employee_id"],
                employee_version_id=kwargs["employee_version_id"],
                created_by=kwargs["created_by"],
                status="pending",
                input_data=kwargs["input_data"],
            )
            session.add(run)
            await session.flush()
            return run

        async def fail_enqueue(*_args, **_kwargs):
            raise RuntimeError("outbox unavailable")

        monkeypatch.setattr(agent_execution_adapter, "assert_authorized", authorize)
        monkeypatch.setattr(agent_execution_adapter, "resolve_employee_version", resolve)
        monkeypatch.setattr(agent_execution_adapter, "create_run", create_run_in_database)
        monkeypatch.setattr(agent_execution_adapter.outbox_service, "enqueue", fail_enqueue)

        work_item = SimpleNamespace(
            id=None,
            tenant_id=tenant_id,
            input_data={"task": "rollback-check"},
            requester_id=None,
            policy_context={},
        )
        agent = SimpleNamespace(id=agent_id, tenant_id=tenant_id, enabled=True)

        try:
            with pytest.raises(RuntimeError, match="outbox unavailable"):
                await agent_execution_adapter.AgentExecutionAdapter(db).dispatch(work_item, agent)

            # Verify using the same outer transaction after the savepoint exits.
            same_session = await db.execute(select(Run.id).where(Run.id == run_id))
            assert same_session.scalar_one_or_none() is None
            await db.commit()

            # Verify durable state from a fresh connection/session, not just ORM identity-map state.
            async with AsyncSessionLocal() as verify_db:
                persisted = await verify_db.execute(select(Run.id).where(Run.id == run_id))
                assert persisted.scalar_one_or_none() is None
        finally:
            await db.execute(delete(EmployeeVersion).where(EmployeeVersion.id == version_id))
            await db.execute(delete(Employee).where(Employee.id == employee_id))
            await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
            await db.commit()
