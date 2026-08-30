"""Unified execution service for human and specialized AI-agent work."""

from __future__ import annotations

import inspect
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.execution_policy import ExecutionPolicy
from app.services.execution_telemetry import ExecutionEvent, ExecutionTelemetry


class ExecutionError(RuntimeError):
    """Raised when a work item cannot be dispatched safely."""


class HumanExecutor(Protocol):
    def dispatch(self, work_item: WorkItem) -> dict[str, Any]: ...


class AgentExecutor(Protocol):
    def dispatch(self, work_item: WorkItem, agent: AgentInstance) -> dict[str, Any]: ...


@dataclass
class ExecutionResult:
    work_item: WorkItem
    dispatched: bool
    waiting_for_approval: bool = False


class UnifiedExecutionService:
    """Canonical async dispatcher for human and specialized AI-agent execution."""

    def __init__(self, db: AsyncSession, *, human_executor: HumanExecutor | None = None, agent_executor: AgentExecutor | None = None) -> None:
        self.db = db
        self.human_executor = human_executor
        self.agent_executor = agent_executor
        self.telemetry = ExecutionTelemetry()

    def assign_human(self, work_item: WorkItem, executor_id: uuid.UUID) -> WorkItem:
        self._assert_assignable(work_item)
        work_item.executor_type = ExecutorType.HUMAN
        work_item.executor_id = executor_id
        work_item.status = WorkItemStatus.ASSIGNED
        return work_item

    async def assign_agent(self, work_item: WorkItem, agent: AgentInstance) -> WorkItem:
        self._assert_assignable(work_item)
        if agent.tenant_id != work_item.tenant_id:
            raise ExecutionError("cross-tenant agent assignment is forbidden")
        if not agent.enabled or agent.status is not AgentInstanceStatus.ENABLED:
            raise ExecutionError("agent instance is not available")
        work_item.executor_type = ExecutorType.AGENT
        work_item.executor_id = agent.id
        work_item.status = WorkItemStatus.ASSIGNED
        return work_item

    def delegate(self, work_item: WorkItem, *, actor_id: uuid.UUID, target_type: ExecutorType, target_id: uuid.UUID, title: str | None = None, description: str | None = None, context: dict[str, Any] | None = None, artifacts: list[dict[str, Any]] | None = None) -> WorkItem:
        if work_item.executor_id != actor_id or work_item.executor_type is None:
            raise ExecutionError("current executor is not authorized to delegate")
        if work_item.status not in {WorkItemStatus.ASSIGNED, WorkItemStatus.RUNNING}:
            raise ExecutionError("work item is not delegable")
        if target_id == actor_id and target_type is work_item.executor_type:
            raise ExecutionError("work item cannot be delegated to itself")
        parent_context = dict(work_item.policy_context or {})
        child_context = dict(parent_context)
        child_context["delegated_from"] = str(work_item.id)
        if context:
            child_context["delegation_context"] = context
        if artifacts:
            child_context["delegation_artifacts"] = artifacts
        child = WorkItem(
            tenant_id=work_item.tenant_id,
            title=title or work_item.title,
            description=description if description is not None else work_item.description,
            status=WorkItemStatus.WAITING_APPROVAL if parent_context.get("requires_approval") else WorkItemStatus.ASSIGNED,
            priority=work_item.priority,
            requester_id=work_item.requester_id,
            executor_type=target_type,
            executor_id=target_id,
            input_data={**(work_item.input_data or {}), "delegated_context": context or {}, "delegated_artifacts": artifacts or []},
            policy_context=child_context,
            idempotency_key=f"delegation:{work_item.id}:{target_type.value}:{target_id}:{uuid.uuid4()}",
            parent_work_item_id=work_item.id,
        )
        self.db.add(child)
        return child

    async def dispatch(self, work_item: WorkItem) -> ExecutionResult:
        if work_item.status is WorkItemStatus.WAITING_APPROVAL:
            return ExecutionResult(work_item, False, True)
        if work_item.executor_type is None or work_item.executor_id is None:
            raise ExecutionError("work item has no executor")
        policy = work_item.policy_context or {}
        policy_result = ExecutionPolicy.authorize(
            tenant_id=work_item.tenant_id, actor_tenant_id=work_item.tenant_id,
            capabilities=set(policy.get("capabilities", [])), required_capability=policy.get("required_capability"),
            tool=policy.get("tool"), allowed_tools=set(policy.get("allowed_tools", [])),
            budget_used=float(policy.get("budget_used", 0.0)), budget_limit=policy.get("budget_limit"),
            requires_approval=self._requires_approval(work_item), approved=bool(policy.get("approved")),
            active_executions=int(policy.get("active_executions", 0)), concurrency_limit=policy.get("concurrency_limit"),
            secret_names=set(policy.get("secret_names", [])), requested_secret=policy.get("requested_secret"), export_secret=bool(policy.get("export_secret")),
        )
        if policy_result.get("waiting_for_approval"):
            work_item.status = WorkItemStatus.WAITING_APPROVAL
            return ExecutionResult(work_item, False, True)
        if work_item.executor_type is ExecutorType.AGENT and work_item.status is WorkItemStatus.RUNNING and isinstance(work_item.output_data, dict) and work_item.output_data.get("run_id"):
            return ExecutionResult(work_item, False)
        work_item.status = WorkItemStatus.RUNNING
        started = self.telemetry.started()
        correlation_id = str(work_item.id)
        self.telemetry.emit(ExecutionEvent(tenant_id=work_item.tenant_id, work_item_id=work_item.id, event="started", correlation_id=correlation_id))
        try:
            if work_item.executor_type is ExecutorType.HUMAN:
                if self.human_executor is None:
                    raise ExecutionError("human executor runtime is not configured")
                work_item.output_data = await self._invoke(self.human_executor.dispatch, work_item)
                work_item.status = WorkItemStatus.RUNNING
            elif work_item.executor_type is ExecutorType.AGENT:
                if self.agent_executor is None:
                    raise ExecutionError("agent executor runtime is not configured")
                agent = await self.db.get(AgentInstance, work_item.executor_id)
                if agent is None or agent.tenant_id != work_item.tenant_id:
                    raise ExecutionError("agent executor is unavailable")
                if not agent.enabled or agent.status is not AgentInstanceStatus.ENABLED:
                    raise ExecutionError("agent executor is not available")
                output = await self._invoke(self.agent_executor.dispatch, work_item, agent)
                work_item.output_data = output
                work_item.status = self._agent_result_status(output)
            else:
                raise ExecutionError("unsupported executor type")
            self.telemetry.emit(ExecutionEvent(tenant_id=work_item.tenant_id, work_item_id=work_item.id, event="dispatched", duration_ms=self.telemetry.elapsed_ms(started), correlation_id=correlation_id))
            return ExecutionResult(work_item, True)
        except Exception:
            work_item.status = WorkItemStatus.FAILED
            self.telemetry.emit(ExecutionEvent(tenant_id=work_item.tenant_id, work_item_id=work_item.id, event="failed", duration_ms=self.telemetry.elapsed_ms(started), correlation_id=correlation_id))
            raise

    def cancel(self, work_item: WorkItem) -> WorkItem:
        if work_item.status in {WorkItemStatus.SUCCEEDED, WorkItemStatus.CANCELLED}:
            raise ExecutionError("terminal work item cannot be cancelled")
        if work_item.status is WorkItemStatus.DRAFT:
            raise ExecutionError("draft work item cannot be cancelled")
        work_item.status = WorkItemStatus.CANCELLED
        return work_item

    def retry(self, work_item: WorkItem) -> WorkItem:
        if work_item.status is not WorkItemStatus.FAILED:
            raise ExecutionError("only failed work items can be retried")
        if work_item.executor_type is None or work_item.executor_id is None:
            raise ExecutionError("failed work item has no executor")
        context = dict(work_item.policy_context or {})
        retry_count = int(context.get("retry_count", 0)) + 1
        max_retries = context.get("max_retries")
        if max_retries is not None and retry_count > int(max_retries):
            raise ExecutionError("maximum retry count exceeded")
        context["retry_count"] = retry_count
        work_item.policy_context = context
        work_item.output_data = None
        work_item.status = WorkItemStatus.ASSIGNED
        return work_item

    def complete_human(self, work_item: WorkItem, *, executor_id: uuid.UUID, output: dict[str, Any] | None = None) -> WorkItem:
        if work_item.executor_type is not ExecutorType.HUMAN:
            raise ExecutionError("work item is not assigned to a human")
        if work_item.executor_id != executor_id:
            raise ExecutionError("human executor does not own work item")
        if work_item.status not in {WorkItemStatus.ASSIGNED, WorkItemStatus.RUNNING}:
            raise ExecutionError("work item is not active")
        work_item.output_data = output or work_item.output_data or {}
        work_item.status = WorkItemStatus.SUCCEEDED
        return work_item

    def fail_human(self, work_item: WorkItem, *, executor_id: uuid.UUID, output: dict[str, Any] | None = None) -> WorkItem:
        if work_item.executor_type is not ExecutorType.HUMAN:
            raise ExecutionError("work item is not assigned to a human")
        if work_item.executor_id != executor_id:
            raise ExecutionError("human executor does not own work item")
        if work_item.status not in {WorkItemStatus.ASSIGNED, WorkItemStatus.RUNNING}:
            raise ExecutionError("work item is not active")
        if output is not None:
            work_item.output_data = output
        work_item.status = WorkItemStatus.FAILED
        return work_item

    @staticmethod
    def _agent_result_status(output: dict[str, Any] | None) -> WorkItemStatus:
        if isinstance(output, dict) and str(output.get("status", "")).lower() in {"failed", "failure", "error"}:
            return WorkItemStatus.FAILED
        if isinstance(output, dict) and str(output.get("status", "")).lower() in {"succeeded", "success", "completed", "complete"}:
            return WorkItemStatus.SUCCEEDED
        return WorkItemStatus.RUNNING

    @staticmethod
    async def _invoke(fn, *args):
        result = fn(*args)
        return await result if inspect.isawaitable(result) else result

    @staticmethod
    def _requires_approval(work_item: WorkItem) -> bool:
        return bool((work_item.policy_context or {}).get("requires_approval"))

    @staticmethod
    def _assert_assignable(work_item: WorkItem) -> None:
        if work_item.status in {WorkItemStatus.SUCCEEDED, WorkItemStatus.CANCELLED}:
            raise ExecutionError("terminal work items cannot be assigned")
