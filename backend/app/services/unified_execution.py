"""Unified execution service for human and specialized AI-agent work."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus


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

    async def dispatch(self, work_item: WorkItem) -> ExecutionResult:
        if work_item.status is WorkItemStatus.WAITING_APPROVAL:
            return ExecutionResult(work_item, False, True)
        if work_item.executor_type is None or work_item.executor_id is None:
            raise ExecutionError("work item has no executor")
        if self._requires_approval(work_item):
            work_item.status = WorkItemStatus.WAITING_APPROVAL
            return ExecutionResult(work_item, False, True)
        work_item.status = WorkItemStatus.RUNNING
        try:
            if work_item.executor_type is ExecutorType.HUMAN:
                if self.human_executor is None:
                    raise ExecutionError("human executor runtime is not configured")
                work_item.output_data = self.human_executor.dispatch(work_item)
            elif work_item.executor_type is ExecutorType.AGENT:
                if self.agent_executor is None:
                    raise ExecutionError("agent executor runtime is not configured")
                agent = await self.db.get(AgentInstance, work_item.executor_id)
                if agent is None or agent.tenant_id != work_item.tenant_id:
                    raise ExecutionError("agent executor is unavailable")
                if not agent.enabled or agent.status is not AgentInstanceStatus.ENABLED:
                    raise ExecutionError("agent executor is not available")
                work_item.output_data = self.agent_executor.dispatch(work_item, agent)
            else:
                raise ExecutionError("unsupported executor type")
            work_item.status = WorkItemStatus.SUCCEEDED
            return ExecutionResult(work_item, True)
        except Exception:
            work_item.status = WorkItemStatus.FAILED
            raise

    @staticmethod
    def _requires_approval(work_item: WorkItem) -> bool:
        return bool((work_item.policy_context or {}).get("requires_approval"))

    @staticmethod
    def _assert_assignable(work_item: WorkItem) -> None:
        if work_item.status in {WorkItemStatus.SUCCEEDED, WorkItemStatus.CANCELLED}:
            raise ExecutionError("terminal work items cannot be assigned")
