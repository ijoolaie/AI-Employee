"""Fail-closed Agent-to-Agent delegation authorization."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.agent_access_review import AgentAccessReview, AgentAccessReviewDecision
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

    source = (
        await db.execute(
            select(WorkItem)
            .where(WorkItem.id == source_work_item_id, WorkItem.tenant_id == tenant_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if source is None:
        raise NotFoundError("Source work item not found for tenant")
    if source.status is WorkItemStatus.CANCELLED:
        raise ValidationAppError("Cannot create delegation from a cancelled source work item")
    if source.executor_type is not ExecutorType.AGENT or source.executor_id != delegator_agent_instance_id:
        raise ValidationAppError("Source work item is not owned by delegating Agent")

    parent_context = dict(source.policy_context or {})
    parent_delegation_id = parent_context.get("delegation_id")
    parent_delegation = None
    if parent_delegation_id is None and parent_context.get("delegated_from") is not None:
        raise ValidationAppError("Delegated source is missing its delegation proof")
    if parent_delegation_id is not None:
        try:
            parent_delegation_uuid = UUID(str(parent_delegation_id))
        except (TypeError, ValueError) as exc:
            raise ValidationAppError("Delegated source has an invalid delegation proof") from exc
        parent_delegation = (
            await db.execute(
                select(AgentDelegation)
                .where(
                    AgentDelegation.id == parent_delegation_uuid,
                    AgentDelegation.tenant_id == tenant_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if parent_delegation is None or parent_delegation.status != "active":
            raise ValidationAppError("Parent delegation is not active")
        if parent_delegation.expires_at <= datetime.now(timezone.utc):
            raise ValidationAppError("Parent delegation has expired")
        if expires_at > parent_delegation.expires_at:
            raise ValidationAppError("Delegation cannot outlive its parent")
        if parent_delegation.delegate_agent_instance_id != delegator_agent_instance_id:
            raise ValidationAppError("Delegation chain holder mismatch")
        if parent_delegation.delegated_work_item_id != source.id:
            raise ValidationAppError("Delegation chain source mismatch")
        if parent_context.get("delegation_depth") != parent_delegation.chain_depth:
            raise ValidationAppError("Delegation chain depth proof is inconsistent")

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
    if parent_delegation is not None:
        parent_scopes = parent_delegation.scopes or {}
        if not _contains(set(parent_scopes.get("actions") or []), requested_actions) or not _contains(set(parent_scopes.get("tools") or []), requested_tools):
            raise ValidationAppError("Delegation cannot expand the parent delegation scope")

    parent_depth = parent_delegation.chain_depth if parent_delegation is not None else 0
    if parent_delegation is None and int(parent_context.get("delegation_depth", 0)) != 0:
        raise ValidationAppError("Root delegation source has an invalid delegation depth")
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
        max_chain_depth=min(max_chain_depth, parent_delegation.max_chain_depth) if parent_delegation is not None else max_chain_depth,
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


async def revoke_delegation(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    delegation_id: UUID,
    actor_user_id: UUID,
) -> AgentDelegation:
    """Explicitly revoke an active delegation under a tenant-scoped row lock."""
    delegation = (
        await db.execute(
            select(AgentDelegation)
            .where(
                AgentDelegation.id == delegation_id,
                AgentDelegation.tenant_id == tenant_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if delegation is None:
        raise NotFoundError("Delegation not found for tenant")
    if delegation.status != "active":
        raise ValidationAppError("Delegation is not active")

    delegation.status = "revoked"
    await db.flush()
    await audit_service.record(
        db,
        action="agent.delegation.revoked",
        actor_type="user",
        actor_id=actor_user_id,
        tenant_id=tenant_id,
        resource_type="agent_delegation",
        resource_id=delegation.id,
        metadata={
            "delegator_agent_instance_id": str(delegation.delegator_agent_instance_id),
            "delegate_agent_instance_id": str(delegation.delegate_agent_instance_id),
            "source_work_item_id": str(delegation.source_work_item_id),
            "delegated_work_item_id": (
                str(delegation.delegated_work_item_id)
                if delegation.delegated_work_item_id is not None
                else None
            ),
            "chain_depth": delegation.chain_depth,
        },
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
    idempotency_key: str | None = None,
) -> WorkItem:
    """Atomically establish delegation authority and bind it to the child WorkItem."""
    if idempotency_key is None or not idempotency_key.strip():
        raise ValidationAppError("Delegation idempotency key is required")
    request_key = idempotency_key.strip()
    existing = (await db.execute(
        select(WorkItem).where(
            WorkItem.tenant_id == tenant_id,
            WorkItem.idempotency_key == request_key,
        ).with_for_update()
    )).scalar_one_or_none()
    if existing is not None:
        existing_delegation_id = (existing.policy_context or {}).get("delegation_id")
        if existing_delegation_id is None:
            raise ValidationAppError("Idempotency key is already bound to a non-delegation WorkItem")
        existing_delegation = (await db.execute(
            select(AgentDelegation).where(
                AgentDelegation.id == UUID(str(existing_delegation_id)),
                AgentDelegation.tenant_id == tenant_id,
            ).with_for_update()
        )).scalar_one_or_none()
        if existing_delegation is None:
            raise ValidationAppError("Idempotency key is bound to a missing delegation")
        requested_scopes = {"actions": sorted(set(scopes.get("actions") or [])), "tools": sorted(set(scopes.get("tools") or []))}
        if (
            existing.parent_work_item_id != source_work_item_id
            or existing.executor_id != delegate_agent_instance_id
            or existing_delegation.delegator_agent_instance_id != delegator_agent_instance_id
            or existing_delegation.scopes != requested_scopes
            or existing_delegation.expires_at != expires_at
        ):
            raise ValidationAppError("Idempotency key is already bound to a different delegation request")
        return existing

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
        idempotency_key=request_key,
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
    """Validate delegation proof and current governance state at execution time."""
    current = now or datetime.now(timezone.utc)
    delegation = (
        await db.execute(
            select(AgentDelegation)
            .where(AgentDelegation.id == delegation_id, AgentDelegation.tenant_id == tenant_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
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

    source = (
        await db.execute(
            select(WorkItem).where(
                WorkItem.id == delegation.source_work_item_id,
                WorkItem.tenant_id == tenant_id,
            ).with_for_update()
        )
    ).scalar_one_or_none()
    if source is None:
        raise ValidationAppError("Delegation source work item is unavailable")
    if source.status is WorkItemStatus.CANCELLED:
        raise ValidationAppError("Delegation is revoked because its source work item was cancelled")

    if delegation.delegated_work_item_id is not None:
        delegated_item = (
            await db.execute(
                select(WorkItem).where(
                    WorkItem.id == delegation.delegated_work_item_id,
                    WorkItem.tenant_id == tenant_id,
                ).with_for_update()
            )
        ).scalar_one_or_none()
        if delegated_item is None:
            raise ValidationAppError("Delegated work item is unavailable")
        if delegated_item.status is WorkItemStatus.CANCELLED:
            raise ValidationAppError("Delegation is revoked because its delegated work item was cancelled")

    # A child delegation remains executable only while every delegation in its
    # authority chain remains active. Checking only the leaf would allow a
    # revoked parent to continue authorizing descendants.
    ancestor = delegation
    ancestor_source = source
    for _ in range(DEFAULT_MAX_CHAIN_DEPTH):
        ancestor_context = dict(getattr(ancestor_source, "policy_context", None) or {})
        if ancestor_context.get("delegated_from") is None:
            break
        raw_parent_id = ancestor_context.get("delegation_id")
        if raw_parent_id is None:
            raise ValidationAppError("Delegated source is missing its delegation proof")
        try:
            parent_id = UUID(str(raw_parent_id))
        except (TypeError, ValueError) as exc:
            raise ValidationAppError("Delegated source has an invalid delegation proof") from exc
        parent = (
            await db.execute(
                select(AgentDelegation)
                .where(
                    AgentDelegation.id == parent_id,
                    AgentDelegation.tenant_id == tenant_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if parent is None or parent.status != "active":
            raise ValidationAppError("Delegation chain contains an inactive parent delegation")
        if parent.expires_at <= current:
            raise ValidationAppError("Delegation chain contains an expired parent delegation")
        if parent.delegate_agent_instance_id != ancestor.delegator_agent_instance_id:
            raise ValidationAppError("Delegation chain holder mismatch")
        if parent.delegated_work_item_id != ancestor_source.id:
            raise ValidationAppError("Delegation chain source mismatch")
        if parent.chain_depth != ancestor.chain_depth - 1:
            raise ValidationAppError("Delegation chain depth proof is inconsistent")

        ancestor_source = (
            await db.execute(
                select(WorkItem).where(
                    WorkItem.id == parent.source_work_item_id,
                    WorkItem.tenant_id == tenant_id,
                ).with_for_update()
            )
        ).scalar_one_or_none()
        if ancestor_source is None:
            raise ValidationAppError("Delegation ancestor source work item is unavailable")
        if ancestor_source.status is WorkItemStatus.CANCELLED:
            raise ValidationAppError("Delegation is revoked because an ancestor source work item was cancelled")
        ancestor = parent
    else:
        raise ValidationAppError("Delegation chain depth exceeded")

    agent_ids = [delegation.delegator_agent_instance_id, delegation.delegate_agent_instance_id]
    agents = (await db.execute(select(AgentInstance).where(AgentInstance.tenant_id == tenant_id, AgentInstance.id.in_(agent_ids)))).scalars().all()
    by_id = {agent.id: agent for agent in agents}
    for agent_id in agent_ids:
        agent = by_id.get(agent_id)
        if agent is None or not agent.enabled or agent.status is not AgentInstanceStatus.ENABLED:
            raise ValidationAppError("Delegation requires currently enabled Agent instances")

    identities = (await db.execute(select(AgentIdentity).where(AgentIdentity.tenant_id == tenant_id, AgentIdentity.agent_instance_id.in_(agent_ids)))).scalars().all()
    identity_by_agent = {identity.agent_instance_id: identity for identity in identities}
    for agent_id in agent_ids:
        identity = identity_by_agent.get(agent_id)
        if identity is None or not identity.active or identity.revoked_at is not None:
            raise ValidationAppError("Delegation requires currently active Agent identities")
        if identity.expires_at is not None and identity.expires_at <= current:
            raise ValidationAppError("Delegation identity has expired")

        latest_review = (await db.execute(
            select(AgentAccessReview)
            .where(
                AgentAccessReview.agent_identity_id == identity.id,
                AgentAccessReview.tenant_id == tenant_id,
            )
            .order_by(AgentAccessReview.reviewed_at.desc(), AgentAccessReview.id.desc())
            .limit(1)
        )).scalar_one_or_none()
        if latest_review is None or latest_review.decision is not AgentAccessReviewDecision.APPROVED:
            raise ValidationAppError("Delegation requires the latest Access Review to be approved")
        if latest_review.next_review_at is not None and latest_review.next_review_at <= current:
            raise ValidationAppError("Delegation requires a non-expired Access Review")

    scopes = delegation.scopes or {}
    actions = set(scopes.get("actions") or [])
    tools = set(scopes.get("tools") or [])
    if action is not None and "*" not in actions and action not in actions:
        raise ValidationAppError("Delegated action is outside scope")
    if tool_name is not None and "*" not in tools and tool_name not in tools:
        raise ValidationAppError("Delegated tool is outside scope")
    return delegation
