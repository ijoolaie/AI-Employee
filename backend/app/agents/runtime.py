"""Bounded Agent Runtime execution loop.

Phase 13.2 introduces the execution boundary around an AgentRuntimeContract.
Phase 13.5 adds best-effort lifecycle telemetry without changing execution
semantics or recording sensitive execution payloads.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import Awaitable, Callable, TypeVar

from app.agents.runtime_contract import AgentRuntimeContract
from app.core.telemetry import agent_runtime_span

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
    outcome: str = "unknown"
    failure_category: str | None = None
    timed_out: bool = False


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

    def _telemetry_attributes(self, **extra: object) -> dict[str, object]:
        attributes = self.contract.evidence_context()
        attributes.update(extra)
        return attributes

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        *,
        retryable: bool = False,
    ) -> RuntimeResult:
        self.state = RuntimeState.RUNNING
        attempts = 0
        max_attempts = self.contract.retry.max_attempts if retryable else 1

        with agent_runtime_span(
            **self._telemetry_attributes(
                **{
                    "runtime.retryable": retryable,
                    "runtime.max_attempts": max_attempts,
                    "runtime.outcome": "running",
                }
            )
        ) as runtime_span:
            while attempts < max_attempts:
                attempts += 1
                if runtime_span is not None:
                    try:
                        runtime_span.set_attribute("runtime.attempt", attempts)
                    except Exception:
                        pass
                try:
                    value = await asyncio.wait_for(
                        operation(), timeout=self.contract.timeout_seconds
                    )
                    self.state = RuntimeState.SUCCEEDED
                    if runtime_span is not None:
                        try:
                            runtime_span.set_attribute("runtime.outcome", "succeeded")
                        except Exception:
                            pass
                    return RuntimeResult(
                        state=self.state,
                        attempts=attempts,
                        value=value,
                        outcome="succeeded",
                    )
                except asyncio.TimeoutError:
                    self.state = RuntimeState.FAILED
                    if runtime_span is not None:
                        try:
                            runtime_span.set_attribute("runtime.outcome", "timeout")
                            runtime_span.set_attribute("runtime.failure_category", "timeout")
                            runtime_span.set_attribute("runtime.timeout", True)
                        except Exception:
                            pass
                    raise
                except asyncio.CancelledError:
                    self.state = RuntimeState.FAILED
                    if runtime_span is not None:
                        try:
                            runtime_span.set_attribute("runtime.outcome", "cancelled")
                            runtime_span.set_attribute("runtime.failure_category", "cancelled")
                        except Exception:
                            pass
                    raise
                except Exception:
                    if attempts >= max_attempts:
                        self.state = RuntimeState.FAILED
                        if runtime_span is not None:
                            try:
                                runtime_span.set_attribute("runtime.outcome", "failed")
                                runtime_span.set_attribute("runtime.failure_category", "exception")
                            except Exception:
                                pass
                        raise
                    if runtime_span is not None:
                        try:
                            runtime_span.set_attribute("runtime.outcome", "retrying")
                            runtime_span.set_attribute("runtime.failure_category", "retryable_exception")
                        except Exception:
                            pass
                    if self.contract.retry.backoff_seconds:
                        await asyncio.sleep(self.contract.retry.backoff_seconds)

            self.state = RuntimeState.FAILED
            if runtime_span is not None:
                try:
                    runtime_span.set_attribute("runtime.outcome", "exhausted")
                    runtime_span.set_attribute("runtime.failure_category", "retry_exhausted")
                except Exception:
                    pass
            raise RuntimeError("Agent Runtime exhausted its execution attempts")
