"""Fail-closed Agent-to-Agent delegation authorization."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.agent_delegation import AgentDelegation
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services import audit_service

DEFAULT_MAX_CHAIN_DEPTH = 3


def _scopes(agent: AgentInstance) -> tuple[set[str], set[str]]:
    policy = agent.permission_policy or {}
    tools = set(policy.get("allowed_tools") or policy.get("tools") or [])
    actions = set(policy.get("permissions") or [])
    return actions, tools


def _contains(scope: set[str], requested: set[str]) -> bool:
    return "*" in scope or requested.issubset(scope)


async def authorize_delegation(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    delegator_agent_instance_id: UUID,
    delegate_agent_instance_id: UUID,
    source_work_item_id: UUID,
    scopes: dict[str, Any],
    expires_at: datetime,
    max_chain_depth: int = DEFAULT_MAX_CHAIN_DEPTH,
) -> AgentDelegation:
    """Create delegation only when both identities and privilege bounds are valid."""
    if delegator_agent_instance_id == delegate_agent_instance_id:
        raise ValidationAppError("Agent cannot delegate to itself")
    if expires_at <= datetime.now(timezone.utc):
        raise ValidationAppError("Delegation must expire in the future")
    if max_chain_depth < 1 or max_chain_depth > DEFAULT_MAX_CHAIN_DEPTH:
        raise ValidationAppError("Delegation chain depth exceeds policy limit")

    source = (await db.execute(select(WorkItem).where(WorkItem.id == source_work_item_id, WorkItem.tenant_id == tenant_id))).scalar_one_or_none()
    if source is None:
        raise NotFoundError("Source work item not found for tenant")
    if source.executor_type is not ExecutorType.AGENT or source.executor_id != delegator_agent_instance_id:
        raise ValidationAppError("Source work item is not owned by delegating Agent")

    agents = (await db.execute(select(AgentInstance).where(AgentInstance.tenant_id == tenant_id, AgentInstance.id.in_([delegator_agent_instance_id, delegate_agent_instance_id])))).scalars().all()
    by_id = {agent.id: agent for agent in agents}
    delegator = by_id.get(delegator_agent_instance_id)
    delegate = by_id.get(delegate_agent_instance_id)
    if delegator is None or delegate is None:
        raise NotFoundError("Agent delegation target is not in tenant")
    for agent in (delegator, delegate):
        if not agent.enabled or agent.status is not AgentInstanceStatus.ENABLED:
            raise ValidationAppError("Delegation requires enabled Agent instances")

    identities = (await db.execute(select(AgentIdentity).where(AgentIdentity.tenant_id == tenant_id, AgentIdentity.agent_instance_id.in_([delegator.id, delegate.id])))).scalars().all()
    identity_by_agent = {identity.agent_instance_id: identity for identity in identities}
    for agent in (delegator, delegate):
        identity = identity_by_agent.get(agent.id)
        if identity is None or not identity.active or identity.revoked_at is not None:
            raise ValidationAppError("Delegation requires active Agent identities")
        if identity.expires_at is not None and identity.expires_at <= datetime.now(timezone.utc):
            raise ValidationAppError("Delegation requires non-expired Agent identities")

    requested_actions = set(scopes.get("actions") or [])
    requested_tools = set(scopes.get("tools") or [])
    if not requested_actions and not requested_tools:
        raise ValidationAppError("Delegation must grant an explicit non-empty scope")
    delegator_actions, delegator_tools = _scopes(delegator)
    delegate_actions, delegate_tools = _scopes(delegate)
    if not _contains(delegator_actions, requested_actions) or not _contains(delegator_tools, requested_tools):
        raise ValidationAppError("Delegation cannot exceed delegator authority")
    if not _contains(delegate_actions, requested_actions) or not _contains(delegate_tools, requested_tools):
        raise ValidationAppError("Delegation target cannot receive unsupported authority")

    parent_depth = int((source.policy_context or {}).get("delegation_depth", 0))
    depth = parent_depth + 1
    if depth > max_chain_depth:
        raise ValidationAppError("Delegation chain depth exceeded")

    delegation = AgentDelegation(
        tenant_id=tenant_id,
        delegator_agent_instance_id=delegator.id,
        delegate_agent_instance_id=delegate.id,
        source_work_item_id=source.id,
        scopes={"actions": sorted(requested_actions), "tools": sorted(requested_tools)},
        chain_depth=depth,
        max_chain_depth=max_chain_depth,
        correlation_id=str(uuid4()),
        status="active",
        expires_at=expires_at,
    )
    db.add(delegation)
    await db.flush()
    await audit_service.record(
        db,
        action="agent.delegation.created",
        actor_type="agent",
        actor_id=delegator.id,
        tenant_id=tenant_id,
        resource_type="agent_delegation",
        resource_id=delegation.id,
        metadata={"delegate_agent_instance_id": str(delegate.id), "source_work_item_id": str(source.id), "scopes": delegation.scopes, "chain_depth": depth, "expires_at": expires_at.isoformat()},
    )
    return delegation


async def create_delegated_work_item(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    source_work_item_id: UUID,
    delegator_agent_instance_id: UUID,
    delegate_agent_instance_id: UUID,
    scopes: dict[str, Any],
    expires_at: datetime,
    title: str | None = None,
    description: str | None = None,
    context: dict[str, Any] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
    max_chain_depth: int = DEFAULT_MAX_CHAIN_DEPTH,
) -> WorkItem:
    """Atomically establish delegation authority and bind it to the child WorkItem."""
    source = (await db.execute(select(WorkItem).where(WorkItem.id == source_work_item_id, WorkItem.tenant_id == tenant_id))).scalar_one_or_none()
    if source is None:
        raise NotFoundError("Source work item not found for tenant")
    delegation = await authorize_delegation(
        db,
        tenant_id=tenant_id,
        delegator_agent_instance_id=delegator_agent_instance_id,
        delegate_agent_instance_id=delegate_agent_instance_id,
        source_work_item_id=source.id,
        scopes=scopes,
        expires_at=expires_at,
        max_chain_depth=max_chain_depth,
    )
    parent_context = dict(source.policy_context or {})
    child_context = dict(parent_context)
    child_context.update({"delegated_from": str(source.id), "delegation_id": str(delegation.id), "delegation_depth": delegation.chain_depth})
    if context:
        child_context["delegation_context"] = context
    if artifacts:
        child_context["delegation_artifacts"] = artifacts
    child = WorkItem(
        tenant_id=source.tenant_id,
        title=title or source.title,
        description=description if description is not None else source.description,
        status=WorkItemStatus.WAITING_APPROVAL if parent_context.get("requires_approval") else WorkItemStatus.ASSIGNED,
        priority=source.priority,
        requester_id=source.requester_id,
        executor_type=ExecutorType.AGENT,
        executor_id=delegate_agent_instance_id,
        input_data={**(source.input_data or {}), "delegated_context": context or {}, "delegated_artifacts": artifacts or []},
        policy_context=child_context,
        idempotency_key=f"agent-delegation:{delegation.id}",
        parent_work_item_id=source.id,
    )
    db.add(child)
    await db.flush()
    delegation.delegated_work_item_id = child.id
    await db.flush()
    return child


async def validate_delegation(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    delegation_id: UUID,
    delegate_agent_instance_id: UUID,
    action: str | None = None,
    tool_name: str | None = None,
    now: datetime | None = None,
) -> AgentDelegation:
    """Validate an unforgeable delegation proof at the policy boundary."""
    current = now or datetime.now(timezone.utc)
    delegation = (await db.execute(select(AgentDelegation).where(AgentDelegation.id == delegation_id, AgentDelegation.tenant_id == tenant_id))).scalar_one_or_none()
    if delegation is None:
        raise ValidationAppError("Delegation not found for tenant")
    if delegation.status != "active":
        raise ValidationAppError("Delegation is not active")
    if delegation.delegate_agent_instance_id != delegate_agent_instance_id:
        raise ValidationAppError("Delegation target mismatch")
    if delegation.expires_at <= current:
        raise ValidationAppError("Delegation has expired")
    if delegation.chain_depth > delegation.max_chain_depth:
        raise ValidationAppError("Delegation chain depth exceeded")
    scopes = delegation.scopes or {}
    actions = set(scopes.get("actions") or [])
    tools = set(scopes.get("tools") or [])
    if action is not None and "*" not in actions and action not in actions:
        raise ValidationAppError("Delegated action is outside scope")
    if tool_name is not None and "*" not in tools and tool_name not in tools:
        raise ValidationAppError("Delegated tool is outside scope")
    return delegation
