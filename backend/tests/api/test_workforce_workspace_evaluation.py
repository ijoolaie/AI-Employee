from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1 import agent_governance


def _result(value):
    return SimpleNamespace(scalar_one_or_none=lambda: value)


@pytest.mark.asyncio
async def test_workspace_acceptance_dispatches_only_server_owned_suite(monkeypatch):
    tenant_id = uuid4()
    user_id = uuid4()
    template_id = uuid4()
    template = SimpleNamespace(
        id=template_id,
        tenant_id=tenant_id,
        is_system_template=True,
        capability_contract={"workforce_role_code": "ai_software_developer"},
        status=SimpleNamespace(value="draft"),
    )
    db = SimpleNamespace(
        execute=AsyncMock(return_value=_result(template)),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )
    task = SimpleNamespace(id="worker-task-123")
    dispatch = SimpleNamespace(delay=Mock(return_value=task))
    monkeypatch.setattr(agent_governance, "evaluate_software_developer_workspace_task", dispatch)
    monkeypatch.setattr(agent_governance, "record", AsyncMock())

    result = await agent_governance.evaluate_software_developer_workspace(
        template_id,
        ctx=SimpleNamespace(tenant_id=tenant_id, user_id=user_id),
        db=db,
    )

    assert result.task_id == "worker-task-123"
    assert result.template_id == template_id
    assert result.status == "dispatched"
    assert result.suite_id == "software_developer_workspace_acceptance"
    dispatch.delay.assert_called_once_with(str(tenant_id), str(template_id), str(user_id))
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_workspace_acceptance_rejects_non_software_developer_template(monkeypatch):
    tenant_id = uuid4()
    template_id = uuid4()
    template = SimpleNamespace(
        id=template_id,
        tenant_id=tenant_id,
        is_system_template=True,
        capability_contract={"workforce_role_code": "ai_content_producer"},
        status=SimpleNamespace(value="draft"),
    )
    db = SimpleNamespace(execute=AsyncMock(return_value=_result(template)))
    dispatch = SimpleNamespace(delay=Mock())
    monkeypatch.setattr(agent_governance, "evaluate_software_developer_workspace_task", dispatch)

    with pytest.raises(HTTPException) as exc:
        await agent_governance.evaluate_software_developer_workspace(
            template_id,
            ctx=SimpleNamespace(tenant_id=tenant_id, user_id=uuid4()),
            db=db,
        )

    assert exc.value.status_code == 422
    dispatch.delay.assert_not_called()


@pytest.mark.asyncio
async def test_workspace_acceptance_rejects_non_draft_template(monkeypatch):
    tenant_id = uuid4()
    template_id = uuid4()
    template = SimpleNamespace(
        id=template_id,
        tenant_id=tenant_id,
        is_system_template=True,
        capability_contract={"workforce_role_code": "ai_software_developer"},
        status=SimpleNamespace(value="published"),
    )
    db = SimpleNamespace(execute=AsyncMock(return_value=_result(template)))
    dispatch = SimpleNamespace(delay=Mock())
    monkeypatch.setattr(agent_governance, "evaluate_software_developer_workspace_task", dispatch)

    with pytest.raises(HTTPException) as exc:
        await agent_governance.evaluate_software_developer_workspace(
            template_id,
            ctx=SimpleNamespace(tenant_id=tenant_id, user_id=uuid4()),
            db=db,
        )

    assert exc.value.status_code == 409
    dispatch.delay.assert_not_called()


def test_workspace_acceptance_worker_is_registered_and_routed():
    from app.workers.celery_app import EXECUTION_QUEUE, celery_app

    assert "app.workers.workforce_evaluation_worker" in celery_app.conf.include
    assert any(
        route.get("workforce.evaluate_software_developer_workspace", {}).get("queue") == EXECUTION_QUEUE
        for route in celery_app.conf.task_routes
        if isinstance(route, dict)
    )
