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
from app.services.agent_evaluation import EVALUATION_CONTRACT_VERSION
from app.services.agent_policy_engine import PolicyRequest, assert_authorized


_agent_execution_context: ContextVar[tuple[uuid.UUID, uuid.UUID, uuid.UUID | None, uuid.UUID | None, uuid.UUID | None] | None] = ContextVar(
    "agent_execution_context", default=None
)


def _hash_evidence(evidence: dict[str, Any]) -> str:
    payload = json.dumps(evidence, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


@asynccontextmanager
async def governed_agent_execution(
    *,
    tenant_id: uuid.UUID,
    agent_instance_id: uuid.UUID,
    run_id: uuid.UUID | None = None,
    employee_id: uuid.UUID | None = None,
    employee_version_id: uuid.UUID | None = None,
) -> AsyncIterator[None]:
    """Bind Agent identity and optional Run/Employee scope to the execution context."""
    token = _agent_execution_context.set(
        (tenant_id, agent_instance_id, run_id, employee_id, employee_version_id)
    )
    try:
        yield
    finally:
        _agent_execution_context.reset(token)


def current_agent_execution_context() -> tuple[uuid.UUID, uuid.UUID, uuid.UUID | None, uuid.UUID | None, uuid.UUID | None] | None:
    return _agent_execution_context.get()


async def record_evaluation(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    template_id: uuid.UUID,
    suite_id: str,
    status: AgentEvaluationStatus,
    evidence: dict[str, Any],
    score: int | None,
    evaluator_user_id: uuid.UUID | None,
    notes: str | None = None,
) -> AgentEvaluation:
    template = (await db.execute(select(AgentTemplate).where(AgentTemplate.id == template_id, AgentTemplate.tenant_id == tenant_id))).scalar_one_or_none()
    if template is None:
        raise NotFoundError("Agent template not found")
    if template.status in {AgentTemplateStatus.PUBLISHED, AgentTemplateStatus.RETIRED}:
        raise ConflictError("Published or retired templates cannot receive new evaluation evidence")
    if score is not None and not 0 <= score <= 100:
        raise ValidationAppError("Evaluation score must be between 0 and 100")

    policy = template.evaluation_policy or {}
    required_suite_id = policy.get("required_suite_id") or policy.get("suite_id")
    if required_suite_id and suite_id != required_suite_id:
        raise ValidationAppError("Evaluation suite does not match the template evaluation policy")
    minimum_score = policy.get("minimum_score")
    if status == AgentEvaluationStatus.PASSED and minimum_score is not None:
        if score is None or score < int(minimum_score):
            raise ValidationAppError("Passed evaluation does not meet the template minimum score")
    required_contract = policy.get("required_contract_version")
    contract_version = evidence.get("contract_version") or EVALUATION_CONTRACT_VERSION
    if required_contract and contract_version != required_contract:
        raise ValidationAppError("Evaluation evidence contract version does not match the template policy")

    evaluation = AgentEvaluation(
        tenant_id=tenant_id,
        agent_template_id=template.id,
        suite_id=suite_id,
        status=status,
        score=score,
        evidence={**evidence, "contract_version": contract_version},
        evaluator_user_id=evaluator_user_id,
        notes=notes,
    )
    evaluation.evidence_hash = _hash_evidence(evaluation.evidence)
    db.add(evaluation)
    await db.flush()

    template.status = AgentTemplateStatus.EVALUATING
    template.evaluation_policy = {
        **policy,
        "last_evaluation": {
            "id": str(evaluation.id),
            "passed": status == AgentEvaluationStatus.PASSED,
            "suite_id": suite_id,
            "score": score,
            "evidence_hash": evaluation.evidence_hash,
            "contract_version": contract_version,
        },
    }
    await db.flush()
    await db.refresh(evaluation)
    return evaluation


async def latest_evaluation(db: AsyncSession, *, tenant_id: uuid.UUID, template_id: uuid.UUID) -> AgentEvaluation | None:
    result = await db.execute(
        select(AgentEvaluation)
        .where(AgentEvaluation.tenant_id == tenant_id, AgentEvaluation.agent_template_id == template_id)
        .order_by(AgentEvaluation.created_at.desc(), AgentEvaluation.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def assert_publishable_with_evidence(db: AsyncSession, *, tenant_id: uuid.UUID, template_id: uuid.UUID) -> AgentEvaluation:
    template = (await db.execute(select(AgentTemplate).where(AgentTemplate.id == template_id, AgentTemplate.tenant_id == tenant_id))).scalar_one_or_none()
    if template is None:
        raise NotFoundError("Agent template not found")
    evidence = await latest_evaluation(db, tenant_id=tenant_id, template_id=template_id)
    if evidence is None or evidence.status != AgentEvaluationStatus.PASSED:
        raise ValidationAppError("Agent template requires its latest evaluation evidence to be passed before publication")

    policy = template.evaluation_policy or {}
    required_suite_id = policy.get("required_suite_id") or policy.get("suite_id")
    if required_suite_id and evidence.suite_id != required_suite_id:
        raise ValidationAppError("Latest evaluation suite does not satisfy the template evaluation policy")
    minimum_score = policy.get("minimum_score")
    if minimum_score is not None and (evidence.score is None or evidence.score < int(minimum_score)):
        raise ValidationAppError("Latest evaluation score does not satisfy the template minimum score")
    required_contract = policy.get("required_contract_version")
    if required_contract and evidence.evidence.get("contract_version") != required_contract:
        raise ValidationAppError("Latest evaluation contract version does not satisfy the template policy")
    return evidence


async def create_identity(db: AsyncSession, *, tenant_id: uuid.UUID, agent_instance_id: uuid.UUID, owner_user_id: uuid.UUID, sponsor_user_id: uuid.UUID, expires_at: datetime | None = None) -> AgentIdentity:
    existing = (await db.execute(select(AgentIdentity).where(AgentIdentity.agent_instance_id == agent_instance_id, AgentIdentity.tenant_id == tenant_id))).scalar_one_or_none()
    if existing is not None:
        return existing
    if not owner_user_id or not sponsor_user_id:
        raise ValidationAppError("Agent identity requires an attributable owner and sponsor")
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

    instance = (await db.execute(select(AgentInstance).where(
        AgentInstance.id == identity.agent_instance_id,
        AgentInstance.tenant_id == tenant_id,
    ).with_for_update())).scalar_one_or_none()
    if instance is None:
        raise NotFoundError("Agent instance not found for identity")
    if decision == AgentAccessReviewDecision.APPROVED and instance.status != AgentInstanceStatus.SUSPENDED:
        raise ConflictError("Approved access review cannot grant execution authority to an active AgentInstance; use governed workforce activation")

    review = AgentAccessReview(tenant_id=tenant_id, agent_identity_id=identity.id, reviewer_user_id=reviewer_user_id, decision=decision, next_review_at=next_review_at, reason=reason)
    db.add(review)
    identity.active = decision == AgentAccessReviewDecision.APPROVED
    identity.revoked_at = None if identity.active else datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(review)
    return review


async def assert_agent_can_execute(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_instance_id: uuid.UUID,
    tool_name: str,
    required_permission: str,
    now: datetime | None = None,
    approval_granted: bool = False,
    requires_approval: bool = False,
    run_id: uuid.UUID | None = None,
    tool_call_id: str | None = None,
    approval_request_id: uuid.UUID | None = None,
    arguments: dict[str, Any] | None = None,
    delegation_id: uuid.UUID | None = None,
) -> AgentInstance:
    """Authorize a tool invocation through the central policy decision kernel."""
    return await assert_authorized(
        db,
        PolicyRequest(
            tenant_id=tenant_id,
            agent_instance_id=agent_instance_id,
            action="tool.execute",
            tool_name=tool_name,
            required_permission=required_permission,
            now=now,
            approval_granted=approval_granted,
            requires_approval=requires_approval,
            run_id=run_id,
            tool_call_id=tool_call_id,
            approval_request_id=approval_request_id,
            arguments=arguments,
            delegation_id=delegation_id,
        ),
    )
