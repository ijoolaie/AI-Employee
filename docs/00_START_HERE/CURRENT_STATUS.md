# Current Status

**Last reconciled:** 2026-09-11  
**Latest certified release:** `v1.3.8`  
**Certified commit:** `fd1e74b6b4c1701f7443efc202bad161ff19618c`  
**Certification run:** `34052885700` — SUCCESS  
**Current engineering mainline:** `main`  
**Current mainline SHA:** `30ed658ae05a116a4e3d2ce3622330aa58dd347c`  
**Current release candidate:** none currently certified  
**Current status:** PRODUCTION HARDENING / SYSTEMATIC EXECUTION-BOUNDARY AUDIT

## Executive truth

The AI Employee Platform is a multi-tenant business operating platform evolving toward a **Human + Agent operating model**. Platform, Reseller and Client workspaces remain separated by tenant, role and authorization boundaries.

The certified release `v1.3.8` remains frozen at its exact certified commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`. Certification does not transfer to later mainline revisions.

Mainline has moved beyond the historical `v1.4.0-rc.1` documentation state. PRs #462 through #487 have added execution-boundary hardening, including WorkItem/Run crash-safety, workflow retry/re-entry/terminal-state/timeout fences, workflow and parallel-branch execution leases, and concurrent Run admission serialization.

## Latest hardening sequence

Key merged hardening includes:
- PR #464 — crash-safe Agent WorkItem → Run handoff.
- PR #465 — approval-resume enqueue race closed through the outbox path.
- PR #466 — atomic Run creation/outbox failure boundary hardened with a nested savepoint.
- PR #467 — WorkItem cancellation fenced against executable pending/waiting Agent Runs at the database boundary.
- PR #468 — workflow execution replay after side effects prevented.
- PR #470 — unsafe workflow child retries fail closed; no blind child recreation.
- PR #473 — workflow re-entry after a child commit fenced.
- PR #475 — concurrent workflow event dispatch fenced with row locking.
- PR #477 — workflow terminal states made immutable at the database boundary.
- PR #479 — workflow advancement fenced after timeout/cancellation/terminal state wins between child commits.
- PR #482 — durable WorkflowRun execution lease, heartbeat, ownership fencing and bounded recovery.
- PR #486 — durable parallel-branch execution lease, child Run identity/step position and optimistic lease-version fencing.
- PR #487 — concurrent Celery Run execution admission serialized with a `SELECT ... FOR UPDATE` Run-row fence.

## Current execution-boundary audit

The previously identified concurrent `pending` Run admission race is closed by PR #487. The worker now acquires the Run row lock before entering the canonical RunService execution path, so duplicate Celery deliveries cannot concurrently pass the `pending` idempotency guard.

The remaining audit focus is now broader Celery redelivery/retry behavior and side-effect boundaries outside the already-hardened Run/Workflow paths. Review must preserve fail-closed semantics and durable ownership/fencing rather than relying on process-local state.

Current audit targets:
1. Celery retry/redelivery semantics across execution, workflow, test-center and control workers.
2. Transactional Outbox dispatch/recovery and dedupe boundaries.
3. Tenant/RBAC authorization immediately before deferred side effects.
4. Remaining stale-state or crash windows that can produce duplicate, lost or unauthorized side effects.
5. Deterministic tests for every newly confirmed P1 boundary.

## Certification boundary

`v1.3.8` remains the latest certified release. The previous `v1.4.0-rc.1` Product Certification attempt (`34497132748`) is historical evidence only and is not a certification of current mainline.

The current mainline SHA `30ed658ae05a116a4e3d2ce3622330aa58dd347c` includes PR #487 after squash merge. PR-level validation for #487 passed before merge. A fresh Production Certification has **not** yet been run for this merged SHA; therefore mainline is **not certified**.

## Production deployment status

A controlled deployment was previously attempted using `v1.3.8`:
- Workflow run: `34060615390`
- Job: `101560362909`
- Result: **FAILED BEFORE REMOTE DEPLOYMENT**
- Failed step: `Configure SSH`
- Cause: required production Environment inputs were empty/missing.
- Remote deploy and deployed-identity verification were skipped.
- Production host mutation: **NONE**.

## External production gates

These remain pending and are not established by repository/production-like certification:

- real production infrastructure;
- deployed-identity verification;
- live provider validation;
- real backup/restore and DR;
- production SLO/SLI and error budget;
- external Vendor → Reseller → Client acceptance;
- DAST against the deployed target where applicable;
- independent security review;
- production networking and secret-management evidence;
- HA/failure recovery in the target environment;
- incident response/on-call evidence;
- final external certification and customer acceptance.

## Evidence boundary

CI, repository tests, CodeQL, production-like validation and simulated providers establish engineering/release evidence. They do not establish live production deployment, live provider certification, measured production SLO/DR, independent security review or customer acceptance.

Certification is bound to the exact SHA and never transfers automatically.

## Security rule

Do not commit production hosts, private keys, registry credentials, webhook secrets, payment secrets, customer data or environment-specific access tokens. Missing required production inputs must fail closed.
