"""Bounded Agent Runtime execution loop.

Phase 13.2 introduces the execution boundary around an AgentRuntimeContract.
The runtime owns lifecycle state, timeout enforcement, and deliberately
conservative retry semantics. It never bypasses the existing RunService or
ToolRegistry permission/approval boundaries.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import Awaitable, Callable, TypeVar

from app.agents.runtime_contract import AgentRuntimeContract

T = TypeVar("T")


class RuntimeState(StrEnum):
    RECEIVED = "received"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class RuntimeResult:
    state: RuntimeState
    attempts: int
    value: object | None = None


class AgentRuntime:
    """Execute one contract-bound operation with bounded lifecycle controls.

    Retries are opt-in per operation. This is intentional: replaying an entire
    Employee Run may duplicate provider calls or external side effects, so the
    default is exactly one attempt. Callers may mark an operation retryable only
    when they know it is safe/idempotent to replay.
    """

    def __init__(self, contract: AgentRuntimeContract) -> None:
        contract.validate()
        self.contract = contract
        self.state = RuntimeState.RECEIVED

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        *,
        retryable: bool = False,
    ) -> RuntimeResult:
        self.state = RuntimeState.RUNNING
        attempts = 0
        max_attempts = self.contract.retry.max_attempts if retryable else 1

        while attempts < max_attempts:
            attempts += 1
            try:
                value = await asyncio.wait_for(
                    operation(), timeout=self.contract.timeout_seconds
                )
                self.state = RuntimeState.SUCCEEDED
                return RuntimeResult(
                    state=self.state,
                    attempts=attempts,
                    value=value,
                )
            except asyncio.CancelledError:
                self.state = RuntimeState.FAILED
                raise
            except Exception:
                if attempts >= max_attempts:
                    self.state = RuntimeState.FAILED
                    raise
                if self.contract.retry.backoff_seconds:
                    await asyncio.sleep(self.contract.retry.backoff_seconds)

        self.state = RuntimeState.FAILED
        raise RuntimeError("Agent Runtime exhausted its execution attempts")
