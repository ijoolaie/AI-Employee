"""Workflow Engine: versioned Employee actions, conditions, schedules and event-driven execution."""
from __future__ import annotations
import uuid
import asyncio
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.logging import request_id_var
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.workflow import Workflow, WorkflowVersion, WorkflowRun, WorkflowStepRun, WorkflowParallelBranchRun
from app.models.workflow_approval import WorkflowApproval
from app.services import audit_service, employee_service, run_service, outbox_service, billing_service
from app.services.workflow_conditions import evaluate_condition
from app.core.metrics import WORKFLOW_STEPS


def _resolve_mapping(mapping: dict[str, str], context: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for target, source in mapping.items():
        if source.startswith("$.input."):
            key = source[8:]
            out[target] = context.get("input", {}).get(key)
        elif source.startswith("$.steps."):
            rest = source[8:]
            step_key, _, field = rest.partition(".")
            value = context.get("steps", {}).get(step_key, {})
            out[target] = value.get(field) if field else value
        else:
            raise ValidationAppError(f"Unsupported workflow mapping source: {source}")
    return out


async def _snapshot_steps(db: AsyncSession, *, tenant_id: uuid.UUID, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve every Employee step to an immutable EmployeeVersion snapshot.

    The returned structure is stored inside WorkflowVersion and is therefore
    the execution contract for all future Runs. Historical WorkflowVersion
    rows are never edited to refresh these references.
    """
    snapshot = []
    for raw in steps:
        step = json.loads(json.dumps(raw, default=str))
        step_type = step.get("type", "employee")
        if step_type == "employee":
            if not step.get("employee_id"):
                raise ValidationAppError(f"Employee step {step.get('key')} requires employee_id")
            employee_id = uuid.UUID(str(step["employee_id"]))
            employee = await employee_service.get_employee(db, employee_id=employee_id, tenant_id=tenant_id)
            version = await employee_service.get_current_version(db, employee_id=employee.id)
            step["employee_version_id"] = str(version.id)
            step["employee_version_number"] = version.version_number
        elif step_type == "parallel":
            branches = step.get("branches") or []
            if not branches:
                raise ValidationAppError(f"Parallel step {step.get('key')} requires at least one branch")
            seen = set()
            for branch in branches:
                bkey = branch.get("key")
                if not bkey or bkey in seen:
                    raise ValidationAppError(f"Parallel step {step.get('key')} has invalid/duplicate branch key")
                seen.add(bkey)
                branch["steps"] = await _snapshot_steps(db, tenant_id=tenant_id, steps=branch.get("steps", []))
        snapshot.append(step)
    return snapshot


def _execution_contract(*, version_number: int, steps: list[dict[str, Any]], max_runtime_seconds: int | None, legacy: bool = False) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "legacy": legacy,
        "workflow_version_number": version_number,
        "steps": steps,
        "max_runtime_seconds": max_runtime_seconds,
    }


def _content_hash(config: dict[str, Any], contract: dict[str, Any]) -> str:
    payload = json.dumps({"config": config, "execution_contract": contract}, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def _validate_steps(db: AsyncSession, *, tenant_id: uuid.UUID, steps: list[dict[str, Any]]) -> None:
    for step in steps:
        if step.get("type", "employee") == "employee":
            if not step.get("employee_id"):
                raise ValidationAppError(f"Employee step {step.get('key')} requires employee_id")
            await employee_service.get_employee(db, employee_id=uuid.UUID(str(step["employee_id"])), tenant_id=tenant_id)
        elif step.get("type") == "parallel":
            branches = step.get("branches") or []
            if not branches:
                raise ValidationAppError(f"Parallel step {step.get('key')} requires at least one branch")
            for branch in branches:
                for branch_step in branch.get("steps", []):
                    if branch_step.get("type", "employee") != "employee":
                        raise ValidationAppError("v0.2.38 parallel branches support employee steps only")
                    if not branch_step.get("employee_id"):
                        raise ValidationAppError(f"Parallel branch step {branch_step.get('key')} requires employee_id")
                    await employee_service.get_employee(db, employee_id=uuid.UUID(str(branch_step["employee_id"])), tenant_id=tenant_id)


async def create_workflow(db: AsyncSession, *, tenant_id: uuid.UUID, created_by: uuid.UUID, slug: str, name: str, steps: list[dict], trigger_type: str, max_runtime_seconds: int | None = None) -> Workflow:
    existing = await db.execute(select(Workflow).where(Workflow.tenant_id == tenant_id, Workflow.slug == slug))
    if existing.scalar_one_or_none():
        raise ValidationAppError(f"Workflow with slug '{slug}' already exists")
    await _validate_steps(db, tenant_id=tenant_id, steps=steps)
    snap = await _snapshot_steps(db, tenant_id=tenant_id, steps=steps)
    workflow = Workflow(tenant_id=tenant_id, slug=slug, name=name, created_by=created_by)
    db.add(workflow)
    await db.flush()
    config = {"steps": steps, "max_runtime_seconds": max_runtime_seconds}
    contract = _execution_contract(version_number=1, steps=snap, max_runtime_seconds=max_runtime_seconds)
    version = WorkflowVersion(workflow_id=workflow.id, version_number=1, is_current=True, trigger_type=trigger_type, config=config, execution_contract=contract, content_hash=_content_hash(config, contract), created_by=created_by)
    db.add(version)
    await db.flush()
    await audit_service.record(db, action="workflow.created", actor_id=created_by, tenant_id=tenant_id, resource_type="workflow", resource_id=workflow.id, request_id=request_id_var.get(), metadata={"version": 1, "steps": len(steps), "content_hash": version.content_hash})
    return workflow


async def create_workflow_version(db: AsyncSession, *, tenant_id: uuid.UUID, workflow_id: uuid.UUID, created_by: uuid.UUID, steps: list[dict], trigger_type: str, max_runtime_seconds: int | None = None, activate: bool = True) -> WorkflowVersion:
    workflow = await get_workflow(db, workflow_id=workflow_id, tenant_id=tenant_id)
    if not workflow.is_active:
        raise ValidationAppError("Workflow is inactive")
    await _validate_steps(db, tenant_id=tenant_id, steps=steps)
    current = await get_current_version(db, workflow_id=workflow.id)
    next_result = await db.execute(select(WorkflowVersion).where(WorkflowVersion.workflow_id == workflow.id).order_by(WorkflowVersion.version_number.desc()).limit(1))
    last = next_result.scalar_one_or_none()
    next_number = (last.version_number if last else 0) + 1
    snap = await _snapshot_steps(db, tenant_id=tenant_id, steps=steps)
    config = {"steps": steps, "max_runtime_seconds": max_runtime_seconds}
    contract = _execution_contract(version_number=next_number, steps=snap, max_runtime_seconds=max_runtime_seconds)
    if activate:
        await db.execute(update(WorkflowVersion).where(WorkflowVersion.workflow_id == workflow.id, WorkflowVersion.is_current.is_(True)).values(is_current=False))
    version = WorkflowVersion(workflow_id=workflow.id, version_number=next_number, is_current=activate, trigger_type=trigger_type, config=config, execution_contract=contract, content_hash=_content_hash(config, contract), created_by=created_by)
    db.add(version)
    await db.flush()
    await audit_service.record(db, action="workflow.version.created", actor_id=created_by, tenant_id=tenant_id, resource_type="workflow_version", resource_id=version.id, request_id=request_id_var.get(), metadata={"workflow_id": str(workflow.id), "version": next_number, "activated": activate, "content_hash": version.content_hash})
    return version


async def activate_workflow_version(db: AsyncSession, *, tenant_id: uuid.UUID, workflow_id: uuid.UUID, version_id: uuid.UUID, actor_id: uuid.UUID) -> WorkflowVersion:
    workflow = await get_workflow(db, workflow_id=workflow_id, tenant_id=tenant_id)
    result = await db.execute(select(WorkflowVersion).where(WorkflowVersion.id == version_id, WorkflowVersion.workflow_id == workflow.id))
    version = result.scalar_one_or_none()
    if version is None:
        raise NotFoundError("Workflow version not found")
    if version.is_current:
        return version
    await db.execute(update(WorkflowVersion).where(WorkflowVersion.workflow_id == workflow.id, WorkflowVersion.is_current.is_(True)).values(is_current=False))
    version.is_current = True
    await db.flush()
    await audit_service.record(db, action="workflow.version.activated", actor_id=actor_id, tenant_id=tenant_id, resource_type="workflow_version", resource_id=version.id, request_id=request_id_var.get(), metadata={"workflow_id": str(workflow.id), "version": version.version_number, "content_hash": version.content_hash})
    return version


async def get_workflow(db: AsyncSession, *, workflow_id: uuid.UUID, tenant_id: uuid.UUID) -> Workflow:
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == tenant_id))
    workflow = result.scalar_one_or_none()
    if workflow is None:
        raise NotFoundError("Workflow not found")
    return workflow


async def get_current_version(db: AsyncSession, *, workflow_id: uuid.UUID) -> WorkflowVersion:
    result = await db.execute(select(WorkflowVersion).where(WorkflowVersion.workflow_id == workflow_id, WorkflowVersion.is_current.is_(True)))
    version = result.scalar_one_or_none()
    if version is None:
        raise NotFoundError("Workflow has no current version")
    return version


async def create_workflow_run(db: AsyncSession, *, tenant_id: uuid.UUID, workflow_id: uuid.UUID, input_data: dict[str, Any], created_by: uuid.UUID, idempotency_key: str | None = None, workflow_version_id: uuid.UUID | None = None) -> WorkflowRun:
    workflow = await get_workflow(db, workflow_id=workflow_id, tenant_id=tenant_id)
    if idempotency_key:
        existing = await db.execute(select(WorkflowRun).where(WorkflowRun.tenant_id == tenant_id, WorkflowRun.workflow_id == workflow_id, WorkflowRun.idempotency_key == idempotency_key))
        existing_run = existing.scalar_one_or_none()
        if existing_run is not None:
            return existing_run
    if not workflow.is_active:
        raise ValidationAppError("Workflow is inactive")
    if workflow_version_id is not None:
        version_result = await db.execute(select(WorkflowVersion).where(WorkflowVersion.id == workflow_version_id, WorkflowVersion.workflow_id == workflow.id))
        version = version_result.scalar_one_or_none()
        if version is None:
            raise NotFoundError("Workflow version not found")
    else:
        version = await get_current_version(db, workflow_id=workflow.id)
    contract = dict(version.execution_contract or {})
    if contract.get("legacy"):
        # Materialize a run-local contract without mutating the immutable version.
        snap = await _snapshot_steps(db, tenant_id=tenant_id, steps=version.config.get("steps", []))
        contract = _execution_contract(version_number=version.version_number, steps=snap, max_runtime_seconds=version.config.get("max_runtime_seconds"), legacy=True)
    max_runtime = version.config.get("max_runtime_seconds")
    deadline = datetime.now(timezone.utc) + timedelta(seconds=int(max_runtime)) if max_runtime else None
    context = {"input": input_data, "steps": {}, "_workflow": {"dispatch_generation": 0, "workflow_version_number": version.version_number, "workflow_content_hash": version.content_hash, "execution_contract": contract}}
    run = WorkflowRun(tenant_id=tenant_id, workflow_id=workflow.id, workflow_version_id=version.id, created_by=created_by, status="pending", context=context, deadline_at=deadline, idempotency_key=idempotency_key)
    db.add(run)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        if idempotency_key:
            existing = await db.execute(select(WorkflowRun).where(WorkflowRun.tenant_id == tenant_id, WorkflowRun.workflow_id == workflow_id, WorkflowRun.idempotency_key == idempotency_key))
            existing_run = existing.scalar_one_or_none()
            if existing_run is not None:
                return existing_run
        raise
    await audit_service.record(db, action="workflow.run.created", actor_id=created_by, tenant_id=tenant_id, resource_type="workflow_run", resource_id=run.id, request_id=request_id_var.get(), metadata={"workflow_id": str(workflow.id), "workflow_version": version.version_number, "workflow_version_id": str(version.id), "content_hash": version.content_hash})
    return run


async def replay_workflow_run(db: AsyncSession, *, tenant_id: uuid.UUID, workflow_id: uuid.UUID, source_run_id: uuid.UUID, created_by: uuid.UUID, idempotency_key: str | None = None) -> WorkflowRun:
    """Create a replay using the exact immutable contract of the source run.

    Older RC8 runs may not have copied the contract into ``context`` even
    though their WorkflowVersion already contains the immutable execution
    contract. In that case we recover the contract from that exact version
    instead of resolving the workflow's current version. If neither location
    contains a non-legacy contract, replay is rejected because doing anything
    else could execute different Employee versions.
    """
    source = await get_workflow_run(db, workflow_run_id=source_run_id, tenant_id=tenant_id)
    if source.workflow_id != workflow_id:
        raise NotFoundError("Workflow run not found")

    # IMPORTANT: never use the workflow's current version for replay.
    # Replay must remain pinned to the version that produced the source run.
    version_result = await db.execute(
        select(WorkflowVersion).where(
            WorkflowVersion.id == source.workflow_version_id,
            WorkflowVersion.workflow_id == workflow_id,
        )
    )
    source_version = version_result.scalar_one_or_none()
    if source_version is None:
        raise NotFoundError("Source workflow version not found")

    source_context = dict(source.context or {})
    source_workflow_state = dict(source_context.get("_workflow") or {})

    # Prefer the run-local snapshot. This is the strongest guarantee because
    # it is the exact contract captured when the run was created.
    source_contract = dict(source_workflow_state.get("execution_contract") or {})

    # Backward-compatible recovery for runs created before the run-local
    # contract was persisted. The WorkflowVersion itself is immutable and is
    # therefore safe to use as the replay source.
    if not source_contract:
        source_contract = dict(source_version.execution_contract or {})

    if not source_contract:
        raise ValidationAppError(
            "Source run has no immutable execution contract and cannot be replayed safely"
        )

    # A legacy contract explicitly means that the version does not contain
    # immutable EmployeeVersion references. Do not silently re-snapshot it
    # during replay because that would change execution semantics.
    if source_contract.get("legacy"):
        raise ValidationAppError(
            "Source workflow version has a legacy execution contract and cannot be replayed safely"
        )

    contract_steps = source_contract.get("steps")
    if not isinstance(contract_steps, list) or not contract_steps:
        raise ValidationAppError(
            "Source workflow version has an invalid immutable execution contract"
        )

    # Replay is pinned to the exact WorkflowVersion used by the source run.
    # create_workflow_run normally copies that version's contract; we then
    # overwrite the run-local snapshot with the source contract to guarantee
    # that replay uses the same contract even for repaired/older runs.
    run = await create_workflow_run(
        db,
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        workflow_version_id=source.workflow_version_id,
        input_data=dict(source_context.get("input") or {}),
        created_by=created_by,
        idempotency_key=idempotency_key,
    )

    state = dict(run.context or {})
    wf = dict(state.get("_workflow") or {})
    wf["replay_of_run_id"] = str(source.id)
    wf["replay_source_version_id"] = str(source.workflow_version_id)
    wf["workflow_version_number"] = source_version.version_number
    wf["workflow_content_hash"] = source_version.content_hash
    wf["execution_contract"] = source_contract
    state["_workflow"] = wf
    run.context = state
    flag_modified(run, "context")

    await audit_service.record(
        db,
        action="workflow.run.replayed",
        actor_id=created_by,
        tenant_id=tenant_id,
        resource_type="workflow_run",
        resource_id=run.id,
        request_id=request_id_var.get(),
        metadata={
            "source_run_id": str(source.id),
            "workflow_version_id": str(source.workflow_version_id),
            "workflow_version": source_version.version_number,
            "content_hash": source_version.content_hash,
        },
    )
    return run


async def _enqueue_resume(db: AsyncSession, run: WorkflowRun, *, reason: str, delay_seconds: int = 0) -> None:
    state = dict(run.context or {})
    workflow_state = dict(state.get("_workflow") or {})
    generation = int(workflow_state.get("dispatch_generation", 0)) + 1
    workflow_state["dispatch_generation"] = generation
    state["_workflow"] = workflow_state
    run.context = state
    flag_modified(run, "context")
    available_at = datetime.now(timezone.utc) + timedelta(seconds=max(0, delay_seconds))
    await outbox_service.enqueue(db, kind="workflow.execute", tenant_id=run.tenant_id, payload={"workflow_run_id": str(run.id), "reason": reason, "generation": generation}, dedupe_key=f"workflow.execute:{run.id}:{generation}", available_at=available_at)


async def _execute_parallel_branch(branch_id: uuid.UUID) -> None:
    from app.core.database import worker_db_session
    async with worker_db_session() as db:
        result = await db.execute(select(WorkflowParallelBranchRun).where(WorkflowParallelBranchRun.id == branch_id).with_for_update())
        branch = result.scalar_one_or_none()
        if branch is None or branch.status == "success":
            return
        parent_result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == branch.workflow_run_id).with_for_update())
        parent = parent_result.scalar_one_or_none()
        if parent is None or parent.status in {"cancelled", "timed_out", "failed", "success"}:
            branch.status = "cancelled" if parent and parent.status == "cancelled" else "failed"
            await db.commit(); return
        branch.status = "running"; branch.started_at = branch.started_at or datetime.now(timezone.utc)
        await db.flush()
        outputs = {}
        try:
            for definition in branch.config.get("steps", []):
                if definition.get("type", "employee") != "employee":
                    raise ValidationAppError("Parallel branch supports employee steps only")
                step_input = _resolve_mapping(definition.get("input_mapping", {}), parent.context or {})
                if not step_input:
                    step_input = dict((parent.context or {}).get("input", {}))
                max_attempts = int(definition.get("retry_max", 0)) + 1
                child = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        child = await run_service.create_run(db, tenant_id=parent.tenant_id, employee_id=uuid.UUID(str(definition["employee_id"])), employee_version_id=uuid.UUID(str(definition["employee_version_id"])) if definition.get("employee_version_id") else None, input_data=step_input, created_by=parent.created_by)
                        await run_service.execute_run(db, run_id=child.id)
                        if child.status != "success":
                            raise RuntimeError(f"Employee Run ended with status {child.status}")
                        break
                    except Exception:
                        if attempt >= max_attempts:
                            raise
                        await db.flush()
                        await asyncio.sleep(min(30, 2 ** (attempt - 1)))
                outputs[definition.get("output_key") or definition["key"]] = child.output_data or {}
            branch.status = "success"; branch.output_data = outputs; branch.completed_at = datetime.now(timezone.utc)
            await _enqueue_resume(db, parent, reason=f"parallel_branch:{branch.branch_key}")
            await db.commit()
        except Exception as exc:
            branch.status = "failed"; branch.error = {"code": "PARALLEL_BRANCH_FAILED", "message": str(exc)[:1000]}; branch.completed_at = datetime.now(timezone.utc)
            await _enqueue_resume(db, parent, reason=f"parallel_branch_failed:{branch.branch_key}")
            await db.commit()
            raise


async def execute_workflow(db: AsyncSession, *, workflow_run_id: uuid.UUID) -> WorkflowRun:
    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == workflow_run_id).with_for_update())
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("Workflow run not found")
    version_result = await db.execute(select(WorkflowVersion).where(WorkflowVersion.id == run.workflow_version_id))
    version = version_result.scalar_one_or_none()
    if version is None:
        raise NotFoundError("Workflow version not found")
    workflow_state = dict((run.context or {}).get("_workflow") or {})
    contract = dict(workflow_state.get("execution_contract") or version.execution_contract or {})
    steps = contract.get("steps") or version.config.get("steps", [])
    context = run.context or {"input": {}, "steps": {}}
    context.setdefault("steps", {})
    start_position = int(context.get("_workflow", {}).get("next_position", 0))
    if run.status not in {"pending", "running", "waiting_approval"}:
        return run
    now = datetime.now(timezone.utc)
    if run.deadline_at and run.deadline_at <= now:
        run.status = "timed_out"
        run.error = {"code": "WORKFLOW_TIMEOUT", "message": "Workflow run exceeded its configured runtime."}
        run.completed_at = now
        await db.flush()
        await audit_service.record(db, action="workflow.run.timed_out", actor_type="system", tenant_id=run.tenant_id, resource_type="workflow_run", resource_id=run.id, status="failure", request_id=request_id_var.get(), metadata={"deadline_at": run.deadline_at.isoformat()})
        return run
    run.status = "running"
    if run.started_at is None:
        run.started_at = datetime.now(timezone.utc)
    await db.flush()
    try:
        for position in range(start_position, len(steps)):
            fresh = await db.execute(select(WorkflowRun.status, WorkflowRun.deadline_at).where(WorkflowRun.id == run.id))
            fresh_status, fresh_deadline = fresh.one()
            if fresh_status == "cancelled":
                run.status = "cancelled"
                return run
            if fresh_deadline and fresh_deadline <= datetime.now(timezone.utc):
                run.status = "timed_out"
                run.error = {"code": "WORKFLOW_TIMEOUT", "message": "Workflow run exceeded its configured runtime."}
                run.completed_at = datetime.now(timezone.utc)
                await db.flush()
                await audit_service.record(db, action="workflow.run.timed_out", actor_type="system", tenant_id=run.tenant_id, resource_type="workflow_run", resource_id=run.id, status="failure", request_id=request_id_var.get(), metadata={"deadline_at": fresh_deadline.isoformat()})
                return run
            definition = steps[position]
            step_key = definition["key"]
            existing_result = await db.execute(select(WorkflowStepRun).where(WorkflowStepRun.workflow_run_id == run.id, WorkflowStepRun.step_key == step_key))
            step = existing_result.scalar_one_or_none()
            if step is None:
                step = WorkflowStepRun(workflow_run_id=run.id, step_key=step_key, step_type=definition.get("type", "employee"), position=position, status="running", input_data={})
                db.add(step)
                await db.flush()
                WORKFLOW_STEPS.labels(step.step_type, "started").inc()
            elif step.status in {"success", "skipped"}:
                context["_workflow"] = {**context.get("_workflow", {}), "next_position": position + 1}
                flag_modified(run, "context")
                continue
            elif step.status == "retry_wait":
                if step.next_retry_at and step.next_retry_at > datetime.now(timezone.utc):
                    return run
                step.status = "running"
                step.next_retry_at = None
                WORKFLOW_STEPS.labels(step.step_type, "retry_started").inc()
                await db.flush()

            # Parallel fan-out: branches are durable records dispatched through the outbox.
            if definition.get("type") == "parallel":
                branch_result = await db.execute(select(WorkflowParallelBranchRun).where(WorkflowParallelBranchRun.workflow_step_run_id == step.id))
                branches = list(branch_result.scalars().all())
                if not branches:
                    for branch_def in definition.get("branches", []):
                        branch = WorkflowParallelBranchRun(workflow_run_id=run.id, workflow_step_run_id=step.id, branch_key=branch_def["key"], config={"steps": branch_def.get("steps", [])}, status="pending")
                        db.add(branch)
                    step.status = "waiting_parallel"
                    await db.flush()
                    branch_result = await db.execute(select(WorkflowParallelBranchRun).where(WorkflowParallelBranchRun.workflow_step_run_id == step.id))
                    branches = list(branch_result.scalars().all())
                    for branch in branches:
                        await outbox_service.enqueue(db, kind="workflow.parallel_branch", tenant_id=run.tenant_id, payload={"branch_id": str(branch.id)}, dedupe_key=f"workflow.parallel_branch:{branch.id}")
                    await db.flush()
                    return run
                if any(b.status == "failed" for b in branches):
                    step.status = "failed"; step.error = {"code": "PARALLEL_BRANCH_FAILED", "message": "One or more parallel branches failed."}; step.completed_at = datetime.now(timezone.utc)
                    run.status = "failed"; run.error = {"step": step_key, **step.error}; raise ValidationAppError(step.error["message"])
                if not all(b.status == "success" for b in branches):
                    step.status = "waiting_parallel"; await db.flush(); return run
                parallel_output = {b.branch_key: (b.output_data or {}) for b in branches}
                step.status = "success"; step.output_data = parallel_output; step.completed_at = datetime.now(timezone.utc)
                context["steps"][step_key] = parallel_output
                if definition.get("output_key"): context[definition["output_key"]] = parallel_output
                context["_workflow"] = {**context.get("_workflow", {}), "next_position": position + 1}
                flag_modified(run, "context"); await db.flush(); continue

            # Durable human approval: never block a worker; persist state and return.
            if definition.get("type") == "approval":
                approval_result = await db.execute(select(WorkflowApproval).where(WorkflowApproval.workflow_step_run_id == step.id).with_for_update())
                approval = approval_result.scalar_one_or_none()
                if approval is None:
                    timeout_seconds = int(definition.get("timeout_seconds", 86400))
                    approval = WorkflowApproval(tenant_id=run.tenant_id, workflow_run_id=run.id, workflow_step_run_id=step.id, step_key=step_key, status="pending", requested_by=run.created_by, metadata={"message": definition.get("message", "Approval required"), "metadata": definition.get("metadata", {})}, expires_at=datetime.now(timezone.utc) + timedelta(seconds=max(1, timeout_seconds)))
                    db.add(approval)
                    step.status = "waiting"
                    run.status = "waiting_approval"
                    context["_workflow"] = {"next_position": position, "waiting_approval_id": str(approval.id)}
                    flag_modified(run, "context")
                    await db.flush()
                    await audit_service.record(db, action="workflow.approval.requested", actor_type="system", tenant_id=run.tenant_id, resource_type="workflow_approval", resource_id=approval.id, request_id=request_id_var.get(), metadata={"workflow_run_id": str(run.id), "step_key": step_key, "expires_at": approval.expires_at.isoformat()})
                    return run
                if approval.status == "pending":
                    run.status = "waiting_approval"
                    context["_workflow"] = {"next_position": position, "waiting_approval_id": str(approval.id)}
                    flag_modified(run, "context")
                    await db.flush()
                    return run
                if approval.status == "rejected":
                    step.status = "failed"
                    step.error = {"code": "WORKFLOW_APPROVAL_REJECTED", "message": approval.decision_reason or "Human approval rejected the workflow step."}
                    step.completed_at = datetime.now(timezone.utc)
                    run.status = "failed"
                    run.error = {"step": step_key, **step.error}
                    raise ValidationAppError(step.error["message"])
                step.status = "success"
                step.output_data = {"approved": True, "decided_by": str(approval.decided_by) if approval.decided_by else None, "reason": approval.decision_reason}
                step.completed_at = datetime.now(timezone.utc)
                context["steps"][step_key] = step.output_data
                context["_workflow"] = {"next_position": position + 1}
                flag_modified(run, "context")
                await db.flush()
                continue

            if definition.get("condition_ref"):
                prior = context.get("steps", {}).get(definition["condition_ref"], {})
                expected = bool(definition.get("condition_value", True))
                if bool(prior.get("passed")) is not expected:
                    step.status = "skipped"; step.output_data = {"skipped_by": definition["condition_ref"]}; step.completed_at = datetime.now(timezone.utc)
                    context["steps"][step_key] = step.output_data; context["_workflow"] = {"next_position": position + 1}; flag_modified(run, "context"); await db.flush(); continue
            # An empty condition object is the default produced by the API schema
            # for ordinary steps. It must mean "no condition", not a condition
            # with an empty context path (which would raise Unsupported context path).
            if definition.get("condition"):
                condition_result = evaluate_condition(definition["condition"], context)
                expected = bool(definition.get("condition_value", True)); passed = condition_result is expected
                step.output_data = {"result": condition_result, "passed": passed}; step.status = "success" if passed else "skipped"; step.completed_at = datetime.now(timezone.utc)
                context["steps"][step_key] = step.output_data; context["_workflow"] = {"next_position": position + 1}; flag_modified(run, "context"); await db.flush(); continue
            if definition.get("type") == "condition":
                raise ValidationAppError("condition step requires condition definition")
            step_input = _resolve_mapping(definition.get("input_mapping", {}), context)
            if not step_input and position == 0: step_input = dict(context.get("input", {}))
            step.input_data = step_input
            max_attempts = int(definition.get("retry_max", 0)) + 1
            backoff_base = int(definition.get("metadata", {}).get("retry_backoff_seconds", 2))
            child = None
            attempt = max(1, int(step.attempt or 1))
            if step.employee_run_id:
                existing_child = await db.get(Run, step.employee_run_id)
                if existing_child is not None and existing_child.status == "success":
                    child = existing_child
            if child is None:
                try:
                    child = await run_service.create_run(db, tenant_id=run.tenant_id, employee_id=uuid.UUID(str(definition["employee_id"])), employee_version_id=uuid.UUID(str(definition["employee_version_id"])) if definition.get("employee_version_id") else None, input_data=step_input, created_by=run.created_by)
                    step.employee_run_id = child.id
                    await run_service.execute_run(db, run_id=child.id)
                    if child.status != "success":
                        raise RuntimeError(f"Employee Run ended with status {child.status}")
                except Exception as exc:
                    step.last_error = {"message": str(exc)[:1000], "attempt": attempt}
                    if attempt < max_attempts:
                        step.attempt = attempt + 1
                        step.status = "retry_wait"
                        delay = min(300, backoff_base * (2 ** (attempt - 1)))
                        step.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
                        await _enqueue_resume(db, run, reason=f"retry:{step_key}:{attempt + 1}", delay_seconds=delay)
                        await db.flush()
                        return run
                    raise
            assert child is not None
            output = child.output_data or {}
            step.output_data = output; step.status = "success"; step.completed_at = datetime.now(timezone.utc)
            context["steps"][step_key] = output
            if definition.get("output_key"): context[definition["output_key"]] = output
            context["_workflow"] = {"next_position": position + 1}
            flag_modified(run, "context")
            await db.flush()
        fresh = await db.execute(select(WorkflowRun.status).where(WorkflowRun.id == run.id))
        if fresh.scalar_one() == "cancelled":
            run.status = "cancelled"
            return run
        run.context = context
        run.output_data = context.get("steps", {})
        run.status = "success"
        run.completed_at = datetime.now(timezone.utc)
        await db.flush()
        await audit_service.record(db, action="workflow.run.completed", actor_type="system", tenant_id=run.tenant_id, resource_type="workflow_run", resource_id=run.id, status="success", request_id=request_id_var.get(), metadata={"status": run.status})
        return run
    except Exception:
        if run.status != "waiting_approval":
            run.status = "failed"
            run.completed_at = datetime.now(timezone.utc)
            await db.flush()
            await audit_service.record(db, action="workflow.run.completed", actor_type="system", tenant_id=run.tenant_id, resource_type="workflow_run", resource_id=run.id, status="failure", request_id=request_id_var.get(), metadata={"status": run.status})
        raise


async def get_workflow_run(db: AsyncSession, *, workflow_run_id: uuid.UUID, tenant_id: uuid.UUID) -> WorkflowRun:
    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == workflow_run_id, WorkflowRun.tenant_id == tenant_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("Workflow run not found")
    return run


async def cancel_workflow_run(db: AsyncSession, *, workflow_run_id: uuid.UUID, tenant_id: uuid.UUID, cancelled_by: uuid.UUID, reason: str | None = None) -> WorkflowRun:
    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == workflow_run_id, WorkflowRun.tenant_id == tenant_id).with_for_update())
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("Workflow run not found")
    if run.status in {"success", "failed", "cancelled", "timed_out"}:
        raise ValidationAppError(f"Workflow run is already terminal: {run.status}")
    now = datetime.now(timezone.utc)
    run.status = "cancelled"
    run.cancelled_at = now
    run.cancel_reason = reason
    run.completed_at = now
    run.error = {"code": "WORKFLOW_CANCELLED", "message": reason or "Workflow run cancelled by user."}
    await db.flush()
    await audit_service.record(db, action="workflow.run.cancelled", actor_type="user", actor_id=cancelled_by, tenant_id=tenant_id, resource_type="workflow_run", resource_id=run.id, status="success", request_id=request_id_var.get(), metadata={"reason": reason})
    return run


async def list_workflows(db, *, tenant_id):
    from sqlalchemy import select
    result = await db.execute(select(Workflow).where(Workflow.tenant_id == tenant_id).order_by(Workflow.created_at.desc()))
    return list(result.scalars().all())
