"""Execution-time governance services for Agent evaluation, identity and tools."""
from __future__ import annotations

import hashlib
import json
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.agent_access_review import AgentAccessReview, AgentAccessReviewDecision
from app.models.agent_evaluation import AgentEvaluation, AgentEvaluationStatus
from app.models.agent_identity import AgentIdentity
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_template import AgentTemplate, AgentTemplateStatus


_agent_execution_context: ContextVar[tuple[uuid.UUID, uuid.UUID] | None] = ContextVar(
    "agent_execution_context", default=None
)


def _hash_evidence(evidence: dict[str, Any]) -> str:
    payload = json.dumps(evidence, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


@asynccontextmanager
async def governed_agent_execution(
    *, tenant_id: uuid.UUID, agent_instance_id: uuid.UUID
) -> AsyncIterator[None]:
    """Bind Agent identity to the current execution context.

    ToolRegistry uses this context as a final, centralized authorization hook.
    Context-local state prevents one concurrent tenant/agent execution from
    leaking its governance identity into another task.
    """
    token = _agent_execution_context.set((tenant_id, agent_instance_id))
    try:
        yield
    finally:
        _agent_execution_context.reset(token)


def current_agent_execution_context() -> tuple[uuid.UUID, uuid.UUID] | None:
    return _agent_execution_context.get()


async def record_evaluation(db: AsyncSession, *, tenant_id: uuid.UUID, template_id: uuid.UUID, suite_id: str, status: AgentEvaluationStatus, evidence: dict[str, Any], score: int | None, evaluator_user_id: uuid.UUID | None, notes: str | None = None) -> AgentEvaluation:
    template = (await db.execute(select(AgentTemplate).where(AgentTemplate.id == template_id, AgentTemplate.tenant_id == tenant_id))).scalar_one_or_none()
    if template is None:
        raise NotFoundError("Agent template not found")
    if template.status in {AgentTemplateStatus.PUBLISHED, AgentTemplateStatus.RETIRED}:
        raise ConflictError("Published or retired templates cannot receive new evaluation evidence")
    if score is not None and not 0 <= score <= 100:
        raise ValidationAppError("Evaluation score must be between 0 and 100")
    evaluation = AgentEvaluation(tenant_id=tenant_id, agent_template_id=template.id, suite_id=suite_id, status=status, score=score, evidence=evidence, evidence_hash=_hash_evidence(evidence), evaluator_user_id=evaluator_user_id, notes=notes)
    db.add(evaluation)
    template.status = AgentTemplateStatus.EVALUATING
    template.evaluation_policy = {**(template.evaluation_policy or {}), "latest_evaluation_id": str(evaluation.id), "passed": status == AgentEvaluationStatus.PASSED, "suite_id": suite_id, "score": score, "evidence_hash": evaluation.evidence_hash}
    await db.flush()
    await db.refresh(evaluation)
    return evaluation


async def latest_evaluation(db: AsyncSession, *, tenant_id: uuid.UUID, template_id: uuid.UUID) -> AgentEvaluation | None:
    result = await db.execute(select(AgentEvaluation).where(AgentEvaluation.tenant_id == tenant_id, AgentEvaluation.agent_template_id == template_id).order_by(AgentEvaluation.created_at.desc()).limit(1))
    return result.scalar_one_or_none()


async def assert_publishable_with_evidence(db: AsyncSession, *, tenant_id: uuid.UUID, template_id: uuid.UUID) -> AgentEvaluation:
    evidence = await latest_evaluation(db, tenant_id=tenant_id, template_id=template_id)
    if evidence is None or evidence.status != AgentEvaluationStatus.PASSED:
        raise ValidationAppError("Agent template requires its latest evaluation evidence to be passed before publication")
    return evidence


async def create_identity(db: AsyncSession, *, tenant_id: uuid.UUID, agent_instance_id: uuid.UUID, owner_user_id: uuid.UUID, sponsor_user_id: uuid.UUID, expires_at: datetime | None = None) -> AgentIdentity:
    existing = (await db.execute(select(AgentIdentity).where(AgentIdentity.agent_instance_id == agent_instance_id, AgentIdentity.tenant_id == tenant_id))).scalar_one_or_none()
    if existing is not None:
        return existing
    identity = AgentIdentity(tenant_id=tenant_id, agent_instance_id=agent_instance_id, owner_user_id=owner_user_id, sponsor_user_id=sponsor_user_id, subject=f"agent:{tenant_id}:{agent_instance_id}", expires_at=expires_at, active=True)
    db.add(identity)
    await db.flush()
    await db.refresh(identity)
    return identity


async def review_access(db: AsyncSession, *, tenant_id: uuid.UUID, identity_id: uuid.UUID, reviewer_user_id: uuid.UUID, decision: AgentAccessReviewDecision, next_review_at: datetime | None, reason: str | None) -> AgentAccessReview:
    identity = (await db.execute(select(AgentIdentity).where(AgentIdentity.id == identity_id, AgentIdentity.tenant_id == tenant_id))).scalar_one_or_none()
    if identity is None:
        raise NotFoundError("Agent identity not found")
    if reviewer_user_id in {identity.owner_user_id, identity.sponsor_user_id}:
        raise ValidationAppError("Access reviewer must be independent from the agent owner and sponsor")
    review = AgentAccessReview(tenant_id=tenant_id, agent_identity_id=identity.id, reviewer_user_id=reviewer_user_id, decision=decision, next_review_at=next_review_at, reason=reason)
    db.add(review)
    identity.active = decision == AgentAccessReviewDecision.APPROVED
    identity.revoked_at = None if identity.active else datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(review)
    return review


async def assert_agent_can_execute(db: AsyncSession, *, tenant_id: uuid.UUID, agent_instance_id: uuid.UUID, tool_name: str, required_permission: str, now: datetime | None = None) -> AgentInstance:
    now = now or datetime.now(timezone.utc)
    instance = (await db.execute(select(AgentInstance).where(AgentInstance.id == agent_instance_id, AgentInstance.tenant_id == tenant_id))).scalar_one_or_none()
    if instance is None:
        raise NotFoundError("Agent instance not found for tenant")
    if instance.status != AgentInstanceStatus.ENABLED or not instance.enabled:
        raise ValidationAppError("Agent instance is not executable")
    identity = (await db.execute(select(AgentIdentity).where(AgentIdentity.agent_instance_id == instance.id, AgentIdentity.tenant_id == tenant_id))).scalar_one_or_none()
    if identity is None or not identity.active or identity.revoked_at is not None:
        raise ValidationAppError("Agent identity is inactive or revoked")
    if identity.expires_at is not None and identity.expires_at <= now:
        identity.active = False
        await db.flush()
        raise ValidationAppError("Agent identity has expired")
    policy = instance.permission_policy or {}
    allowed_tools = set(policy.get("allowed_tools") or policy.get("tools") or [])
    permissions = set(policy.get("permissions") or [])
    if tool_name not in allowed_tools and "*" not in allowed_tools:
        raise ValidationAppError(f"Tool is not authorized for AgentInstance: {tool_name}", details={"tool": tool_name, "agent_instance_id": str(instance.id)})
    if required_permission not in permissions and "*" not in permissions:
        raise ValidationAppError(f"AgentInstance lacks required permission: {required_permission}", details={"tool": tool_name, "required_permission": required_permission})
    return instance
