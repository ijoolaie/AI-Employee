"""Run service — implements the Employee execution model (11_Employee_Framework §5):

1. receive execution request + input          -> create_run()
2. load Employee definition + current version  -> create_run()
3. validate input against Input Schema         -> _validate_input()
4. check tenant quota/entitlements             -> billing_service.enforce_run_quota()
5. prepare Context for AI Core                 -> ExecutionContext / prompt_assembly
6. assemble Context/Prompt, then execute via AI Core -> app.ai.prompt_assembly -> AIGateway
7. validate output against Output Schema       -> validate_json_data()
8. Human Approval when required                -> approval state + explicit approved-tool resumption
9. store result, Trace, Cost                   -> execute_run() (ai_provider_calls + runs)
10. return output                              -> API layer

Prompt/Context assembly is implemented in app.ai.prompt_assembly; RunService
provides validated EmployeeVersion data and execution context, while the
Gateway remains the only provider boundary.

Human-in-the-loop is implemented in the run lifecycle: gated tool calls create
an approval request and pause execution; only an explicit approval decision can
resume the exact continuation, with tool authorization re-checked in the worker.
"""

from __future__ import annotations

import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import AIGateway
from app.ai.prompt_assembly import ExecutionContext, assemble_employee_prompt
from app.ai.schemas import ChatMessage, ChatRequest
from app.ai.tool_registry import registry
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.logging import request_id_var
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.tool_approval import ToolApprovalRequest
from app.models.conversation import CustomerMessage, CustomerConversation
from app.services import approval_service
from app.models.user import User
from app.models.role import Role
from app.services import audit_service, employee_service, billing_service
from app.services.schema_validation import validate_json_data
from app.rag import service as rag_service
from app.memory import service as memory_service
from app.memory.context import build_memory_query, memory_settings
from app.memory.auto_extract import extract_and_consolidate_run_memory, auto_memory_settings
from app.agents.planner import autonomy_settings, create_plan

logger = logging.getLogger("app.services.run")
settings = get_settings()


def _validate_input(input_data: dict[str, Any], input_schema: dict[str, Any]) -> None:
    """Validate Run input against the EmployeeVersion JSON Schema."""
    validate_json_data(input_data, input_schema, field_name="input_data")


def _message_to_json(message: ChatMessage) -> dict[str, Any]:
    return {
        "role": message.role,
        "content": message.content,
        "tool_calls": [
            {"id": call.id, "name": call.name, "arguments": call.arguments}
            for call in message.tool_calls
        ],
        "tool_call_id": message.tool_call_id,
    }


def _message_from_json(data: dict[str, Any]) -> ChatMessage:
    from app.ai.schemas import ToolCall
    return ChatMessage(
        role=data["role"],
        content=data.get("content", ""),
        tool_calls=[ToolCall(id=c["id"], name=c["name"], arguments=c.get("arguments", {})) for c in data.get("tool_calls", [])],
        tool_call_id=data.get("tool_call_id"),
    )


from app.rag.context import build_rag_query, rag_settings


async def create_run(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    input_data: dict[str, Any],
    created_by: uuid.UUID | None,
    employee_version_id: uuid.UUID | None = None,
) -> Run:
    employee = await employee_service.get_employee(db, employee_id=employee_id, tenant_id=tenant_id)
    if employee_version_id is not None:
        version_result = await db.execute(select(EmployeeVersion).where(EmployeeVersion.id == employee_version_id, EmployeeVersion.employee_id == employee.id))
        version = version_result.scalar_one_or_none()
        if version is None:
            raise NotFoundError("Employee version not found for employee")
    else:
        version = await employee_service.get_current_version(db, employee_id=employee.id)

    _validate_input(input_data, version.input_schema)
    await billing_service.enforce_run_quota(db, tenant_id=tenant_id)

    run = Run(
        tenant_id=tenant_id,
        employee_id=employee.id,
        employee_version_id=version.id,
        created_by=created_by,
        status="pending",
        input_data=input_data,
        request_id=request_id_var.get(),
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)

    await audit_service.record(
        db,
        action="run.created",
        actor_type="user" if created_by else "system",
        actor_id=created_by,
        tenant_id=tenant_id,
        resource_type="run",
        resource_id=run.id,
        request_id=request_id_var.get(),
        metadata={"employee_id": str(employee.id), "employee_version": version.version_number},
    )
    return run


async def execute_run(db: AsyncSession, *, run_id: uuid.UUID) -> Run:
    """Runs the Employee synchronously in-process. In production this body is
    what the Celery worker task (app.workers.run_worker) calls — kept as a
    plain function so it's callable directly (tests, sync fallback) or via
    the queue without duplicating logic."""
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("Run not found")

    # Idempotency guard: a Celery redelivery, duplicate enqueue, or explicit
    # re-invocation must never execute a terminal Run (and therefore must not
    # call the AI provider or side-effecting tools a second time). A Run that
    # is already running is likewise left alone; recovery/retry of an actually
    # lost worker is a separate lifecycle concern and must not be implemented
    # by blindly replaying an in-flight AI execution.
    if run.status in {"success", "failed", "cancelled", "running"}:
        logger.info(
            "run_execution_skipped_idempotent",
            extra={"run_id": str(run.id), "status": run.status},
        )
        return run

    version_result = await db.execute(
        select(EmployeeVersion).where(EmployeeVersion.id == run.employee_version_id)
    )
    version = version_result.scalar_one_or_none()
    if version is None:
        raise NotFoundError("Employee version not found for this run")

    # A waiting Run is resumable only through an explicit approval decision.
    approval_result = await db.execute(
        select(ToolApprovalRequest)
        .where(ToolApprovalRequest.run_id == run.id, ToolApprovalRequest.tenant_id == run.tenant_id)
        .order_by(ToolApprovalRequest.created_at.desc())
    )
    latest_approval = approval_result.scalars().first()
    if run.status == "waiting":
        if latest_approval is None or latest_approval.status == "pending":
            return run
        if latest_approval.status == "rejected":
            return run

    run.status = "running"
    if run.started_at is None:
        run.started_at = datetime.now(timezone.utc)
    await db.flush()

    # Re-authorize tool execution inside the worker. Endpoint RBAC alone is not
    # sufficient because Celery is a separate execution boundary.
    tool_permissions: set[str] = set()
    if run.created_by is not None:
        user_result = await db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == run.created_by, User.tenant_id == run.tenant_id)
        )
        run_user = user_result.scalar_one_or_none()
        if run_user is not None:
            if run_user.is_superuser:
                tool_permissions = {"*"}
            else:
                tool_permissions = {
                    permission.code
                    for role in run_user.roles
                    if role.tenant_id == run.tenant_id
                    for permission in role.permissions
                }

    gateway = AIGateway()
    paused_for_approval = False
    try:
        rules = version.rules or {}
        rag_config = rag_settings(rules)
        retrieved_context: list[dict[str, Any]] = []
        if rag_config["enabled"]:
            rag_query = build_rag_query(run.input_data, rag_config["query_fields"])
            retrieved_context = await rag_service.search(
                db, tenant_id=run.tenant_id, query=rag_query, top_k=rag_config["top_k"]
            )
            await audit_service.record(
                db, action="knowledge.retrieved", actor_type="system", tenant_id=run.tenant_id,
                resource_type="run", resource_id=run.id, status="success", request_id=run.request_id,
                metadata={"top_k": rag_config["top_k"], "result_count": len(retrieved_context), "query_fields": rag_config["query_fields"]},
            )

        memory_config = memory_settings(rules)
        memory_context: list[dict[str, Any]] = []
        if memory_config["enabled"]:
            memory_query = build_memory_query(run.input_data, memory_config["query_fields"])
            memory_context = await memory_service.search_memory(
                db, tenant_id=run.tenant_id, employee_id=run.employee_id, query=memory_query,
                top_k=memory_config["top_k"], min_score=memory_config["min_score"]
            )
            await audit_service.record(
                db, action="memory.retrieved", actor_type="system", tenant_id=run.tenant_id,
                resource_type="run", resource_id=run.id, status="success", request_id=run.request_id,
                metadata={"top_k": memory_config["top_k"], "result_count": len(memory_context), "query_fields": memory_config["query_fields"], "min_score": memory_config["min_score"]},
            )

        autonomy_config = autonomy_settings(rules)
        autonomous_plan = None
        if autonomy_config["enabled"]:
            try:
                plan = await create_plan(
                    gateway,
                    db,
                    tenant_id=run.tenant_id,
                    run_id=run.id,
                    model=settings.ai_default_model,
                    input_data=run.input_data,
                    prompt_template=version.prompt_template,
                    allowed_tools=version.allowed_tools or [],
                    max_steps=autonomy_config["max_steps"],
                )
                autonomous_plan = plan.as_context()
                await audit_service.record(
                    db,
                    action="run.autonomous_plan.created",
                    actor_type="system",
                    tenant_id=run.tenant_id,
                    resource_type="run",
                    resource_id=run.id,
                    status="success",
                    request_id=run.request_id,
                    metadata={
                        "plan_version": plan.version,
                        "goal": plan.goal,
                        "step_count": len(plan.steps),
                        "steps": [step.id for step in plan.steps],
                    },
                )
            except Exception as plan_exc:
                await audit_service.record(
                    db,
                    action="run.autonomous_plan.failed",
                    actor_type="system",
                    tenant_id=run.tenant_id,
                    resource_type="run",
                    resource_id=run.id,
                    status="failure",
                    request_id=run.request_id,
                    metadata={"error": str(plan_exc)[:1000]},
                )
                if autonomy_config["require_plan"]:
                    raise
                logger.warning("autonomous_plan_failed_continuing", extra={"run_id": str(run.id)})

        execution_context = ExecutionContext(
            input_data=run.input_data,
            rules=rules,
            retrieved_context=retrieved_context,
            memory=memory_context,
            autonomous_plan=autonomous_plan,
        )
        prompt_version = str(version.version_number)
        assembly = assemble_employee_prompt(
            prompt_template=version.prompt_template,
            prompt_version=prompt_version,
            context=execution_context,
            allowed_tools=version.allowed_tools or [],
        )
        messages = list(assembly.messages)
        employee_allowed_tools = set(version.allowed_tools or [])
        resume_approval = latest_approval if latest_approval is not None and latest_approval.status == "approved" else None
        if resume_approval is not None:
            messages = [_message_from_json(item) for item in resume_approval.continuation_messages]
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost_usd = 0.0
        tool_iterations = 0
        # Best-effort carry-through of the last executed Tool result so that
        # a structured artifact a Tool produces (e.g. Phase 2 Report Employee
        # `report_artifacts` file IDs from analyze_dataset) can be surfaced on
        # Run.output_data without changing the model-facing message protocol.
        # Only whitelisted keys are ever merged (see output_data assembly
        # below) — this never widens what an arbitrary Tool can inject.
        last_tool_result: dict[str, Any] | None = None

        while True:
            # Resume an approved gated tool call before asking the model for another turn.
            if resume_approval is not None:
                tool_call_name = resume_approval.tool_name
                tool_call_id = resume_approval.tool_call_id
                tool_status = "failure"
                tool_error = None
                tool_result: dict[str, Any] = {"error": "Tool execution failed"}
                started = datetime.now(timezone.utc)
                try:
                    tool = registry.get(tool_call_name)

                    if tool_call_name not in employee_allowed_tools:
                        raise ValidationAppError(
                            f"Tool is not allowed by Employee guardrails: {tool_call_name}",
                            details={
                                "tool": tool_call_name,
                                "allowed_tools": sorted(employee_allowed_tools),
                            },
                        )

                    effective_permissions = set(tool_permissions)
                    if "*" in effective_permissions:
                        effective_permissions.add(tool.required_permission)
                    tool_result = await registry.execute(
                        tool_call_name,
                        resume_approval.arguments,
                        permissions=effective_permissions,
                        approval_granted=True,
                        allowed_tools=employee_allowed_tools,
                        db=db,
                        tenant_id=run.tenant_id,
                        actor_id=run.created_by,
                    )
                    tool_status = "success"
                    resume_approval.status = "consumed"
                    if isinstance(tool_result, dict):
                        last_tool_result = tool_result
                    await db.flush()
                except Exception as exc:  # noqa: BLE001
                    tool_error = str(exc)[:1000]
                    tool_result = {"error": tool_error}
                    raise
                finally:
                    elapsed_ms = max(0, int((datetime.now(timezone.utc) - started).total_seconds() * 1000))
                    await audit_service.record(
                        db,
                        action="tool.call",
                        actor_type="system",
                        tenant_id=run.tenant_id,
                        resource_type="run",
                        resource_id=run.id,
                        status=tool_status,
                        request_id=run.request_id,
                        metadata={
                            "tool": tool_call_name,
                            "tool_call_id": tool_call_id,
                            "latency_ms": elapsed_ms,
                            "approval_id": str(resume_approval.id),
                            "approved": True,
                            "error": tool_error,
                        },
                    )
                messages.append(ChatMessage(role="tool", content=json.dumps(tool_result, ensure_ascii=False, default=str), tool_call_id=tool_call_id))
                resume_approval = None
                continue

            request = ChatRequest(
                messages=messages,
                model=settings.ai_default_model,
                tools=assembly.tools,
            )
            result = await gateway.chat(
                db,
                request,
                tenant_id=run.tenant_id,
                run_id=run.id,
                prompt_version=prompt_version,
                call_metadata={
                    **assembly.metadata,
                    "tool_iteration": tool_iterations,
                    "rag_enabled": rag_config["enabled"],
                    "rag_result_count": len(retrieved_context),
                },
            )
            total_prompt_tokens += result.prompt_tokens
            total_completion_tokens += result.completion_tokens
            total_cost_usd += result.cost_usd

            if not result.tool_calls:
                break

            tool_iterations += 1
            if tool_iterations > settings.ai_max_tool_iterations:
                raise ValidationAppError(
                    "Tool-call iteration limit exceeded",
                    details={"max_iterations": settings.ai_max_tool_iterations},
                )

            messages.append(
                ChatMessage(
                    role="assistant",
                    content=result.content,
                    tool_calls=result.tool_calls,
                )
            )

            for tool_call in result.tool_calls:
                started = datetime.now(timezone.utc)
                tool_status = "failure"
                tool_error = None
                tool_result: dict[str, Any] = {"error": "Tool execution failed"}
                try:
                    tool = registry.get(tool_call.name)

                    if tool_call.name not in employee_allowed_tools:
                        raise ValidationAppError(
                            f"Tool is not allowed by Employee guardrails: {tool_call.name}",
                            details={
                                "tool": tool_call.name,
                                "allowed_tools": sorted(employee_allowed_tools),
                            },
                        )

                    effective_permissions = set(tool_permissions)
                    if "*" in effective_permissions:
                        effective_permissions.add(tool.required_permission)
                    approval_required = await approval_service.requires_approval(
                        db,
                        tool=tool,
                        tenant_id=run.tenant_id,
                        employee_id=run.employee_id,
                    )
                    if approval_required:
                        continuation_messages = [_message_to_json(item) for item in messages]
                        approval = await approval_service.create_request(
                            db,
                            run=run,
                            tool_name=tool_call.name,
                            tool_call_id=tool_call.id,
                            arguments=tool_call.arguments,
                            continuation_messages=continuation_messages,
                        )
                        run.status = "waiting"
                        paused_for_approval = True
                        await audit_service.record(
                            db,
                            action="tool.approval_requested",
                            actor_type="system",
                            tenant_id=run.tenant_id,
                            resource_type="run",
                            resource_id=run.id,
                            status="pending",
                            request_id=run.request_id,
                            metadata={
                                "tool": tool_call.name,
                                "tool_call_id": tool_call.id,
                                "approval_id": str(approval.id),
                                "approved": False,
                            },
                        )
                        await db.flush()
                        break

                    tool_result = await registry.execute(
                        tool_call.name,
                        tool_call.arguments,
                        permissions=effective_permissions,
                        approval_granted=False,
                        allowed_tools=employee_allowed_tools,
                        db=db,
                        tenant_id=run.tenant_id,
                        actor_id=run.created_by,
                    )
                    tool_status = "success"
                    if isinstance(tool_result, dict):
                        last_tool_result = tool_result
                except Exception as exc:  # noqa: BLE001
                    tool_error = str(exc)[:1000]
                    tool_result = {"error": tool_error}
                    raise
                finally:
                    elapsed_ms = max(0, int((datetime.now(timezone.utc) - started).total_seconds() * 1000))
                    await audit_service.record(
                        db,
                        action="tool.call",
                        actor_type="system",
                        tenant_id=run.tenant_id,
                        resource_type="run",
                        resource_id=run.id,
                        status=tool_status,
                        request_id=run.request_id,
                        metadata={
                            "tool": tool_call.name,
                            "tool_call_id": tool_call.id,
                            "latency_ms": elapsed_ms,
                            "approval_required": approval_required if 'approval_required' in locals() else None,
                            "error": tool_error,
                        },
                    )

                if paused_for_approval:
                    break
                messages.append(
                    ChatMessage(
                        role="tool",
                        content=json.dumps(tool_result, ensure_ascii=False, default=str),
                        tool_call_id=tool_call.id,
                    )
                )

            if paused_for_approval:
                break

        if paused_for_approval:
            await db.flush()
            return run

        output_data = {"content": result.content}
        if last_tool_result and isinstance(last_tool_result.get("report_artifacts"), list):
            output_data["report_artifacts"] = last_tool_result["report_artifacts"]
        if last_tool_result and isinstance(last_tool_result.get("report_artifact"), dict):
            output_data["report_artifact"] = last_tool_result["report_artifact"]
        validate_json_data(output_data, version.output_schema, field_name="output_data")
        run.output_data = output_data
        run.status = "success"
        run.completed_at = datetime.now(timezone.utc)
        run.prompt_tokens = total_prompt_tokens
        run.completion_tokens = total_completion_tokens
        run.cost_usd = total_cost_usd
        await db.flush()
        await audit_service.record(
            db, action="run.completed", actor_type="system", tenant_id=run.tenant_id,
            resource_type="run", resource_id=run.id, status="success", request_id=run.request_id,
            metadata={"prompt_tokens": total_prompt_tokens, "completion_tokens": total_completion_tokens, "cost_usd": total_cost_usd},
        )
        await extract_and_consolidate_run_memory(db, run=run, output_data=output_data, settings=auto_memory_settings(version.rules or {}))
        await db.commit()
        return run
    except Exception as exc:  # noqa: BLE001
        await db.rollback()
        run_result = await db.execute(select(Run).where(Run.id == run_id))
        run = run_result.scalar_one_or_none()
        if run is not None:
            run.status = "failed"
            run.error_message = str(exc)[:2000]
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()
        raise
