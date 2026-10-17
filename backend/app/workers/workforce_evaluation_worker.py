"""Trusted, provider-independent workforce acceptance execution."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from uuid import UUID

from sqlalchemy import select

from app.core.database import worker_db_session
from app.models.agent_evaluation import AgentEvaluation, AgentEvaluationStatus
from app.models.agent_template import AgentTemplate
from app.services.audit_service import record
from app.services.workforce_semantic_domains import run_software_developer_workspace_acceptance
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.workforce_evaluation")


def _evidence_hash(evidence: dict) -> str:
    payload = json.dumps(evidence, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


async def _evaluate_workspace_async(tenant_id: UUID, template_id: UUID, evaluator_user_id: UUID | None, task_id: str | None) -> str:
    async with worker_db_session() as db:
        template = (
            await db.execute(
                select(AgentTemplate).where(
                    AgentTemplate.id == template_id,
                    AgentTemplate.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if template is None:
            raise ValueError("first-party workforce template not found")
        role_code = (template.capability_contract or {}).get("workforce_role_code")
        if not template.is_system_template or role_code != "ai_software_developer":
            raise ValueError("workspace acceptance is only supported for the first-party Software Developer template")
        if getattr(template.status, "value", template.status) != "draft":
            raise ValueError("workspace acceptance requires a draft template")

        suite_id = "software_developer_workspace_acceptance"
        try:
            suite_result = await run_software_developer_workspace_acceptance(tenant_id=str(tenant_id))
            status = AgentEvaluationStatus.PASSED
            score = 100
            evidence = {
                **suite_result,
                "worker_execution": True,
                "source": "celery_worker",
                "worker_task_id": task_id,
                "template_id": str(template.id),
                "template_version": template.version,
            }
            notes = "Deterministic local workspace artifact acceptance passed; no provider-backed execution is claimed."
        except Exception as exc:
            status = AgentEvaluationStatus.FAILED
            score = 0
            evidence = {
                "suite_id": suite_id,
                "suite_version": "workspace_artifact_lifecycle_v1",
                "tenant_id": str(tenant_id),
                "worker_execution": True,
                "source": "celery_worker",
                "worker_task_id": task_id,
                "template_id": str(template.id),
                "template_version": template.version,
                "evidence_boundary": "local_workspace_artifact_only",
                "failure_type": type(exc).__name__,
            }
            notes = "Deterministic local workspace artifact acceptance failed; template remains draft."
            logger.exception("software_developer_workspace_acceptance_failed")

        evaluation = AgentEvaluation(
            tenant_id=tenant_id,
            agent_template_id=template.id,
            suite_id=suite_id,
            status=status,
            score=score,
            evidence=evidence,
            evidence_hash=_evidence_hash(evidence),
            evaluator_user_id=evaluator_user_id,
            notes=notes,
        )
        db.add(evaluation)
        await db.flush()
        await record(
            db,
            action="agent_template.workspace_acceptance_completed",
            actor_type="system",
            actor_id=None,
            tenant_id=tenant_id,
            resource_type="agent_template",
            resource_id=template.id,
            status="success" if status == AgentEvaluationStatus.PASSED else "failure",
            metadata={
                "evaluation_id": str(evaluation.id),
                "suite_id": suite_id,
                "suite_version": "workspace_artifact_lifecycle_v1",
                "evaluation_status": status.value,
                "worker_task_id": task_id,
                "evidence_hash": evaluation.evidence_hash,
                "evidence_boundary": "local_workspace_artifact_only",
            },
        )
        await db.commit()
        return str(evaluation.id)


@celery_app.task(bind=True, name="workforce.evaluate_software_developer_workspace")
def evaluate_software_developer_workspace_task(
    self,
    tenant_id: str,
    template_id: str,
    evaluator_user_id: str | None = None,
) -> str:
    """Run the fixed acceptance suite; no caller-provided test code or evidence is accepted."""
    task_id = getattr(self.request, "id", None)
    return asyncio.run(
        _evaluate_workspace_async(
            UUID(tenant_id),
            UUID(template_id),
            UUID(evaluator_user_id) if evaluator_user_id else None,
            task_id,
        )
    )
