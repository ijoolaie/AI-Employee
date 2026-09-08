from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.models.agent_instance import AgentInstanceStatus
from app.workers import run_worker


@contextmanager
def _span(*_args, **_kwargs):
    yield


class _Db:
    def __init__(self, run, version, instance=None, identity=None):
        self.run = run
        self.version = version
        self.instance = instance
        self.identity = identity
        self.committed = False
        self.rolled_back = False

    async def execute(self, query):
        text = str(query)
        if "employee_versions" in text:
            return SimpleNamespace(scalar_one_or_none=lambda: self.version)
        if "agent_instances" in text:
            return SimpleNamespace(scalar_one_or_none=lambda: self.instance)
        if "agent_identities" in text:
            return SimpleNamespace(scalar_one_or_none=lambda: self.identity)
        if "tool_approval_requests" in text:
            return SimpleNamespace(scalars=lambda: SimpleNamespace(first=lambda: None))
        return SimpleNamespace(scalar_one_or_none=lambda: self.run)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def flush(self):
        return None


@asynccontextmanager
async def _session(db):
    yield db


def _run(run_id, tenant_id, *, agent_instance_id=None):
    return SimpleNamespace(
        id=run_id,
        tenant_id=tenant_id,
        employee_id=uuid4(),
        employee_version_id=uuid4(),
        agent_instance_id=agent_instance_id,
        created_by=None,
        input_data={},
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        status="queued",
        started_at=None,
        completed_at=None,
    )


def _employee_version():
    return SimpleNamespace(
        id=uuid4(),
        employee_id=uuid4(),
        version_number=1,
        rules={},
    )


def _agent_instance(tenant_id, agent_instance_id):
    return SimpleNamespace(
        id=agent_instance_id,
        tenant_id=tenant_id,
        status=AgentInstanceStatus.ENABLED,
        enabled=True,
    )


def _agent_identity(tenant_id, agent_instance_id):
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_instance_id=agent_instance_id,
        active=True,
        revoked_at=None,
        expires_at=None,
    )


def test_execute_run_task_requires_tenant_context():
    with pytest.raises(ValidationAppError):
        run_worker.execute_run_task(str(uuid4()), "")


def test_execute_run_task_rejects_invalid_context():
    with pytest.raises(ValidationAppError):
        run_worker.execute_run_task("not-a-uuid", str(uuid4()))


@pytest.mark.asyncio
async def test_run_worker_fails_closed_on_tenant_mismatch(monkeypatch):
    run_id = uuid4()
    owner_tenant = uuid4()
    supplied_tenant = uuid4()
    db = _Db(_run(run_id, owner_tenant), _employee_version())

    monkeypatch.setattr(run_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(run_worker, "span", _span)

    with pytest.raises(ValidationAppError):
        await run_worker._run_async(str(run_id), str(supplied_tenant))

    assert db.committed is False


@pytest.mark.asyncio
async def test_run_worker_blocks_queued_agent_run_when_kill_switch_is_active(monkeypatch):
    run_id = uuid4()
    tenant_id = uuid4()
    agent_instance_id = uuid4()
    run = _run(run_id, tenant_id, agent_instance_id=agent_instance_id)
    instance = _agent_instance(tenant_id, agent_instance_id)
    identity = _agent_identity(tenant_id, agent_instance_id)
    db = _Db(run, _employee_version(), instance, identity)

    async def _kill_switch(*_args, **_kwargs):
        raise ValidationAppError("Agent execution revoked by emergency kill switch")

    async def _memory(*_args, **_kwargs):
        raise AssertionError("memory must not be accessed after kill switch assertion")

    monkeypatch.setattr(run_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(run_worker, "span", _span)
    monkeypatch.setattr(run_worker, "assert_not_killed", _kill_switch)
    monkeypatch.setattr(run_worker, "build_runtime_memory", _memory)

    with pytest.raises(ValidationAppError, match="emergency kill switch"):
        await run_worker._run_async(str(run_id), str(tenant_id))

    assert db.committed is False


@pytest.mark.asyncio
async def test_run_worker_preserves_non_agent_run_compatibility_and_attribution(monkeypatch):
    run_id = uuid4()
    tenant_id = uuid4()
    run = _run(run_id, tenant_id)
    db = _Db(run, _employee_version())
    calls = []

    async def _execute(db_arg, *, run_id):
        calls.append((db_arg, run_id))

    async def _memory(*_args, **_kwargs):
        return []

    monkeypatch.setattr(run_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(run_worker, "span", _span)
    monkeypatch.setattr(run_worker, "build_runtime_memory", _memory)
    monkeypatch.setattr(run_worker.run_service, "execute_run", _execute)

    await run_worker._run_async(str(run_id), str(tenant_id))

    assert calls == [(db, run_id)]
    assert run.agent_instance_id is None
    assert db.committed is True
    assert run.total_tokens == run.prompt_tokens + run.completion_tokens


@pytest.mark.asyncio
async def test_run_worker_passes_matching_tenant_to_run_service(monkeypatch):
    run_id = uuid4()
    tenant_id = uuid4()
    run = _run(run_id, tenant_id)
    db = _Db(run, _employee_version())
    calls = []

    async def _execute(db_arg, *, run_id):
        calls.append((db_arg, run_id))

    async def _memory(*_args, **_kwargs):
        return []

    monkeypatch.setattr(run_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(run_worker, "span", _span)
    monkeypatch.setattr(run_worker.run_service, "execute_run", _execute)
    monkeypatch.setattr(run_worker, "build_runtime_memory", _memory)

    await run_worker._run_async(str(run_id), str(tenant_id))

    assert calls == [(db, run_id)]
    assert db.committed is True
    assert run.total_tokens == run.prompt_tokens + run.completion_tokens


@pytest.mark.asyncio
async def test_run_worker_commits_failure_before_reraising(monkeypatch):
    run_id = uuid4()
    tenant_id = uuid4()
    run = _run(run_id, tenant_id)
    db = _Db(run, _employee_version())

    async def _execute(_db_arg, *, run_id):
        raise RuntimeError(f"execution failed: {run_id}")

    async def _memory(*_args, **_kwargs):
        return []

    monkeypatch.setattr(run_worker, "worker_db_session", lambda: _session(db))
    monkeypatch.setattr(run_worker, "span", _span)
    monkeypatch.setattr(run_worker, "build_runtime_memory", _memory)
    monkeypatch.setattr(run_worker.run_service, "execute_run", _execute)

    with pytest.raises(RuntimeError, match="execution failed"):
        await run_worker._run_async(str(run_id), str(tenant_id))

    assert db.committed is True
