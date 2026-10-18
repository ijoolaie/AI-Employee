from __future__ import annotations

import hashlib
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.models.agent_evaluation import AgentEvaluationStatus
from app.workers import workforce_evaluation_worker as worker


def _db_result(value):
    return SimpleNamespace(scalar_one_or_none=lambda: value)


def _template(*, tenant_id, template_id, status="draft"):
    return SimpleNamespace(
        id=template_id,
        tenant_id=tenant_id,
        is_system_template=True,
        capability_contract={"workforce_role_code": "ai_software_developer"},
        status=status,
        version=3,
    )


def _install_worker_db(monkeypatch, db):
    @asynccontextmanager
    async def fake_worker_db_session():
        yield db

    monkeypatch.setattr(worker, "worker_db_session", fake_worker_db_session)


@pytest.mark.asyncio
async def test_workspace_worker_persists_failed_evaluation_when_acceptance_suite_raises(monkeypatch):
    tenant_id = uuid4()
    template_id = uuid4()
    template = _template(tenant_id=tenant_id, template_id=template_id)
    db = SimpleNamespace(
        execute=AsyncMock(return_value=_db_result(template)),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
    )
    _install_worker_db(monkeypatch, db)
    monkeypatch.setattr(
        worker,
        "run_software_developer_workspace_acceptance",
        AsyncMock(side_effect=RuntimeError("injected suite failure")),
    )
    audit = AsyncMock()
    monkeypatch.setattr(worker, "record", audit)

    evaluation_id = await worker._evaluate_workspace_async(
        tenant_id, template_id, evaluator_user_id=None, task_id="task-failed-123"
    )

    evaluation = db.add.call_args.args[0]
    assert evaluation_id == str(evaluation.id)
    assert evaluation.status == AgentEvaluationStatus.FAILED
    assert evaluation.score == 0
    assert evaluation.evidence["failure_type"] == "RuntimeError"
    assert evaluation.evidence["worker_execution"] is True
    assert evaluation.evidence["source"] == "celery_worker"
    assert evaluation.evidence["worker_task_id"] == "task-failed-123"
    assert evaluation.evidence["evidence_boundary"] == "local_workspace_artifact_only"
    assert evaluation.evidence_hash == hashlib.sha256(
        json.dumps(evaluation.evidence, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    assert template.status == "draft"
    db.flush.assert_awaited_once()
    db.commit.assert_awaited_once()
    audit.assert_awaited_once()
    assert audit.await_args.kwargs["status"] == "failure"
    assert audit.await_args.kwargs["metadata"]["evaluation_status"] == AgentEvaluationStatus.FAILED.value


@pytest.mark.asyncio
async def test_workspace_worker_pass_evidence_is_bound_to_worker_task_and_template(monkeypatch):
    tenant_id = uuid4()
    template_id = uuid4()
    template = _template(tenant_id=tenant_id, template_id=template_id)
    db = SimpleNamespace(
        execute=AsyncMock(return_value=_db_result(template)),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
    )
    _install_worker_db(monkeypatch, db)
    monkeypatch.setattr(
        worker,
        "run_software_developer_workspace_acceptance",
        AsyncMock(
            return_value={
                "suite_id": "software_developer_workspace_acceptance",
                "suite_version": "workspace_artifact_lifecycle_v1",
                "status": "passed",
                "checks_passed": 10,
                "evidence_boundary": "local_workspace_artifact_only",
            }
        ),
    )
    monkeypatch.setattr(worker, "record", AsyncMock())

    evaluation_id = await worker._evaluate_workspace_async(
        tenant_id, template_id, evaluator_user_id=None, task_id="task-passed-456"
    )

    evaluation = db.add.call_args.args[0]
    assert evaluation_id == str(evaluation.id)
    assert evaluation.status == AgentEvaluationStatus.PASSED
    assert evaluation.score == 100
    assert evaluation.evidence["worker_execution"] is True
    assert evaluation.evidence["source"] == "celery_worker"
    assert evaluation.evidence["worker_task_id"] == "task-passed-456"
    assert evaluation.evidence["template_id"] == str(template_id)
    assert evaluation.evidence["template_version"] == 3
    assert evaluation.evidence_hash == hashlib.sha256(
        json.dumps(evaluation.evidence, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_workspace_worker_rejects_non_draft_template_before_running_suite(monkeypatch):
    tenant_id = uuid4()
    template_id = uuid4()
    template = _template(tenant_id=tenant_id, template_id=template_id, status="published")
    db = SimpleNamespace(execute=AsyncMock(return_value=_db_result(template)), add=Mock())
    _install_worker_db(monkeypatch, db)
    suite = AsyncMock()
    monkeypatch.setattr(worker, "run_software_developer_workspace_acceptance", suite)

    with pytest.raises(ValueError, match="requires a draft template"):
        await worker._evaluate_workspace_async(
            tenant_id, template_id, evaluator_user_id=None, task_id="task-published-789"
        )

    suite.assert_not_awaited()
    db.add.assert_not_called()
