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
