# Phase 4.24.7 — Run Execution Hardening

## Changes

1. Added an idempotency guard to `RunService.execute_run()` so terminal (`success`, `failed`, `cancelled`) and already-`running` Runs are not executed again. This protects against duplicate Celery delivery and accidental re-invocation of a completed Run.
2. Removed the misleading `max_retries=2` / `default_retry_delay=10` declaration from `run.execute`. The previous declaration did not itself trigger retries, while automatic replay of an AI/tool execution can duplicate external side effects.
3. Kept durable Run failure persistence: `execute_run()` sets `status=failed`, stores the error, stamps `completed_at`, flushes, and re-raises; the worker commits that state before propagating the task failure.

## Remaining runtime verification

- Confirm failed Run state in PostgreSQL after a forced execution failure.
- Confirm duplicate delivery/invocation leaves a terminal Run unchanged and does not create another provider call.
- Worker crash/redelivery recovery remains a separate concern because blindly replaying an in-flight AI execution is not safe without an execution lease/idempotency key for external side effects.
