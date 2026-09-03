import asyncio

import pytest

from app.agents.runtime import AgentRuntime, RuntimeState
from app.agents.runtime_contract import AgentRuntimeContract, RetryPolicy
from app.core import telemetry


def _contract(**overrides):
    values = {
        "tenant_id": "tenant-1",
        "run_id": "run-1",
        "employee_id": "employee-1",
        "employee_version_id": "version-1",
        "input_data": {"prompt": "secret prompt"},
        "approval_state": "granted",
        "approval_id": "approval-1",
        "memory": [{"text": "secret memory", "embedding": [1, 2, 3]}],
        "retry": RetryPolicy(max_attempts=2),
        "timeout_seconds": 1,
    }
    values.update(overrides)
    return AgentRuntimeContract(**values)


@pytest.mark.asyncio
async def test_runtime_success_emits_only_safe_attributes(monkeypatch):
    captured = {}

    class FakeSpan:
        def set_attribute(self, key, value):
            captured[key] = value

    class FakeContext:
        def __enter__(self):
            return FakeSpan()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(telemetry, "span", lambda name, **attrs: (captured.update(attrs) or FakeContext()))

    result = await AgentRuntime(_contract()).execute(lambda: asyncio.sleep(0, result="ok"))

    assert result.state is RuntimeState.SUCCEEDED
    assert result.outcome == "succeeded"
    assert captured["run.id"] == "run-1"
    assert captured["tenant.id"] == "tenant-1"
    assert captured["employee.version.id"] == "version-1"
    assert captured["approval.id"] == "approval-1"
    assert "secret prompt" not in repr(captured)
    assert "secret memory" not in repr(captured)
    assert "embedding" not in repr(captured)


@pytest.mark.asyncio
async def test_runtime_timeout_is_distinguishable(monkeypatch):
    captured = {}

    class FakeSpan:
        def set_attribute(self, key, value):
            captured[key] = value

    class FakeContext:
        def __enter__(self):
            return FakeSpan()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(telemetry, "span", lambda name, **attrs: (captured.update(attrs) or FakeContext()))

    async def slow():
        await asyncio.sleep(0.05)

    runtime = AgentRuntime(_contract(timeout_seconds=1))
    # wait_for uses seconds; use a sub-second timeout after validation.
    runtime.contract.timeout_seconds = 0.01
    with pytest.raises(asyncio.TimeoutError):
        await runtime.execute(slow)

    assert runtime.state is RuntimeState.FAILED
    assert captured["runtime.outcome"] == "timeout"
    assert captured["runtime.failure_category"] == "timeout"


@pytest.mark.asyncio
async def test_retry_outcome_is_observable(monkeypatch):
    captured = {}

    class FakeSpan:
        def set_attribute(self, key, value):
            captured[key] = value

    class FakeContext:
        def __enter__(self):
            return FakeSpan()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(telemetry, "span", lambda name, **attrs: (captured.update(attrs) or FakeContext()))

    attempts = 0

    async def flaky():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("secret failure detail")
        return "ok"

    result = await AgentRuntime(_contract()).execute(flaky, retryable=True)

    assert result.attempts == 2
    assert result.outcome == "succeeded"
    assert captured["runtime.attempt"] == 2
    assert captured["runtime.retryable"] is True
