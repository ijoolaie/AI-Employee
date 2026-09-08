from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.models.agent_instance import AgentInstanceStatus
from app.services.agent_governance import assert_agent_can_execute
from app.services import agent_execution_adapter


class _GovernanceDB:
    def __init__(self, instance, identity):
        self.instance = instance
        self.identity = identity
        self.flushed = False

    async def execute(self, query):
        text = str(query)
        if "agent_identities" in text:
            return SimpleNamespace(scalar_one_or_none=lambda: self.identity)
        return SimpleNamespace(scalar_one_or_none=lambda: self.instance)

    async def flush(self):
        self.flushed = True


@pytest.mark.asyncio
async def test_suspended_agent_cannot_execute():
    tenant_id = uuid4()
    instance = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        status=AgentInstanceStatus.SUSPENDED,
        enabled=False,
        permission_policy={"allowed_tools": ["ticket.read"], "permissions": ["tickets.read"]},
    )
    identity = SimpleNamespace(active=True, revoked_at=None, expires_at=None)

    with pytest.raises(ValidationAppError, match="agent_instance_not_executable"):
        await assert_agent_can_execute(
            _GovernanceDB(instance, identity),
            tenant_id=tenant_id,
            agent_instance_id=instance.id,
            tool_name="ticket.read",
            required_permission="tickets.read",
        )


@pytest.mark.asyncio
async def test_revoked_agent_identity_cannot_execute():
    tenant_id = uuid4()
    instance = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        status=AgentInstanceStatus.ENABLED,
        enabled=True,
        permission_policy={"allowed_tools": ["ticket.read"], "permissions": ["tickets.read"]},
    )
    identity = SimpleNamespace(active=False, revoked_at=datetime.now(timezone.utc), expires_at=None)

    with pytest.raises(ValidationAppError, match="agent_identity_revoked"):
        await assert_agent_can_execute(
            _GovernanceDB(instance, identity),
            tenant_id=tenant_id,
            agent_instance_id=instance.id,
            tool_name="ticket.read",
            required_permission="tickets.read",
        )


@pytest.mark.asyncio
async def test_expired_agent_identity_is_deactivated_and_cannot_execute():
    tenant_id = uuid4()
    instance = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        status=AgentInstanceStatus.ENABLED,
        enabled=True,
        permission_policy={"allowed_tools": ["ticket.read"], "permissions": ["tickets.read"]},
    )
    identity = SimpleNamespace(
        active=True,
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    db = _GovernanceDB(instance, identity)

    with pytest.raises(ValidationAppError, match="expired"):
        await assert_agent_can_execute(
            db,
            tenant_id=tenant_id,
            agent_instance_id=instance.id,
            tool_name="ticket.read",
            required_permission="tickets.read",
        )

    assert identity.active is False
    assert db.flushed is True


@pytest.mark.asyncio
async def test_cross_tenant_work_item_is_rejected_before_run_creation(monkeypatch):
    tenant_a = uuid4()
    tenant_b = uuid4()
    agent = SimpleNamespace(id=uuid4(), tenant_id=tenant_b, enabled=True)
    work_item = SimpleNamespace(tenant_id=tenant_a, input_data={}, requester_id=uuid4())

    async def resolve(*_args, **_kwargs):
        raise AssertionError("cross-tenant assignment must be rejected before resolver/Run")

    monkeypatch.setattr(agent_execution_adapter, "resolve_employee_version", resolve)

    with pytest.raises(ValueError, match="cross-tenant"):
        await agent_execution_adapter.AgentExecutionAdapter(object()).dispatch(work_item, agent)


@pytest.mark.asyncio
async def test_successful_agent_work_item_creates_agent_attributed_run(monkeypatch):
    tenant_id = uuid4()
    agent_id = uuid4()
    run_id = uuid4()
    definition_id = uuid4()
    employee_id = uuid4()
    version_id = uuid4()
    requester_id = uuid4()
    calls = {}

    work_item = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        input_data={"task": "triage"},
        requester_id=requester_id,
    )
    agent = SimpleNamespace(id=agent_id, tenant_id=tenant_id, enabled=True)
    instance = SimpleNamespace(id=agent_id)
    definition = SimpleNamespace(id=definition_id)
    version = SimpleNamespace(id=version_id, employee_id=employee_id)
    run = SimpleNamespace(id=run_id, agent_instance_id=None)

    async def resolve(db, *, tenant_id, agent_instance_id):
        calls["resolve"] = (db, tenant_id, agent_instance_id)
        return instance, definition, version

    async def create(db, **kwargs):
        calls["create"] = (db, kwargs)
        return run

    class _DB:
        async def flush(self):
            calls["flushed"] = True

    monkeypatch.setattr(agent_execution_adapter, "resolve_employee_version", resolve)
    monkeypatch.setattr(agent_execution_adapter, "create_run", create)
    monkeypatch.setattr(agent_execution_adapter, "execute_run_task", None, raising=False)

    async def _enqueue(*_args, **_kwargs):
        calls["enqueued"] = True

    class _Task:
        delay = staticmethod(_enqueue)

    monkeypatch.setattr(agent_execution_adapter, "execute_run_task", _Task(), raising=False)

    result = await agent_execution_adapter.AgentExecutionAdapter(_DB()).dispatch(work_item, agent)

    assert run.agent_instance_id == agent_id
    assert calls["flushed"] is True
    assert result["executor_type"] == "agent"
    assert result["agent_instance_id"] == str(agent_id)
    assert result["run_id"] == str(run_id)
