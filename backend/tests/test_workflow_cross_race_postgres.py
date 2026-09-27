"""Real PostgreSQL runtime coverage for workflow cross-race admission."""

from __future__ import annotations

import asyncio

from datetime import datetime, timedelta, timezone
import uuid

import pytest
import pytest_asyncio

from app.core.exceptions import ValidationAppError
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.agent_definition import AgentDefinition
from app.models.agent_instance import AgentInstance
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.outbox import OutboxMessage
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
        # Execution rows reference Run through employee_run_id, so remove
        # branch/step link owners before deleting the durable child Runs.
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
        await db.execute(delete(WorkflowRun).where(WorkflowRun.tenant_id == data["tenant_id"]))
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
async def test_replay_existing_parallel_branch_creates_new_branch_identity(
    workflow_cross_race_setup, monkeypatch
):
    data = workflow_cross_race_setup

    # Replay must bind to the immutable source version. Use a dedicated
    # parallel version so execution exercises durable branch creation on the
    # replayed WorkflowRun rather than merely replay metadata.
    async with AsyncSessionLocal() as db:
        version = WorkflowVersion(
            workflow_id=data["workflow_id"],
            version_number=2,
            is_current=False,
            trigger_type="manual",
            config={
                "steps": [{
                    "key": "parallel",
                    "type": "parallel",
                    "branches": [{
                        "key": "branch-a",
                        "steps": [{
                            "key": "child",
                            "type": "employee",
                            "employee_id": str(data["employee_id"]),
                            "employee_version_id": str(data["employee_version_id"]),
                        }],
                    }],
                }],
            },
            execution_contract={
                "schema_version": 1,
                "legacy": False,
                "workflow_version_number": 2,
                "steps": [{
                    "key": "parallel",
                    "type": "parallel",
                    "branches": [{
                        "key": "branch-a",
                        "steps": [{
                            "key": "child",
                            "type": "employee",
                            "employee_id": str(data["employee_id"]),
                            "employee_version_id": str(data["employee_version_id"]),
                        }],
                    }],
                }],
                "max_runtime_seconds": 300,
            },
            content_hash="replay-existing-branch-runtime-v2",
            created_by=None,
        )
        db.add(version)
        await db.flush()

        source = WorkflowRun(
            tenant_id=data["tenant_id"],
            workflow_id=data["workflow_id"],
            workflow_version_id=version.id,
            created_by=None,
            agent_instance_id=data["agent_instance_id"],
            status="waiting_parallel",
            context={
                "input": {"value": "replay"},
                "steps": {},
                "_workflow": {
                    "next_position": 0,
                    "execution_contract": version.execution_contract,
                },
            },
            deadline_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db.add(source)
        await db.flush()

        source_step = WorkflowStepRun(
            workflow_run_id=source.id,
            step_key="parallel",
            step_type="parallel",
            position=0,
            status="waiting_parallel",
            input_data={},
        )
        db.add(source_step)
        await db.flush()

        source_branch = WorkflowParallelBranchRun(
            workflow_run_id=source.id,
            workflow_step_run_id=source_step.id,
            branch_key="branch-a",
            config={"steps": version.execution_contract["steps"][0]["branches"][0]["steps"]},
            status="pending",
        )
        db.add(source_branch)
        await db.commit()

        source_id = source.id
        source_branch_id = source_branch.id
        source_step_id = source_step.id
        source_version_id = version.id
        source_hash = version.content_hash

        replay = await workflow_service.replay_workflow_run(
            db,
            tenant_id=data["tenant_id"],
            workflow_id=data["workflow_id"],
            source_run_id=source.id,
            created_by=None,
            idempotency_key=f"replay-existing-branch-{uuid.uuid4()}",
        )
        await db.commit()

        replay_id = replay.id
        assert replay_id != source_id
        assert replay.workflow_version_id == source_version_id
        assert replay.context["_workflow"]["replay_of_run_id"] == str(source_id)
        assert replay.context["_workflow"]["replay_source_version_id"] == str(source_version_id)
        assert replay.context["_workflow"]["workflow_content_hash"] == source_hash
        assert replay.context["_workflow"]["execution_contract"] == version.execution_contract

        # Executing the replay creates branch rows scoped to the replay's
        # WorkflowStepRun. It must never discover/reuse the source branch.
        async def acquire_lease(db, *, workflow_run_id, allow_recovery=False):
            run = await db.get(WorkflowRun, workflow_run_id)
            assert run is not None
            lease_id = uuid.uuid4()
            run.execution_lease_id = lease_id
            run.execution_lease_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
            run.status = "running"
            await db.flush()
            return lease_id

        monkeypatch.setattr(
            workflow_service,
            "acquire_workflow_execution_lease",
            acquire_lease,
        )

        async def assert_lease(db, *, workflow_run_id, lease_id):
            return await db.get(WorkflowRun, workflow_run_id)

        monkeypatch.setattr(
            workflow_service,
            "assert_workflow_execution_lease",
            assert_lease,
        )
        async def heartbeat_lease(*_args, **_kwargs):
            return None

        monkeypatch.setattr(
            workflow_service,
            "heartbeat_workflow_execution_lease",
            heartbeat_lease,
        )

        await workflow_service.execute_workflow(db, workflow_run_id=replay.id)
        await db.commit()

        replay_steps = (
            await db.execute(
                select(WorkflowStepRun).where(
                    WorkflowStepRun.workflow_run_id == replay.id,
                    WorkflowStepRun.step_key == "parallel",
                )
            )
        ).scalars().all()
        assert len(replay_steps) == 1
        replay_step = replay_steps[0]
        assert replay_step.id != source_step_id

        replay_branches = (
            await db.execute(
                select(WorkflowParallelBranchRun).where(
                    WorkflowParallelBranchRun.workflow_run_id == replay.id,
                    WorkflowParallelBranchRun.workflow_step_run_id == replay_step.id,
                )
            )
        ).scalars().all()
        assert len(replay_branches) == 1
        replay_branch = replay_branches[0]
        assert replay_branch.id != source_branch_id
        assert replay_branch.workflow_run_id == replay.id
        assert replay_branch.workflow_step_run_id == replay_step.id
        assert replay_branch.branch_key == "branch-a"
        assert replay_branch.status == "pending"

        source_branch_after = await db.get(WorkflowParallelBranchRun, source_branch_id)
        source_run_after = await db.get(WorkflowRun, source_id)
        assert source_branch_after is not None
        assert source_branch_after.workflow_run_id == source_id
        assert source_branch_after.workflow_step_run_id == source_step_id
        assert source_branch_after.status == "pending"
        assert source_run_after is not None
        assert source_run_after.workflow_version_id == source_version_id

        # No employee child from the source branch may be accidentally linked
        # to the replayed branch during replay branch creation.
        linked_children = (
            await db.execute(
                select(Run).where(
                    Run.workflow_parallel_branch_run_id == replay_branch.id
                )
            )
        ).scalars().all()
        assert linked_children == []

        # Remove the extra replay/source execution graph created by this test.
        # WorkflowVersion remains immutable by design.
        await db.execute(
            delete(WorkflowParallelBranchRun).where(
                WorkflowParallelBranchRun.workflow_run_id.in_([source_id, replay_id])
            )
        )
        await db.execute(
            delete(WorkflowStepRun).where(
                WorkflowStepRun.workflow_run_id.in_([source_id, replay_id])
            )
        )
        await db.execute(
            delete(WorkflowRun).where(
                WorkflowRun.id.in_([source_id, replay_id])
            )
        )
        await db.commit()


@pytest.mark.asyncio
async def test_worker_crash_branch_lease_recovery_requeues_same_branch(
    workflow_cross_race_setup, monkeypatch
):
    data = workflow_cross_race_setup

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
            config={"steps": [{"key": "child", "employee_id": str(data["employee_id"])}]},
            status="running",
            current_step_position=0,
            execution_lease_id=uuid.uuid4(),
            execution_lease_expires_at=datetime.now(timezone.utc) - timedelta(seconds=5),
            execution_heartbeat_at=datetime.now(timezone.utc) - timedelta(seconds=30),
        )
        db.add(branch)
        await db.commit()
        branch_id = branch.id

    async def enqueue(db, *, kind, tenant_id=None, payload, dedupe_key=None, available_at=None):
        message = OutboxMessage(
            tenant_id=tenant_id,
            kind=kind,
            payload=payload,
            status="pending",
            attempts=0,
            dedupe_key=dedupe_key,
            available_at=available_at or datetime.now(timezone.utc),
        )
        db.add(message)
        await db.flush()
        return message

    from app.workers import workflow_trigger_worker
    from app.services import outbox_service

    monkeypatch.setattr(outbox_service, "enqueue", enqueue)

    count = await workflow_trigger_worker._timeout_workflow_runs_async()
    assert count == 1

    async with AsyncSessionLocal() as db:
        recovered = await db.get(WorkflowParallelBranchRun, branch_id)
        assert recovered is not None
        assert recovered.execution_lease_id is not None
        assert recovered.execution_lease_expires_at is not None
        assert recovered.execution_lease_expires_at > datetime.now(timezone.utc)

        outbox = (
            await db.execute(
                select(OutboxMessage).where(
                    OutboxMessage.dedupe_key
                    == f"workflow.parallel_branch:{branch_id}:lease-recovery:{recovered.execution_lease_id}"
                )
            )
        ).scalar_one_or_none()
        assert outbox is not None
        assert outbox.kind == "workflow.parallel_branch"
        assert outbox.payload["branch_id"] == str(branch_id)


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
        assert "became terminal before child execution" in (child.error_message or "")


@pytest.mark.asyncio
async def test_parallel_branch_cancellation_after_child_execution_preserves_terminal_branch(
    workflow_cross_race_setup, monkeypatch
):
    data = workflow_cross_race_setup
    branch_lease_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        step = WorkflowStepRun(
            workflow_run_id=data["workflow_run_id"],
            step_key="parallel-post-child",
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
            branch_key="branch-post-child",
            config={
                "steps": [{
                    "key": "child",
                    "type": "employee",
                    "employee_id": str(data["employee_id"]),
                    "employee_version_id": str(data["employee_version_id"]),
                }]
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

    async def execute_child(db, *, run_id, **_kwargs):
        nonlocal executed
        executed = True
        child = await db.get(Run, run_id)
        assert child is not None
        child.status = "success"
        child.output_data = {"result": "completed-before-cancel"}
        # Mirror the real run_service.execute_run() transaction boundary:
        # child execution commits before the workflow worker re-locks the
        # parent for post-child terminal reconciliation. Without this commit
        # the test session retains the parent FOR UPDATE lock and the injected
        # concurrent cancellation blocks instead of exercising the race.
        await db.commit()

    monkeypatch.setattr(workflow_service.run_service, "create_run", create_run)
    monkeypatch.setattr(workflow_service.run_service, "execute_run", execute_child)

    original_lock = workflow_service._lock_parent_for_child_execution
    lock_calls = 0

    async def lock_with_post_child_cancellation(db, *, workflow_run_id):
        nonlocal lock_calls
        lock_calls += 1
        if lock_calls == 3:
            async with AsyncSessionLocal() as racing_db:
                cancelled = await workflow_service.cancel_workflow_run(
                    racing_db,
                    workflow_run_id=workflow_run_id,
                    tenant_id=data["tenant_id"],
                    cancelled_by=uuid.uuid4(),
                    reason="Injected post-child cancellation",
                )
                await racing_db.commit()
                assert cancelled.status == "cancelled"
        return await original_lock(db, workflow_run_id=workflow_run_id)

    monkeypatch.setattr(
        workflow_service,
        "_lock_parent_for_child_execution",
        lock_with_post_child_cancellation,
    )

    await workflow_service._execute_parallel_branch(
        branch_id,
        expected_tenant_id=data["tenant_id"],
    )

    assert executed is True

    async with AsyncSessionLocal() as db:
        parent = await db.get(WorkflowRun, data["workflow_run_id"])
        branch = await db.get(WorkflowParallelBranchRun, branch_id)
        child = (
            await db.execute(
                select(Run).where(
                    Run.tenant_id == data["tenant_id"],
                    Run.workflow_parallel_branch_run_id == branch_id,
                )
            )
        ).scalar_one()

        assert parent is not None
        assert parent.status == "cancelled"
        assert branch is not None
        assert branch.status == "cancelled"
        assert branch.execution_lease_id is None
        assert child.status == "success"


@pytest.mark.asyncio
async def test_retry_existing_successful_child_reuses_same_run_without_reexecution(
    workflow_cross_race_setup, monkeypatch
):
    data = workflow_cross_race_setup
    async with AsyncSessionLocal() as db:
        run = await db.get(WorkflowRun, data["workflow_run_id"])
        assert run is not None
        run.status = "pending"
        run.execution_lease_id = None
        run.execution_lease_expires_at = None
        await db.commit()

    async with AsyncSessionLocal() as db:
        step = WorkflowStepRun(
            workflow_run_id=data["workflow_run_id"],
            step_key="child",
            step_type="employee",
            position=0,
            status="running",
            attempt=2,
            input_data={"value": "retry"},
        )
        db.add(step)
        await db.flush()
        child = Run(
            tenant_id=data["tenant_id"],
            employee_id=data["employee_id"],
            employee_version_id=data["employee_version_id"],
            agent_instance_id=data["agent_instance_id"],
            status="success",
            input_data={"value": "retry"},
            output_data={"result": "already-executed"},
            workflow_step_run_id=step.id,
        )
        db.add(child)
        await db.flush()
        step.employee_run_id = child.id
        await db.commit()
        child_id = child.id

    async def acquire_lease(db, *, workflow_run_id, allow_recovery=False):
        run = await db.get(WorkflowRun, workflow_run_id)
        assert run is not None
        run.status = "running"
        run.execution_lease_id = uuid.uuid4()
        run.execution_lease_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await db.flush()
        return run.execution_lease_id

    async def assert_lease(db, *, workflow_run_id, lease_id, **_kwargs):
        run = await db.get(WorkflowRun, workflow_run_id)
        assert run is not None
        assert run.execution_lease_id == lease_id
        return run

    monkeypatch.setattr(workflow_service, "acquire_workflow_execution_lease", acquire_lease)
    monkeypatch.setattr(workflow_service, "assert_workflow_execution_lease", assert_lease)
    async def heartbeat_lease(*_args, **_kwargs):
        return None

    monkeypatch.setattr(workflow_service, "heartbeat_workflow_execution_lease", heartbeat_lease)

    async def execute_child(*_args, **_kwargs):
        raise AssertionError("successful durable child was re-executed")

    async def create_child(*_args, **_kwargs):
        raise AssertionError("successful durable child caused a replacement Run")

    monkeypatch.setattr(workflow_service.run_service, "execute_run", execute_child)
    monkeypatch.setattr(workflow_service.run_service, "create_run", create_child)

    async with AsyncSessionLocal() as db:
        result = await workflow_service.execute_workflow(db, workflow_run_id=data["workflow_run_id"])
        await db.commit()
        assert result.status == "success"

    async with AsyncSessionLocal() as db:
        children = (
            await db.execute(
                select(Run).where(
                    Run.tenant_id == data["tenant_id"],
                    Run.workflow_step_run_id.is_not(None),
                )
            )
        ).scalars().all()
        step = (
            await db.execute(
                select(WorkflowStepRun).where(
                    WorkflowStepRun.workflow_run_id == data["workflow_run_id"],
                    WorkflowStepRun.step_key == "child",
                )
            )
        ).scalar_one()
        assert len(children) == 1
        assert children[0].id == child_id
        assert children[0].status == "success"
        assert step.employee_run_id == child_id
        assert step.status == "success"
        assert step.output_data == {"result": "already-executed"}


@pytest.mark.asyncio
async def test_retry_existing_non_successful_child_fails_closed_without_replacement(
    workflow_cross_race_setup, monkeypatch
):
    data = workflow_cross_race_setup
    async with AsyncSessionLocal() as db:
        run = await db.get(WorkflowRun, data["workflow_run_id"])
        assert run is not None
        run.status = "pending"
        run.execution_lease_id = None
        run.execution_lease_expires_at = None
        await db.commit()

    async with AsyncSessionLocal() as db:
        step = WorkflowStepRun(
            workflow_run_id=data["workflow_run_id"],
            step_key="child",
            step_type="employee",
            position=0,
            status="retry_wait",
            attempt=2,
            input_data={"value": "retry"},
        )
        db.add(step)
        await db.flush()
        child = Run(
            tenant_id=data["tenant_id"],
            employee_id=data["employee_id"],
            employee_version_id=data["employee_version_id"],
            agent_instance_id=data["agent_instance_id"],
            status="failed",
            input_data={"value": "retry"},
            error={"code": "RUN_EXECUTION_FAILED", "message": "prior attempt failed"},
            workflow_step_run_id=step.id,
        )
        db.add(child)
        await db.flush()
        step.employee_run_id = child.id
        await db.commit()
        child_id = child.id

    async def acquire_lease(db, *, workflow_run_id, allow_recovery=False):
        run = await db.get(WorkflowRun, workflow_run_id)
        assert run is not None
        run.status = "running"
        run.execution_lease_id = uuid.uuid4()
        run.execution_lease_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await db.flush()
        return run.execution_lease_id

    async def assert_lease(db, *, workflow_run_id, lease_id, **_kwargs):
        return await db.get(WorkflowRun, workflow_run_id)

    monkeypatch.setattr(workflow_service, "acquire_workflow_execution_lease", acquire_lease)
    monkeypatch.setattr(workflow_service, "assert_workflow_execution_lease", assert_lease)
    async def heartbeat_lease(*_args, **_kwargs):
        return None

    monkeypatch.setattr(workflow_service, "heartbeat_workflow_execution_lease", heartbeat_lease)

    async def create_child(*_args, **_kwargs):
        raise AssertionError("failed durable child caused an unsafe replacement Run")

    async def execute_child(*_args, **_kwargs):
        raise AssertionError("failed durable child was re-executed")

    monkeypatch.setattr(workflow_service.run_service, "create_run", create_child)
    monkeypatch.setattr(workflow_service.run_service, "execute_run", execute_child)

    async with AsyncSessionLocal() as db:
        with pytest.raises(ValidationAppError, match="refusing to create a replacement"):
            await workflow_service.execute_workflow(db, workflow_run_id=data["workflow_run_id"])
        await db.commit()

    async with AsyncSessionLocal() as db:
        children = (
            await db.execute(
                select(Run).where(
                    Run.tenant_id == data["tenant_id"],
                    Run.workflow_step_run_id.is_not(None),
                )
            )
        ).scalars().all()
        step = (
            await db.execute(
                select(WorkflowStepRun).where(
                    WorkflowStepRun.workflow_run_id == data["workflow_run_id"],
                    WorkflowStepRun.step_key == "child",
                )
            )
        ).scalar_one()
        parent = await db.get(WorkflowRun, data["workflow_run_id"])

        assert len(children) == 1
        assert children[0].id == child_id
        assert children[0].status == "failed"
        assert step.employee_run_id == child_id
        assert step.status == "failed"
        assert step.error["code"] == "WORKFLOW_CHILD_RETRY_UNSAFE"
        assert parent.status == "failed"


@pytest.mark.asyncio
async def test_retry_mismatched_linked_child_fails_closed_without_cross_step_reuse(
    workflow_cross_race_setup, monkeypatch
):
    data = workflow_cross_race_setup
    async with AsyncSessionLocal() as db:
        run = await db.get(WorkflowRun, data["workflow_run_id"])
        assert run is not None
        run.status = "pending"
        run.execution_lease_id = None
        run.execution_lease_expires_at = None
        await db.commit()

    async with AsyncSessionLocal() as db:
        step = WorkflowStepRun(
            workflow_run_id=data["workflow_run_id"],
            step_key="child",
            step_type="employee",
            position=0,
            status="running",
            attempt=2,
            input_data={"value": "retry"},
        )
        wrong_step = WorkflowStepRun(
            workflow_run_id=data["workflow_run_id"],
            step_key="wrong-child",
            step_type="employee",
            position=1,
            status="success",
            input_data={},
        )
        db.add_all([step, wrong_step])
        await db.flush()
        child = Run(
            tenant_id=data["tenant_id"],
            employee_id=data["employee_id"],
            employee_version_id=data["employee_version_id"],
            agent_instance_id=data["agent_instance_id"],
            status="success",
            input_data={"value": "wrong-step"},
            output_data={"result": "wrong-boundary"},
            workflow_step_run_id=wrong_step.id,
        )
        db.add(child)
        await db.flush()
        step.employee_run_id = child.id
        await db.commit()
        child_id = child.id

    async def acquire_lease(db, *, workflow_run_id, allow_recovery=False):
        run = await db.get(WorkflowRun, workflow_run_id)
        assert run is not None
        run.status = "running"
        run.execution_lease_id = uuid.uuid4()
        run.execution_lease_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await db.flush()
        return run.execution_lease_id

    async def assert_lease(db, *, workflow_run_id, lease_id, **_kwargs):
        return await db.get(WorkflowRun, workflow_run_id)

    monkeypatch.setattr(workflow_service, "acquire_workflow_execution_lease", acquire_lease)
    monkeypatch.setattr(workflow_service, "assert_workflow_execution_lease", assert_lease)
    async def heartbeat_lease(*_args, **_kwargs):
        return None

    monkeypatch.setattr(workflow_service, "heartbeat_workflow_execution_lease", heartbeat_lease)

    async with AsyncSessionLocal() as db:
        with pytest.raises(ValidationAppError, match="no matching durable workflow-step identity|refusing replay"):
            await workflow_service.execute_workflow(db, workflow_run_id=data["workflow_run_id"])
        await db.commit()

    async with AsyncSessionLocal() as db:
        children = (
            await db.execute(
                select(Run).where(
                    Run.tenant_id == data["tenant_id"],
                    Run.workflow_step_run_id.is_not(None),
                )
            )
        ).scalars().all()
        step = (
            await db.execute(
                select(WorkflowStepRun).where(
                    WorkflowStepRun.workflow_run_id == data["workflow_run_id"],
                    WorkflowStepRun.step_key == "child",
                )
            )
        ).scalar_one()
        assert len(children) == 1
        assert children[0].id == child_id
        assert children[0].workflow_step_run_id == wrong_step.id
        assert step.employee_run_id == child_id
        assert step.status == "failed"
        assert step.error["code"] == "WORKFLOW_CHILD_RETRY_UNSAFE"


@pytest.mark.asyncio
async def test_branch_lease_loss_during_parent_cancellation_preserves_terminal_branch(
    workflow_cross_race_setup, monkeypatch
):
    """A branch losing its lease while the parent is concurrently cancelled
    must not resurrect or overwrite the durable cancellation decision.
    """
    data = workflow_cross_race_setup
    async with AsyncSessionLocal() as db:
        step = WorkflowStepRun(
            workflow_run_id=data["workflow_run_id"],
            step_key="parallel-lease-loss",
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
            branch_key="branch-lease-loss",
            config={
                "steps": [{
                    "key": "lease-loss-child",
                    "type": "employee",
                    "employee_id": str(data["employee_id"]),
                    "employee_version_id": str(data["employee_version_id"]),
                }]
            },
            status="pending",
        )
        db.add(branch)
        await db.commit()
        branch_id = branch.id

    lease_id = uuid.uuid4()
    assert_calls = 0
    cancellation_started = asyncio.Event()
    cancellation_task = None

    async def acquire_branch_lease(db, *, branch_id, **_kwargs):
        branch = await db.get(WorkflowParallelBranchRun, branch_id)
        assert branch is not None
        branch.status = "running"
        branch.execution_lease_id = lease_id
        branch.execution_lease_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await db.flush()
        return lease_id

    async def cancel_parent():
        async with AsyncSessionLocal() as racing_db:
            # Establish the parent-first side of the real lock-order race.
            await racing_db.execute(
                select(WorkflowRun)
                .where(WorkflowRun.id == data["workflow_run_id"])
                .with_for_update()
            )
            cancelled = await workflow_service.cancel_workflow_run(
                racing_db,
                workflow_run_id=data["workflow_run_id"],
                tenant_id=data["tenant_id"],
                cancelled_by=uuid.uuid4(),
                reason="Injected branch lease-loss cancellation",
            )
            await racing_db.commit()
            assert cancelled.status == "cancelled"

    async def assert_branch_lease(db, *, branch_id, lease_id, **_kwargs):
        nonlocal assert_calls, cancellation_task
        assert_calls += 1
        if assert_calls == 2:
            cancellation_task = asyncio.create_task(cancel_parent())
            await cancellation_started.wait()
            raise ValidationAppError("WORKFLOW_BRANCH_EXECUTION_LEASE_LOST")
        return await db.get(WorkflowParallelBranchRun, branch_id)

    async def heartbeat_branch(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        workflow_execution_lease,
        "acquire_parallel_branch_execution_lease",
        acquire_branch_lease,
    )
    monkeypatch.setattr(
        workflow_execution_lease,
        "assert_parallel_branch_execution_lease",
        assert_branch_lease,
    )
    monkeypatch.setattr(
        workflow_execution_lease,
        "heartbeat_parallel_branch_execution_lease",
        heartbeat_branch,
    )

    with pytest.raises(ValidationAppError, match="WORKFLOW_BRANCH_EXECUTION_LEASE_LOST"):
        await workflow_service._execute_parallel_branch(
            branch_id,
            expected_tenant_id=data["tenant_id"],
        )

    assert cancellation_task is not None
    await cancellation_task

    async with AsyncSessionLocal() as db:
        parent = await db.get(WorkflowRun, data["workflow_run_id"])
        branch = await db.get(WorkflowParallelBranchRun, branch_id)

        assert parent is not None
        assert parent.status == "cancelled"
        assert branch is not None
        assert branch.status == "cancelled"
        assert branch.execution_lease_id is None
        assert branch.execution_lease_expires_at is None
        assert branch.execution_heartbeat_at is None
        assert branch.completed_at is not None



@pytest.mark.asyncio
async def test_parallel_branch_recovery_uses_parent_first_lock_order(
    workflow_cross_race_setup,
):
    """Branch recovery must not deadlock with parent-first cancellation."""
    data = workflow_cross_race_setup

    async with AsyncSessionLocal() as db:
        run = await db.get(WorkflowRun, data["workflow_run_id"])
        assert run is not None
        run.status = "running"
        run.deadline_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        db.add(
            WorkflowStepRun(
                workflow_run_id=run.id,
                step_key="recovery-race",
                step_type="parallel",
                position=0,
                status="waiting_parallel",
                input_data={},
            )
        )
        await db.flush()
        step = (
            await db.execute(
                select(WorkflowStepRun).where(
                    WorkflowStepRun.workflow_run_id == run.id,
                    WorkflowStepRun.step_key == "recovery-race",
                )
            )
        ).scalar_one()
        branch = WorkflowParallelBranchRun(
            workflow_run_id=run.id,
            workflow_step_run_id=step.id,
            branch_key="recovery-race-branch",
            config={"steps": []},
            status="running",
            execution_lease_id=uuid.uuid4(),
            execution_lease_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        db.add(branch)
        await db.commit()
        branch_id = branch.id

    parent_locked = asyncio.Event()

    async def cancel_parent():
        async with AsyncSessionLocal() as db:
            await db.execute(
                select(WorkflowRun)
                .where(WorkflowRun.id == data["workflow_run_id"])
                .with_for_update()
            )
            parent_locked.set()
            # Give recovery a chance to contend for the same parent row before
            # cancellation takes the branch lock.
            await asyncio.sleep(0.1)
            cancelled = await workflow_service.cancel_workflow_run(
                db,
                workflow_run_id=data["workflow_run_id"],
                tenant_id=data["tenant_id"],
                cancelled_by=uuid.uuid4(),
                reason="Recovery lock-order race",
            )
            await db.commit()
            assert cancelled.status == "cancelled"

    cancellation_task = asyncio.create_task(cancel_parent())
    await asyncio.wait_for(parent_locked.wait(), timeout=2)

    async with AsyncSessionLocal() as recovery_db:
        recovery_task = asyncio.create_task(
            workflow_execution_lease.recover_parallel_branch_execution_lease(
                recovery_db,
                branch_id=branch_id,
            )
        )
        with pytest.raises(ValidationAppError, match="Parent workflow is not recoverable"):
            await asyncio.wait_for(recovery_task, timeout=2)

    await asyncio.wait_for(cancellation_task, timeout=2)

    async with AsyncSessionLocal() as db:
        parent = await db.get(WorkflowRun, data["workflow_run_id"])
        branch = await db.get(WorkflowParallelBranchRun, branch_id)
        assert parent is not None
        assert parent.status == "cancelled"
        assert branch is not None
        assert branch.status == "cancelled"
        assert branch.execution_lease_id is None
        assert branch.execution_lease_expires_at is None


@pytest.mark.asyncio
async def test_parallel_branch_execution_uses_parent_first_lock_order(
    workflow_cross_race_setup, monkeypatch
):
    """A running branch must not hold Branch while waiting for its parent lock."""
    data = workflow_cross_race_setup
    lease_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        run = await db.get(WorkflowRun, data["workflow_run_id"])
        assert run is not None
        run.status = "running"
        run.deadline_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        step = WorkflowStepRun(
            workflow_run_id=run.id,
            step_key="execution-lock-order",
            step_type="parallel",
            position=0,
            status="waiting_parallel",
            input_data={},
        )
        db.add(step)
        await db.flush()
        branch = WorkflowParallelBranchRun(
            workflow_run_id=run.id,
            workflow_step_run_id=step.id,
            branch_key="execution-lock-order-branch",
            config={
                "steps": [{
                    "key": "execution-lock-order-child",
                    "type": "employee",
                    "employee_id": str(data["employee_id"]),
                    "employee_version_id": str(data["employee_version_id"]),
                }]
            },
            status="running",
            execution_lease_id=lease_id,
            execution_lease_expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db.add(branch)
        await db.commit()
        branch_id = branch.id

    parent_locked = asyncio.Event()
    cancellation_task = None

    async def assert_branch_lease(db, *, branch_id, lease_id):
        nonlocal cancellation_task
        if cancellation_task is None:
            cancellation_task = asyncio.create_task(
                cancel_parent_while_worker_is_at_branch_fence()
            )
            await asyncio.wait_for(parent_locked.wait(), timeout=2)
        current = await db.get(WorkflowParallelBranchRun, branch_id)
        assert current is not None
        return current

    async def cancel_parent_while_worker_is_at_branch_fence():
        async with AsyncSessionLocal() as db:
            await db.execute(
                select(WorkflowRun)
                .where(WorkflowRun.id == data["workflow_run_id"])
                .with_for_update()
            )
            parent_locked.set()
            cancelled = await workflow_service.cancel_workflow_run(
                db,
                workflow_run_id=data["workflow_run_id"],
                tenant_id=data["tenant_id"],
                cancelled_by=uuid.uuid4(),
                reason="Execution lock-order race",
            )
            await db.commit()
            assert cancelled.status == "cancelled"

    monkeypatch.setattr(
        workflow_execution_lease,
        "assert_parallel_branch_execution_lease",
        assert_branch_lease,
    )

    await asyncio.wait_for(
        workflow_service._execute_parallel_branch(
            branch_id,
            execution_lease_id=lease_id,
            expected_tenant_id=data["tenant_id"],
        ),
        timeout=4,
    )
    assert cancellation_task is not None
    await asyncio.wait_for(cancellation_task, timeout=4)

    async with AsyncSessionLocal() as db:
        parent = await db.get(WorkflowRun, data["workflow_run_id"])
        branch = await db.get(WorkflowParallelBranchRun, branch_id)
        assert parent is not None
        assert parent.status == "cancelled"
        assert branch is not None
        assert branch.status == "cancelled"
        assert branch.execution_lease_id is None
        assert branch.execution_lease_expires_at is None


def test_workflow_approval_paths_lock_parent_before_step():
    """Approval decision and expiry must share WorkflowRun -> WorkflowStepRun order."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    api_source = (root / "app/api/v1/workflow_approvals.py").read_text()
    worker_source = (root / "app/workers/workflow_trigger_worker.py").read_text()

    api_parent = api_source.index("select(WorkflowRun)")
    api_step = api_source.index("select(WorkflowStepRun)")
    worker_parent = worker_source.index("select(WorkflowRun).where(WorkflowRun.id == approval.workflow_run_id)")
    worker_step = worker_source.index("select(WorkflowStepRun).where(WorkflowStepRun.id == approval.workflow_step_run_id)")

    assert api_parent < api_step
    assert worker_parent < worker_step
    assert ".with_for_update()" in api_source[api_parent:api_step]
    assert ".with_for_update()" in worker_source[worker_parent:worker_step]


@pytest.mark.asyncio
async def test_timeout_sweep_branch_recovery_keeps_parent_first_lock_order(
    workflow_cross_race_setup, monkeypatch
):
    """The recovery sweep must not hold a branch lock before acquiring its parent."""
    data = workflow_cross_race_setup

    async with AsyncSessionLocal() as db:
        run = await db.get(WorkflowRun, data["workflow_run_id"])
        assert run is not None
        run.status = "running"
        run.deadline_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        step = WorkflowStepRun(
            workflow_run_id=run.id,
            step_key="sweep-lock-order",
            step_type="parallel",
            position=0,
            status="waiting_parallel",
            input_data={},
        )
        db.add(step)
        await db.flush()
        branch = WorkflowParallelBranchRun(
            workflow_run_id=run.id,
            workflow_step_run_id=step.id,
            branch_key="sweep-lock-order-branch",
            config={"steps": []},
            status="running",
            execution_lease_id=uuid.uuid4(),
            execution_lease_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        db.add(branch)
        await db.commit()
        branch_id = branch.id

    discovery_returned = asyncio.Event()
    cancellation_task = None

    async def cancel_parent():
        async with AsyncSessionLocal() as db:
            await db.execute(
                select(WorkflowRun)
                .where(WorkflowRun.id == data["workflow_run_id"])
                .with_for_update()
            )
            cancellation_started.set()
            cancelled = await workflow_service.cancel_workflow_run(
                db,
                workflow_run_id=data["workflow_run_id"],
                tenant_id=data["tenant_id"],
                cancelled_by=uuid.uuid4(),
                reason="Recovery sweep lock-order race",
            )
            await db.commit()
            assert cancelled.status == "cancelled"

    original_recover = workflow_execution_lease.recover_parallel_branch_execution_lease

    async def recover_with_race(db, *, branch_id):
        nonlocal cancellation_task
        discovery_returned.set()
        cancellation_task = asyncio.create_task(cancel_parent())
        await asyncio.sleep(0.05)
        return await original_recover(db, branch_id=branch_id)

    async def enqueue(db, *, kind, tenant_id=None, payload, dedupe_key=None, available_at=None):
        message = OutboxMessage(
            tenant_id=tenant_id,
            kind=kind,
            payload=payload,
            status="pending",
            attempts=0,
            dedupe_key=dedupe_key,
            available_at=available_at or datetime.now(timezone.utc),
        )
        db.add(message)
        await db.flush()
        return message

    from app.workers import workflow_trigger_worker
    from app.services import outbox_service

    monkeypatch.setattr(workflow_execution_lease, "recover_parallel_branch_execution_lease", recover_with_race)
    monkeypatch.setattr(outbox_service, "enqueue", enqueue)

    count = await asyncio.wait_for(
        workflow_trigger_worker._timeout_workflow_runs_async(),
        timeout=4,
    )

    assert discovery_returned.is_set()
    assert cancellation_task is not None
    await asyncio.wait_for(cancellation_task, timeout=2)
    assert count == 1

    async with AsyncSessionLocal() as db:
        parent = await db.get(WorkflowRun, data["workflow_run_id"])
        branch = await db.get(WorkflowParallelBranchRun, branch_id)
        assert parent is not None
        assert parent.status == "cancelled"
        assert branch is not None
        assert branch.status == "cancelled"
        assert branch.execution_lease_id is None
        assert branch.execution_lease_expires_at is None
