"""Real PostgreSQL runtime coverage for workflow cross-race admission."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.agent_definition import AgentDefinition
from app.models.agent_instance import AgentInstance
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.tenant import Tenant
from app.models.workflow import Workflow, WorkflowParallelBranchRun, WorkflowRun, WorkflowStepRun, WorkflowVersion
from app.services import workflow_execution_lease, workflow_service


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

        agent_definition = AgentDefinition(
            tenant_id=tenant.id,
            slug=f"workflow-cross-race-agent-{uuid.uuid4().hex[:8]}",
            name="Workflow Cross-Race Agent",
        )
        db.add(agent_definition)
        await db.flush()

        agent_instance = AgentInstance(
            tenant_id=tenant.id,
            agent_definition_id=agent_definition.id,
            name="Workflow Cross-Race Agent Instance",
        )
        db.add(agent_instance)
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
            agent_instance_id=agent_instance.id,
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
            "agent_instance_id": agent_instance.id,
            "agent_definition_id": agent_definition.id,
            "workflow_id": workflow.id,
            "workflow_version_id": version.id,
            "workflow_run_id": run.id,
        }

    yield data

    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(WorkflowParallelBranchRun).where(
                WorkflowParallelBranchRun.workflow_run_id == data["workflow_run_id"]
            )
        )
        await db.execute(
            delete(WorkflowStepRun).where(
                WorkflowStepRun.workflow_run_id == data["workflow_run_id"]
            )
        )
        await db.execute(delete(Run).where(Run.tenant_id == data["tenant_id"]))
        await db.execute(
            delete(WorkflowRun).where(WorkflowRun.id == data["workflow_run_id"])
        )
        # WorkflowVersion is an immutable ledger row and cannot be physically deleted.
        # Retain the workflow/version graph and deprovision the tenant fixture instead.
        await db.execute(
            delete(AgentInstance).where(
                AgentInstance.id == data["agent_instance_id"]
            )
        )
        await db.execute(
            delete(AgentDefinition).where(
                AgentDefinition.id == data["agent_definition_id"]
            )
        )
        await db.execute(
            delete(EmployeeVersion).where(
                EmployeeVersion.id == data["employee_version_id"]
            )
        )
        await db.execute(delete(Employee).where(Employee.id == data["employee_id"]))
        tenant = await db.get(Tenant, data["tenant_id"])
        if tenant is not None:
            tenant.status = "deprovisioned"
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

    original_lock = workflow_service._lock_parent_for_child_execution
    timeout_injected = False

    async def lock_with_injected_timeout(db, *, workflow_run_id):
        nonlocal timeout_injected
        if not timeout_injected:
            timeout_injected = True
            async with AsyncSessionLocal() as racing_db:
                parent = await racing_db.get(WorkflowRun, workflow_run_id)
                assert parent is not None
                parent.status = "timed_out"
                parent.error = {
                    "code": "WORKFLOW_TIMEOUT",
                    "message": "Injected deterministic cross-race timeout",
                }
                parent.completed_at = datetime.now(timezone.utc)
                await racing_db.commit()
        return await original_lock(db, workflow_run_id=workflow_run_id)

    monkeypatch.setattr(
        workflow_service,
        "_lock_parent_for_child_execution",
        lock_with_injected_timeout,
    )

    async with AsyncSessionLocal() as db:
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
        assert child[0].agent_instance_id == data["agent_instance_id"]
        assert child[0].completed_at is not None
        assert "became terminal before child execution" in (child[0].error_message or "")


@pytest.mark.asyncio
async def test_parallel_branch_timeout_after_child_commit_never_executes_child(
    workflow_cross_race_setup, monkeypatch
):
    data = workflow_cross_race_setup
    branch_lease_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        step = WorkflowStepRun(
            workflow_run_id=data["workflow_run_id"],
            step_key="parallel",
            step_type="parallel",
            position=0,
            status="waiting_parallel",
            input_data={},
        )
        db.add(step)
        await db.flush()
        branch = WorkflowParallelBranchRun(
            workflow_run_id=data["workflow_run_id"],
            workflow_step_run_id=step.id,
            branch_key="branch-a",
            config={
                "steps": [
                    {
                        "key": "child",
                        "type": "employee",
                        "employee_id": str(data["employee_id"]),
                        "employee_version_id": str(data["employee_version_id"]),
                    }
                ]
            },
            status="pending",
        )
        db.add(branch)
        await db.commit()
        branch_id = branch.id

    async def acquire_branch(db, *, branch_id, **_kwargs):
        branch = await db.get(WorkflowParallelBranchRun, branch_id)
        assert branch is not None
        branch.status = "running"
        branch.execution_lease_id = branch_lease_id
        branch.execution_lease_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await db.flush()
        return branch_lease_id

    async def assert_branch(db, *, branch_id, lease_id, **_kwargs):
        branch = await db.get(WorkflowParallelBranchRun, branch_id)
        assert branch is not None
        assert branch.status == "running"
        assert branch.execution_lease_id == branch_lease_id
        return branch

    async def heartbeat_branch(*_args, **_kwargs):
        return None

    monkeypatch.setattr(workflow_execution_lease, "acquire_parallel_branch_execution_lease", acquire_branch)
    monkeypatch.setattr(workflow_execution_lease, "assert_parallel_branch_execution_lease", assert_branch)
    monkeypatch.setattr(workflow_execution_lease, "heartbeat_parallel_branch_execution_lease", heartbeat_branch)

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

    executed = False

    async def execute_child(*_args, **_kwargs):
        nonlocal executed
        executed = True
        raise AssertionError("parallel child execution crossed the timeout fence")

    monkeypatch.setattr(workflow_service.run_service, "create_run", create_run)
    monkeypatch.setattr(workflow_service.run_service, "execute_run", execute_child)

    original_lock = workflow_service._lock_parent_for_child_execution
    lock_calls = 0

    async def lock_with_timeout(db, *, workflow_run_id):
        nonlocal lock_calls
        lock_calls += 1
        # The first boundary check must admit the branch and allow the child
        # Run to be durably committed. Inject the concurrent timeout only at
        # the second parent lock, which is the post-commit execution fence.
        if lock_calls == 2:
            async with AsyncSessionLocal() as racing_db:
                parent = await racing_db.get(WorkflowRun, workflow_run_id)
                assert parent is not None
                parent.status = "timed_out"
                parent.error = {
                    "code": "WORKFLOW_TIMEOUT",
                    "message": "Injected parallel-branch timeout",
                }
                parent.completed_at = datetime.now(timezone.utc)
                await racing_db.commit()
        return await original_lock(db, workflow_run_id=workflow_run_id)

    monkeypatch.setattr(
        workflow_service,
        "_lock_parent_for_child_execution",
        lock_with_timeout,
    )

    await workflow_service._execute_parallel_branch(
        branch_id,
        expected_tenant_id=data["tenant_id"],
    )

    assert executed is False

    async with AsyncSessionLocal() as db:
        parent = await db.get(WorkflowRun, data["workflow_run_id"])
        branch = await db.get(WorkflowParallelBranchRun, branch_id)
        child_result = await db.execute(
            select(Run).where(
                Run.tenant_id == data["tenant_id"],
                Run.workflow_parallel_branch_run_id == branch_id,
            )
        )
        child = child_result.scalar_one()

        assert parent is not None
        assert parent.status == "timed_out"
        assert branch is not None
        assert branch.status == "failed"
        assert branch.execution_lease_id is None
        assert child.status == "cancelled"
        assert child.completed_at is not None
        assert "became terminal before child execution" in (child.error_message or "")


@pytest.mark.asyncio
async def test_parallel_branch_cancellation_after_child_commit_never_executes_child(
    workflow_cross_race_setup, monkeypatch
):
    data = workflow_cross_race_setup
    branch_lease_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        step = WorkflowStepRun(
            workflow_run_id=data["workflow_run_id"],
            step_key="parallel",
            step_type="parallel",
            position=0,
            status="waiting_parallel",
            input_data={},
        )
        db.add(step)
        await db.flush()
        branch = WorkflowParallelBranchRun(
            workflow_run_id=data["workflow_run_id"],
            workflow_step_run_id=step.id,
            branch_key="branch-a",
            config={
                "steps": [
                    {
                        "key": "child",
                        "type": "employee",
                        "employee_id": str(data["employee_id"]),
                        "employee_version_id": str(data["employee_version_id"]),
                    }
                ]
            },
            status="pending",
        )
        db.add(branch)
        await db.commit()
        branch_id = branch.id

    async def acquire_branch(db, *, branch_id, **_kwargs):
        branch = await db.get(WorkflowParallelBranchRun, branch_id)
        assert branch is not None
        branch.status = "running"
        branch.execution_lease_id = branch_lease_id
        branch.execution_lease_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await db.flush()
        return branch_lease_id

    async def assert_branch(db, *, branch_id, lease_id, **_kwargs):
        branch = await db.get(WorkflowParallelBranchRun, branch_id)
        assert branch is not None
        assert branch.status == "running"
        assert branch.execution_lease_id == branch_lease_id
        return branch

    async def heartbeat_branch(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        workflow_execution_lease,
        "acquire_parallel_branch_execution_lease",
        acquire_branch,
    )
    monkeypatch.setattr(
        workflow_execution_lease,
        "assert_parallel_branch_execution_lease",
        assert_branch,
    )
    monkeypatch.setattr(
        workflow_execution_lease,
        "heartbeat_parallel_branch_execution_lease",
        heartbeat_branch,
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

    executed = False

    async def execute_child(*_args, **_kwargs):
        nonlocal executed
        executed = True
        raise AssertionError("parallel child execution crossed the cancellation fence")

    monkeypatch.setattr(workflow_service.run_service, "create_run", create_run)
    monkeypatch.setattr(workflow_service.run_service, "execute_run", execute_child)

    original_lock = workflow_service._lock_parent_for_child_execution
    lock_calls = 0

    async def lock_with_cancellation(db, *, workflow_run_id):
        nonlocal lock_calls
        lock_calls += 1
        if lock_calls == 2:
            async with AsyncSessionLocal() as racing_db:
                cancelled = await workflow_service.cancel_workflow_run(
                    racing_db,
                    workflow_run_id=workflow_run_id,
                    tenant_id=data["tenant_id"],
                    cancelled_by=uuid.uuid4(),
                    reason="Injected parallel-branch cancellation",
                )
                await racing_db.commit()
                assert cancelled.status == "cancelled"
        return await original_lock(db, workflow_run_id=workflow_run_id)

    monkeypatch.setattr(
        workflow_service,
        "_lock_parent_for_child_execution",
        lock_with_cancellation,
    )

    await workflow_service._execute_parallel_branch(
        branch_id,
        expected_tenant_id=data["tenant_id"],
    )

    assert executed is False

    async with AsyncSessionLocal() as db:
        parent = await db.get(WorkflowRun, data["workflow_run_id"])
        branch = await db.get(WorkflowParallelBranchRun, branch_id)
        child_result = await db.execute(
            select(Run).where(
                Run.tenant_id == data["tenant_id"],
                Run.workflow_parallel_branch_run_id == branch_id,
            )
        )
        child = child_result.scalar_one()

        assert parent is not None
        assert parent.status == "cancelled"
        assert branch is not None
        assert branch.status == "cancelled"
        assert branch.execution_lease_id is None
        assert child.status == "cancelled"
        assert child.completed_at is not None
        assert "WorkflowRun was cancelled" in (child.error_message or "")
