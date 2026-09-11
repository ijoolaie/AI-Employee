# Execution Boundary Handoff — 2026-09-11

## Repository

- Repository: `ijoolaie/AI-Employee`
- Mainline: `main`
- Current mainline SHA: `30ed658ae05a116a4e3d2ce3622330aa58dd347c`
- Latest merged hardening: PR #487

## Mission

Continue the production-hardening audit of the AI Employee execution system. The primary objective is to eliminate P1 correctness failures involving duplicate, lost, replayed or unauthorized side effects while preserving fail-closed behavior.

## Completed immediately before this handoff

PR #487 — **P1: serialize concurrent Run execution admission** — is merged.

Root cause: `RunService.execute_run()` performed its status/idempotency check without serializing concurrent Celery deliveries. Two workers could observe the same `pending` Run and both enter execution.

Fix: `run.execute` now enters a database fence that acquires the Run row with `SELECT ... FOR UPDATE` before invoking canonical RunService execution. This serializes admission on the durable Run record.

Validation: PR-level required gates passed before squash merge. The merge commit is `30ed658ae05a116a4e3d2ce3622330aa58dd347c`.

## Existing hardening that must not regress

- Agent WorkItem → Run handoff is transactional and crash-safe.
- Approval resume dispatch uses the transactional outbox.
- Run creation/outbox failure uses an atomic savepoint boundary.
- WorkItem cancellation is fenced against executable Agent Runs.
- Workflow replay after side effects is fail-closed.
- Unsafe workflow child retry/recreation is fail-closed.
- Workflow re-entry after child commit is fenced.
- Workflow event dispatch is row-lock serialized.
- Workflow terminal states are database-fenced against resurrection.
- Workflow advancement after timeout/cancellation/terminal-state wins is fenced.
- WorkflowRun execution has durable ownership/heartbeat/fencing with bounded recovery.
- Parallel branch execution has durable branch ownership, heartbeat, child Run identity, step position and optimistic lease-version fencing.
- Provider calls have durable call fencing; do not replace that protection with process-local locks.
- Email side effects use an explicit `uncertain` state and are not automatically reclaimed after an ambiguous SMTP outcome.

## Current audit targets

### P1-A — Celery retry/redelivery

Review every execution-bearing Celery task for the sequence:

1. durable state transition;
2. irreversible external side effect;
3. worker crash/redelivery;
4. automatic retry.

For each task, establish whether retry is safe, idempotent through a durable key, or must fail closed.

Priority workers:
- `run_worker.py`
- `workflow_worker.py`
- `workflow_trigger_worker.py`
- `test_center_worker.py`
- `outbox_worker.py`
- `email_worker.py`

### P1-B — Outbox dispatch/recovery

Audit claim → enqueue → mark-dispatched ordering, stale `processing` reclamation, dedupe keys, manual replay, and unknown/unsupported message kinds. Verify that a crash after downstream task acceptance cannot cause unsafe duplicate side effects.

### P1-C — Tenant/RBAC/Agent governance

Audit deferred side effects so current tenant, Agent identity, permissions, kill-switch state and approval state are checked at the final side-effect boundary, not only when work is created or queued.

### P1-D — Remaining crash windows

Search for state transitions that imply an external effect without a durable identity/fence. Focus on provider calls, payments, webhooks, filesystem/object-store effects, notifications and integrations.

## Rules for the next engineer/agent

- Never make `running` automatically retryable merely because a worker disappeared.
- Never create a replacement child execution solely because the original worker crashed.
- Preserve durable provider-call identity and child Run identity.
- Prefer database locks/optimistic versioning/durable leases over process-local state.
- Every new P1 finding requires a deterministic regression test.
- Merge only after all required gates are green.
- Certification is exact-SHA only; PR CI does not certify production.
- Do not claim production deployment, live provider validation or customer acceptance without independent evidence.

## Release/certification boundary

- Latest certified release: `v1.3.8`
- Certified SHA: `fd1e74b6b4c1701f7443efc202bad161ff19618c`
- Certification run: `34052885700` — SUCCESS
- Current mainline SHA: `30ed658ae05a116a4e3d2ce3622330aa58dd347c`
- Current mainline certification: **PENDING**

## Definition of done for the next phase

The next phase is complete only when:

1. all P1 execution-boundary findings are either fixed with deterministic tests or explicitly proven false;
2. required CI/security/runtime gates are green on the exact merge candidate;
3. documentation reflects the exact mainline SHA and hardening state;
4. a fresh exact-SHA Production Certification is run before declaring a new release certified.

## Immediate next action

Start with a full Celery retry/redelivery matrix, then trace each execution-bearing task into its first irreversible side effect. Open the smallest focused P1 PR for the first confirmed unsafe boundary, run the complete gate set, merge it, reconcile this handoff, and repeat until the audit reaches a clean boundary.
