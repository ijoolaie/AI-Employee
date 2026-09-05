import uuid
from types import SimpleNamespace

import pytest

from app.ai.schemas import ChatResult, ToolCall
from app.core.exceptions import ValidationAppError
from app.models.run import Run
from app.services import run_service


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def first(self):
        return self.value


class _FakeDB:
    def __init__(self, run, version):
        self.run = run
        self.version = version
        self.execute_count = 0
        self.rollback_count = 0

    async def execute(self, _statement):
        self.execute_count += 1
        if self.execute_count == 1:
            return _ScalarResult(self.run)
        if self.execute_count == 2:
            return _ScalarResult(self.version)
        if self.execute_count == 3:
            return _ScalarResult(None)
        if self.execute_count == 4:
            return _ScalarResult(self.run)
        raise AssertionError(f"Unexpected db.execute call #{self.execute_count}")

    async def flush(self):
        return None

    async def rollback(self):
        self.rollback_count += 1
        return None

    async def commit(self):
        return None

    def add(self, _value):
        return None


class _FakeRegistry:
    def __init__(self, tool_names, requires_approval=False):
        self.execute_calls = []
        self.tools = {
            name: SimpleNamespace(
                name=name,
                description=f"test tool {name}",
                input_schema={"type": "object", "additionalProperties": True},
                required_permission="run.execute",
                requires_approval=requires_approval,
                definition=SimpleNamespace(
                    name=name,
                    description=f"test tool {name}",
                    input_schema={"type": "object", "additionalProperties": True},
                ),
            )
            for name in tool_names
        }

    def get(self, name):
        if name not in self.tools:
            raise AssertionError(f"Unexpected registry.get({name!r})")
        return self.tools[name]

    async def execute(self, name, arguments, **kwargs):
        self.execute_calls.append((name, arguments, kwargs))
        return {"ok": True}


class _FakeGateway:
    def __init__(self, tool_call=None):
        self.tool_call = tool_call
        self.calls = 0

    async def chat(self, *_args, **_kwargs):
        self.calls += 1
        if self.calls == 1 and self.tool_call is not None:
            return ChatResult(
                content="",
                prompt_tokens=1,
                completion_tokens=1,
                tool_calls=[self.tool_call],
            )
        return ChatResult(
            content="done",
            prompt_tokens=1,
            completion_tokens=1,
            tool_calls=[],
        )


def _fake_assembly(**_kwargs):
    return SimpleNamespace(messages=[], tools=[], metadata={})


def _make_run_and_version(allowed_tools):
    tenant_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    version_id = uuid.uuid4()
    run = Run(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        employee_id=employee_id,
        employee_version_id=version_id,
        created_by=None,
        status="pending",
        input_data={"request": "test"},
        request_id="guardrail-test",
        total_cost_usd=0,
    )
    version = SimpleNamespace(
        id=version_id,
        version_number=1,
        input_schema={},
        output_schema={},
        prompt_template="You are a test employee.",
        allowed_tools=list(allowed_tools),
        rules={},
    )
    return run, version


def _patch_execution_dependencies(monkeypatch, registry, gateway):
    monkeypatch.setattr(run_service, "registry", registry)
    monkeypatch.setattr(run_service, "AIGateway", lambda: gateway)
    monkeypatch.setattr(run_service, "assemble_employee_prompt", _fake_assembly)
    monkeypatch.setattr(run_service.audit_service, "record", _noop_audit)


@pytest.mark.asyncio
async def test_execute_run_blocks_model_requested_tool_outside_employee_allowlist(monkeypatch):
    run, version = _make_run_and_version(["allowed_tool"])
    db = _FakeDB(run, version)
    registry = _FakeRegistry(["allowed_tool", "blocked_tool"])
    gateway = _FakeGateway(ToolCall(id="call-blocked", name="blocked_tool", arguments={}))

    _patch_execution_dependencies(monkeypatch, registry, gateway)

    with pytest.raises(ValidationAppError, match="Tool is not allowed by Employee guardrails"):
        await run_service.execute_run(db, run_id=run.id)

    assert registry.execute_calls == []
    assert run.status == "failed"
    assert run.error_message.startswith("Tool is not allowed by Employee guardrails")
    assert db.rollback_count == 1


@pytest.mark.asyncio
async def test_execute_run_passes_employee_allowlist_to_registry_execution(monkeypatch):
    run, version = _make_run_and_version(["allowed_tool"])
    db = _FakeDB(run, version)
    registry = _FakeRegistry(["allowed_tool"])
    gateway = _FakeGateway(ToolCall(id="call-allowed", name="allowed_tool", arguments={"x": 1}))

    _patch_execution_dependencies(monkeypatch, registry, gateway)

    result = await run_service.execute_run(db, run_id=run.id)

    assert result.status == "success"
    assert len(registry.execute_calls) == 1
    name, arguments, kwargs = registry.execute_calls[0]
    assert name == "allowed_tool"
    assert arguments == {"x": 1}
    assert kwargs["allowed_tools"] == {"allowed_tool"}


@pytest.mark.asyncio
async def test_execute_run_blocks_disallowed_tool_before_approval(monkeypatch):
    run, version = _make_run_and_version(["allowed_tool"])
    db = _FakeDB(run, version)
    registry = _FakeRegistry(["allowed_tool", "blocked_tool"], requires_approval=True)
    gateway = _FakeGateway(ToolCall(id="call-blocked-approval", name="blocked_tool", arguments={}))
    approval_calls = []

    async def fake_create_request(*args, **kwargs):
        approval_calls.append((args, kwargs))
        return SimpleNamespace(id=uuid.uuid4())

    _patch_execution_dependencies(monkeypatch, registry, gateway)
    monkeypatch.setattr(run_service.approval_service, "create_request", fake_create_request)

    with pytest.raises(ValidationAppError, match="Tool is not allowed by Employee guardrails"):
        await run_service.execute_run(db, run_id=run.id)

    assert registry.execute_calls == []
    assert approval_calls == []
    assert run.status == "failed"


@pytest.mark.asyncio
async def test_execute_run_allowed_approval_tool_pauses_without_execution(monkeypatch):
    run, version = _make_run_and_version(["approval_tool"])
    db = _FakeDB(run, version)
    registry = _FakeRegistry(["approval_tool"], requires_approval=True)
    gateway = _FakeGateway(ToolCall(id="call-approval", name="approval_tool", arguments={"x": 1}))
    approval_calls = []

    async def fake_create_request(*args, **kwargs):
        approval_calls.append((args, kwargs))
        run.status = "waiting"
        return SimpleNamespace(id=uuid.uuid4())

    _patch_execution_dependencies(monkeypatch, registry, gateway)
    monkeypatch.setattr(run_service.approval_service, "create_request", fake_create_request)

    result = await run_service.execute_run(db, run_id=run.id)

    assert result.status == "waiting"
    assert registry.execute_calls == []
    assert len(approval_calls) == 1
    assert approval_calls[0][1]["tool_name"] == "approval_tool"


async def _noop_audit(*_args, **_kwargs):
    return None
