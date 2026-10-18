from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.models.agent_evaluation import AgentEvaluationStatus
from app.services.agent_governance import assert_publishable_with_evidence, _hash_evidence


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _DB:
    def __init__(self, template, evaluation, trusted_audit=None):
        self.values = iter([template, evaluation, trusted_audit])

    async def execute(self, _statement):
        return _Result(next(self.values))


def _trusted_audit(tenant_id, template_id, evaluation):
    return SimpleNamespace(
        tenant_id=tenant_id,
        actor_type="system",
        action="agent_template.workspace_acceptance_completed",
        resource_type="agent_template",
        resource_id=str(template_id),
        status="success",
        ledger_sequence=1,
        entry_hash="server-created-ledger-hash",
        metadata_={
            "evaluation_id": str(evaluation.id),
            "worker_task_id": evaluation.evidence["worker_task_id"],
            "suite_id": "software_developer_workspace_acceptance",
            "suite_version": "workspace_artifact_lifecycle_v1",
            "evaluation_status": "passed",
            "evidence_hash": evaluation.evidence_hash,
            "evidence_boundary": "local_workspace_artifact_only",
        },
    )


def _valid_evidence(tenant_id, template_id, version):
    checks = [{"id": f"check_{i}", "passed": True} for i in range(10)]
    return {
        "suite_id": "software_developer_workspace_acceptance",
        "suite_version": "workspace_artifact_lifecycle_v1",
        "tenant_id": str(tenant_id),
        "status": "passed",
        "checks": checks,
        "checks_passed": 10,
        "evidence_boundary": "local_workspace_artifact_only",
        "provider_execution": "not_required",
        "external_side_effects": False,
        "worker_execution": True,
        "source": "celery_worker",
        "worker_task_id": "worker-task-123",
        "template_id": str(template_id),
        "template_version": version,
    }



@pytest.mark.asyncio
async def test_publishability_accepts_valid_worker_bound_workspace_evidence():
    tenant_id = uuid4()
    template_id = uuid4()
    template = SimpleNamespace(
        id=template_id,
        tenant_id=tenant_id,
        is_system_template=True,
        capability_contract={"workforce_role_code": "ai_software_developer"},
        evaluation_policy={},
        version=3,
    )
    evidence = _valid_evidence(tenant_id, template_id, template.version)
    evaluation = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_template_id=template_id,
        suite_id="software_developer_workspace_acceptance",
        status=AgentEvaluationStatus.PASSED,
        score=100,
        evidence=evidence,
        evidence_hash=_hash_evidence(evidence),
    )
    trusted_audit = _trusted_audit(tenant_id, template_id, evaluation)

    result = await assert_publishable_with_evidence(
        _DB(template, evaluation, trusted_audit), tenant_id=tenant_id, template_id=template_id
    )
    assert result is evaluation


@pytest.mark.asyncio
@pytest.mark.parametrize("mutation", [
    lambda evidence: evidence.update(source="caller"),
    lambda evidence: evidence.update(worker_execution=False),
    lambda evidence: evidence.update(tenant_id="another-tenant"),
    lambda evidence: evidence.update(template_id="another-template"),
    lambda evidence: evidence.update(worker_task_id=""),
    lambda evidence: evidence.update(checks_passed=9),
    lambda evidence: evidence.update(evidence_boundary="provider_execution"),
])
async def test_publishability_rejects_forged_or_mismatched_worker_evidence(mutation):
    tenant_id = uuid4()
    template_id = uuid4()
    template = SimpleNamespace(
        id=template_id,
        tenant_id=tenant_id,
        is_system_template=True,
        capability_contract={"workforce_role_code": "ai_software_developer"},
        evaluation_policy={},
        version=3,
    )
    evidence = _valid_evidence(tenant_id, template_id, template.version)
    mutation(evidence)
    # Hash is recomputed intentionally: integrity alone must not confer provenance.
    evaluation = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_template_id=template_id,
        suite_id="software_developer_workspace_acceptance",
        status=AgentEvaluationStatus.PASSED,
        score=100,
        evidence=evidence,
        evidence_hash=_hash_evidence(evidence),
    )

    with pytest.raises(ValidationAppError, match="verified worker-generated evaluation provenance"):
        await assert_publishable_with_evidence(
            _DB(template, evaluation), tenant_id=tenant_id, template_id=template_id
        )


@pytest.mark.asyncio
async def test_publishability_rejects_fully_matching_rehashed_payload_without_worker_audit():
    tenant_id = uuid4()
    template_id = uuid4()
    template = SimpleNamespace(
        id=template_id,
        tenant_id=tenant_id,
        is_system_template=True,
        capability_contract={"workforce_role_code": "ai_software_developer"},
        evaluation_policy={},
        version=3,
    )
    evidence = _valid_evidence(tenant_id, template_id, template.version)
    # Every caller-visible field is valid and the hash is recomputed, but there
    # is deliberately no server-owned completion event for this evaluation.
    evaluation = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_template_id=template_id,
        suite_id="software_developer_workspace_acceptance",
        status=AgentEvaluationStatus.PASSED,
        score=100,
        evidence=evidence,
        evidence_hash=_hash_evidence(evidence),
    )

    with pytest.raises(ValidationAppError, match="verified worker-generated evaluation provenance"):
        await assert_publishable_with_evidence(
            _DB(template, evaluation, trusted_audit=None),
            tenant_id=tenant_id,
            template_id=template_id,
        )


@pytest.mark.asyncio
async def test_publishability_rejects_first_party_roles_without_trusted_suite():
    tenant_id = uuid4()
    template_id = uuid4()
    template = SimpleNamespace(
        id=template_id,
        tenant_id=tenant_id,
        is_system_template=True,
        capability_contract={"workforce_role_code": "ai_content_producer"},
        evaluation_policy={},
    )
    evidence = {
        "worker_execution": True,
        "source": "celery_worker",
        "tenant_id": str(tenant_id),
        "template_id": str(template_id),
    }
    evaluation = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_template_id=template_id,
        suite_id="some-passed-suite",
        status=AgentEvaluationStatus.PASSED,
        score=100,
        evidence=evidence,
        evidence_hash=_hash_evidence(evidence),
    )

    with pytest.raises(ValidationAppError, match="verified worker-generated evaluation provenance"):
        await assert_publishable_with_evidence(
            _DB(template, evaluation), tenant_id=tenant_id, template_id=template_id
        )
