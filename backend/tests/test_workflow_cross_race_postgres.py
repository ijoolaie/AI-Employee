"""Real PostgreSQL runtime coverage for workflow cross-race admission."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.tenant import Tenant
from app.models.workflow import Workflow, WorkflowRun, WorkflowStepRun, WorkflowVersion
from app.services import workflow_service


@pytest_asyncio.fixture
async def workflow_cross_race_setup(monkeypatch):
    async def record(*_args, **_kwargs):
        return None

    monkeypatch.setattr(workflow_service.audit_service, "record", record)

    async with AsyncSessionLocal() as db:
        tenant = Tenant(
            name="Workflow Cross-Race Runtime Test",
            slug=f"workflow-cross-race-{uuid.uuid4().hex[:12]}",
            status="active",
        )
        db.add(tenant)
        await db.flush()

        employee = Employee(
            tenant_id=tenant.id,
            slug=f"workflow-cross-race-employee-{uuid.uuid4().hex[:8]}",
            name="Workflow Cross-Race Employee",
            kind="custom",
            is_active=True,
        )
        db.add(employee)
        await db.flush()

        employee_version = EmployeeVersion(
            employee_id=employee.id,
            version_number=1,
            is_current=True,
            input_schema={},
            output_schema={},
            prompt_template="",
            allowed_tools=[],
            rules={},
        )
        db.add(employee_version)
        await db.flush()

        workflow = Workflow(
            tenant_id=tenant.id,
            slug=f"workflow-cross-race-{uuid.uuid4().hex[:8]}",
            name="Workflow Cross-Race Runtime",
            created_by=None,
        )
        db.add(workflow)
        await db.flush()

        definition = {
            "key": "child",
            "type": "employee",
            "employee_id": str(employee.id),
            "employee_version_id": str(employee_version.id),
        }
        version = WorkflowVersion(
            workflow_id=workflow.id,
            version_number=1,
            is_current=True,
            trigger_type="manual",
            config={"steps": [definition]},
            execution_contract={
                "schema_version": 1,
                "legacy": False,
                "workflow_version_number": 1,
                "steps": [definition],
                "max_runtime_seconds": 300,
            },
            content_hash="runtime-cross-race-test",
            created_by=None,
        )
        db.add(version)
        await db.flush()

        run = WorkflowRun(
            tenant_id=tenant.id,
            workflow_id=workflow.id,
            workflow_version_id=version.id,
            created_by=None,
            status="running",
            context={
                "input": {"value": "race"},
                "steps": {},
                "_workflow": {
                    "next_position": 0,
                    "execution_contract": version.execution_contract,
                },
            },
            deadline_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db.add(run)
        await db.commit()

        data = {
            "tenant_id": tenant.id,
            "employee_id": employee.id,
            "employee_version_id": employee_version.id,
            "workflow_id": workflow.id,
            "workflow_version_id": version.id,
            "workflow_run_id": run.id,
        }

    yield data

    async with AsyncSessionLocal() as db:
        await db.execute(delete(Run).where(Run.tenant_id == data["tenant_id"]))
        await db.execute(
            delete(WorkflowStepRun).where(
                WorkflowStepRun.workflow_run_id == data["workflow_run_id"]
            )
        )
        await db.execute(
            delete(WorkflowRun).where(WorkflowRun.id == data["workflow_run_id"])
        )
        await db.execute(
            delete(WorkflowVersion).where(
                WorkflowVersion.id == data["workflow_version_id"]
            )
        )
        await db.execute(delete(Workflow).where(Workflow.id == data["workflow_id"]))
        await db.execute(
            delete(EmployeeVersion).where(
                EmployeeVersion.id == data["employee_version_id"]
            )
        )
        await db.execute(
            delete(Employee).where(Employee.id == data["employee_id"])
        )
        await db.execute(delete(Tenant).where(Tenant.id == data["tenant_id"]))
        await db.commit()


@pytest.mark.asyncio
async def test_timeout_between_child_commit_and_execution_fence_cancels_pending_child(
    workflow_cross_race_setup, monkeypatch
):
    data = workflow_cross_race_setup
    lease_id = uuid.uuid4()

    async def acquire(_db, **_kwargs):
        return lease_id

    async def assert_lease(db, *, workflow_run_id, lease_id, **_kwargs):
        return await db.get(WorkflowRun, workflow_run_id)

    async def heartbeat(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        workflow_service,
        "acquire_workflow_execution_lease",
        acquire,
    )
    monkeypatch.setattr(
        workflow_service,
        "assert_workflow_execution_lease",
        assert_lease,
    )
    monkeypatch.setattr(
        workflow_service,
        "heartbeat_workflow_execution_lease",
        heartbeat,
    )

    async def create_run(
        db,
        *,
        tenant_id,
        employee_id,
        input_data,
        created_by,
        employee_version_id=None,
        agent_instance_id=None,
    ):
        child = Run(
            tenant_id=tenant_id,
            employee_id=employee_id,
            employee_version_id=employee_version_id or data["employee_version_id"],
            agent_instance_id=agent_instance_id,
            created_by=created_by,
            status="pending",
            input_data=input_data,
        )
        db.add(child)
        await db.flush()
        return child

    async def execute_child(*_args, **_kwargs):
        raise AssertionError("child execution crossed the side-effect boundary")

    monkeypatch.setattr(workflow_service.run_service, "create_run", create_run)
    monkeypatch.setattr(workflow_service.run_service, "execute_run", execute_child)

    async with AsyncSessionLocal() as db:
        original_commit = db.commit
        timeout_injected = False

        async def commit_and_timeout():
            nonlocal timeout_injected
            await original_commit()
            if timeout_injected:
                return
            timeout_injected = True
            async with AsyncSessionLocal() as racing_db:
                parent = await racing_db.get(WorkflowRun, data["workflow_run_id"])
                assert parent is not None
                parent.status = "timed_out"
                parent.error = {
                    "code": "WORKFLOW_TIMEOUT",
                    "message": "Injected deterministic cross-race timeout",
                }
                parent.completed_at = datetime.now(timezone.utc)
                await racing_db.commit()

        monkeypatch.setattr(db, "commit", commit_and_timeout)

        result = await workflow_service.execute_workflow(
            db,
            workflow_run_id=data["workflow_run_id"],
            execution_lease_id=lease_id,
        )
        await db.commit()

        assert result.status == "timed_out"

    async with AsyncSessionLocal() as db:
        parent = await db.get(WorkflowRun, data["workflow_run_id"])
        child = (
            await db.execute(
                select(Run).where(
                    Run.tenant_id == data["tenant_id"],
                    Run.workflow_step_run_id.is_not(None),
                )
            )
        ).scalars().all()

        assert parent is not None
        assert parent.status == "timed_out"
        assert len(child) == 1
        assert child[0].status == "cancelled"
        assert child[0].completed_at is not None
        assert "became terminal before child execution" in (child[0].error_message or "")
