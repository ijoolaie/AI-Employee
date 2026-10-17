from __future__ import annotations

import hashlib
import json
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
    def __init__(self, template, evaluation):
        self.values = iter([template, evaluation])

    async def execute(self, _statement):
        return _Result(next(self.values))


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


def _fixtures(evidence):
    tenant_id = uuid4()
    template_id = uuid4()
    template = SimpleNamespace(
        id=template_id,
        tenant_id=tenant_id,
        is_system_template=True,
        capability_contract={"workforce_role_code": "ai_software_developer"},
        evaluation_policy={},
    )
    evidence["tenant_id"] = str(tenant_id)
    evidence["template_id"] = str(template_id)
    evidence["template_version"] = template.version = 3
    evaluation = SimpleNamespace(
        tenant_id=tenant_id,
        agent_template_id=template_id,
        suite_id="software_developer_workspace_acceptance",
        status=AgentEvaluationStatus.PASSED,
        score=100,
        evidence=evidence,
        evidence_hash=_hash_evidence(evidence),
    )
    return tenant_id, template_id, template, evaluation


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
        tenant_id=tenant_id,
        agent_template_id=template_id,
        suite_id="software_developer_workspace_acceptance",
        status=AgentEvaluationStatus.PASSED,
        score=100,
        evidence=evidence,
        evidence_hash=_hash_evidence(evidence),
    )

    result = await assert_publishable_with_evidence(
        _DB(template, evaluation), tenant_id=tenant_id, template_id=template_id
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
