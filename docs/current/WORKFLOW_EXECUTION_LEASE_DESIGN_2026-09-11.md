# Workflow Execution Lease & Fencing — 2026-09-11

## Purpose

Define the safe recovery boundary for a WorkflowRun that remains durably `running` after a worker crash.

## Safety rule

A `running` WorkflowRun is **not retryable by status alone**. Recovery must transfer durable ownership and fence the previous worker before any new workflow side effect is allowed.

## Lease model

- `execution_lease_id`: opaque UUID identifying the current execution owner.
- `execution_lease_expires_at`: UTC expiry timestamp.
- `execution_heartbeat_at`: latest successful owner heartbeat.
- Lease acquisition/recovery uses a conditional database update under row lock.
- A worker must present the lease identity at every workflow execution boundary.
- A stale worker whose lease no longer matches must stop before creating another child Run or invoking an external provider.

## Recovery invariants

1. Normal execution acquires a lease before transitioning `pending` → `running`.
2. Heartbeat extends only the currently owned lease.
3. Recovery may replace a lease only after expiry.
4. Lease replacement does not create a replacement WorkflowRun or child Run.
5. Existing `employee_run_id` / branch child identity remains authoritative.
6. Existing durable provider-call fences remain authoritative and fail closed on ambiguity.
7. A worker with an old lease cannot commit workflow progress after ownership transfer.
8. Workflows without a configured runtime bound are not automatically recovered merely because they are old.

## Implementation scope

The first implementation should cover WorkflowRun ownership. Run-level provider execution remains protected by the existing durable Run/provider fence and is not made blindly retryable.

## Tests required before merge

- concurrent lease acquisition: exactly one owner;
- expired lease recovery transfers ownership exactly once;
- stale owner is rejected after transfer;
- stale owner cannot advance to another workflow child;
- recovery reuses existing child Run identity;
- provider fence remains fail-closed after recovery;
- terminal WorkflowRun cannot acquire a new lease;
- no-runtime-limit WorkflowRun is not automatically recovered.

## Operational note

Lease recovery is a crash-recovery mechanism, not a generic retry mechanism. If a worker may still be alive, ownership transfer must require an expired lease; this bounds the split-brain window instead of relying on process disappearance detection.
