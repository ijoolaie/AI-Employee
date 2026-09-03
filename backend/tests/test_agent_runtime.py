import asyncio

import pytest

from app.agents.runtime import AgentRuntime, RuntimeState
from app.agents.runtime_contract import AgentRuntimeContract, RetryPolicy


def contract(**overrides):
    values = {
        "tenant_id": "tenant-1",
        "run_id": "run-1",
        "employee_id": "employee-1",
        "employee_version_id": "version-1",
        "input_data": {"goal": "test"},
    }
    values.update(overrides)
    return AgentRuntimeContract(**values)


@pytest.mark.asyncio
async def test_runtime_executes_contract_and_returns_success():
    runtime = AgentRuntime(contract())

    async def operation():
        return {"ok": True}

    result = await runtime.execute(operation)

    assert result.state is RuntimeState.SUCCEEDED
    assert result.attempts == 1
    assert result.value == {"ok": True}
    assert runtime.state is RuntimeState.SUCCEEDED


@pytest.mark.asyncio
async def test_runtime_enforces_timeout():
    runtime = AgentRuntime(contract(timeout_seconds=1))

    async def operation():
        await asyncio.sleep(2)

    with pytest.raises(asyncio.TimeoutError):
        await runtime.execute(operation)

    assert runtime.state is RuntimeState.FAILED


@pytest.mark.asyncio
async def test_runtime_does_not_retry_non_retryable_full_run():
    runtime = AgentRuntime(
        contract(retry=RetryPolicy(max_attempts=3, backoff_seconds=0))
    )
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await runtime.execute(operation, retryable=False)

    assert calls == 1
    assert runtime.state is RuntimeState.FAILED


@pytest.mark.asyncio
async def test_runtime_can_retry_explicitly_retryable_operation():
    runtime = AgentRuntime(
        contract(retry=RetryPolicy(max_attempts=2, backoff_seconds=0))
    )
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("transient")
        return "ok"

    result = await runtime.execute(operation, retryable=True)

    assert result.state is RuntimeState.SUCCEEDED
    assert result.attempts == 2
    assert calls == 2
