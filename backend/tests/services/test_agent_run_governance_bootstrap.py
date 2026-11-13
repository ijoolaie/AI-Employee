from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import agent_run_governance_bootstrap as bootstrap


@pytest.mark.asyncio
async def test_agent_run_preflight_reestablishes_current_authority(monkeypatch):
    tenant_id = uuid4()
    agent_instance_id = uuid4()
    run_id = uuid4()
    calls = []

    async def fake_assert_authorized(db, request):
        calls.append((db, request))

    monkeypatch.setattr(bootstrap, "assert_authorized", fake_assert_authorized)
    run = SimpleNamespace(
        tenant_id=tenant_id,
        agent_instance_id=agent_instance_id,
        id=run_id,
    )
    db = object()

    await bootstrap.authorize_agent_run(db, run)

    assert len(calls) == 1
    _, request = calls[0]
    assert request.action == "run.execute"
    assert request.tenant_id == tenant_id
    assert request.agent_instance_id == agent_instance_id
    assert request.run_id == run_id
    assert request.tool_name is None
    assert request.required_permission is None


@pytest.mark.asyncio
async def test_agent_run_preflight_propagates_delegation_proof(monkeypatch):
    tenant_id = uuid4()
    agent_instance_id = uuid4()
    run_id = uuid4()
    delegation_id = uuid4()
    calls = []

    async def fake_assert_authorized(_db, request):
        calls.append(request)

    monkeypatch.setattr(bootstrap, "assert_authorized", fake_assert_authorized)
    run = SimpleNamespace(
        tenant_id=tenant_id,
        agent_instance_id=agent_instance_id,
        id=run_id,
        delegation_id=delegation_id,
    )

    await bootstrap.authorize_agent_run(object(), run)

    assert len(calls) == 1
    assert calls[0].delegation_id == delegation_id
    assert calls[0].action == "run.execute"


@pytest.mark.asyncio
async def test_agent_run_preflight_propagates_fail_closed_denial(monkeypatch):
    async def deny(_db, _request):
        raise RuntimeError("governance denied")

    monkeypatch.setattr(bootstrap, "assert_authorized", deny)
    run = SimpleNamespace(
        tenant_id=uuid4(),
        agent_instance_id=uuid4(),
        id=uuid4(),
    )

    with pytest.raises(RuntimeError, match="governance denied"):
        await bootstrap.authorize_agent_run(object(), run)

@pytest.mark.asyncio
async def test_run_service_rechecks_delegation_after_worker_preflight_before_execution(monkeypatch):
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.run import Run
    from app.services import run_service

    tenant_id = uuid4()
    agent_instance_id = uuid4()
    run_id = uuid4()
    delegation_id = uuid4()
    run = SimpleNamespace(
        id=run_id,
        tenant_id=tenant_id,
        agent_instance_id=agent_instance_id,
        delegation_id=delegation_id,
    )
    calls = []

    class _Result:
        def scalar_one_or_none(self):
            return run

    class _Session(AsyncSession):
        def __init__(self):
            pass

        async def execute(self, _statement):
            return _Result()

    async def original_execute(_db, *, run_id):
        calls.append(run_id)
        return SimpleNamespace(id=run_id)

    async def revoked_authority(_db, current_run):
        assert current_run.id == run_id
        assert current_run.delegation_id == delegation_id
        raise RuntimeError("delegation revoked after worker preflight")

    monkeypatch.setattr(run_service, "execute_run", original_execute)
    monkeypatch.setattr(bootstrap, "_INSTALLED", False)
    monkeypatch.setattr(bootstrap, "authorize_agent_run", revoked_authority)
    bootstrap.install()

    with pytest.raises(RuntimeError, match="revoked after worker preflight"):
        await run_service.execute_run(_Session(), run_id=run_id)

    assert calls == []
