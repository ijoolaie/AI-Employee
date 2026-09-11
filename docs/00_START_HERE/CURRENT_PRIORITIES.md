# Current Priorities

**Reconciled:** 2026-09-11  
**Latest certified release:** `v1.3.8`  
**Certified commit:** `fd1e74b6b4c1701f7443efc202bad161ff19618c`  
**Current mainline:** `30ed658ae05a116a4e3d2ce3622330aa58dd347c`  
**Current status:** PRODUCTION HARDENING / SYSTEMATIC EXECUTION-BOUNDARY AUDIT

## Executive priority

The historical `v1.4.0-rc.1` blocker is closed as a current planning item. PR #487 has now closed the concurrent `pending` Run admission race. Work continues as a systematic audit of Celery redelivery/retry, deferred side effects and authorization boundaries. Mainline is not certified because no fresh Production Certification has been run against the current exact SHA.

## P1 — next correctness boundaries

1. Audit Celery retry/redelivery semantics across Run, Workflow, Test Center and control workers; reject unsafe automatic replay after an irreversible side effect.
2. Audit Transactional Outbox dispatch/recovery for lost dispatch, duplicate enqueue, stale processing and manual replay hazards.
3. Audit Tenant/RBAC and Agent governance immediately before deferred side effects; authorization must be evaluated against current durable state.
4. Identify remaining stale-state/crash windows that can create duplicate, lost or unauthorized side effects.
5. Add deterministic crash/concurrency tests for every confirmed P1 boundary.
6. Run all required gates on each corrected HEAD and merge only when green.
7. After the hardening set stabilizes, run Production Certification against the exact resulting SHA before declaring a release certified.

## Completed hardening checkpoint

- PR #464 — crash-safe Agent WorkItem → Run handoff.
- PR #465 — approval-resume enqueue race closed through outbox.
- PR #466 — Run creation/outbox failure boundary hardened with nested savepoint.
- PR #467 — WorkItem cancellation fenced at the DB boundary.
- PR #468 — workflow replay after side effects prevented.
- PR #470 — unsafe workflow child retries fail closed.
- PR #473 — workflow re-entry after child commit fenced.
- PR #475 — concurrent workflow event dispatch fenced.
- PR #477 — workflow terminal states made immutable.
- PR #479 — post-timeout/terminal workflow advancement fenced.
- PR #482 — durable WorkflowRun execution lease and bounded recovery.
- PR #486 — durable parallel-branch execution lease/recovery and optimistic ownership fencing.
- PR #487 — concurrent Run execution admission serialized with a database row lock.

## Certification checkpoint

- Latest certified release: `v1.3.8`
- Certified commit: `fd1e74b6b4c1701f7443efc202bad161ff19618c`
- Current mainline: `30ed658ae05a116a4e3d2ce3622330aa58dd347c`
- PR #487: merged; PR validation passed before merge.
- Fresh Production Certification for current mainline: **PENDING**

## P2 — external production gates

After release certification is complete, the remaining external boundary still requires real production infrastructure, deployed-identity verification, live provider validation, backup/restore and DR, production SLO/SLI, external Vendor → Reseller → Client acceptance, independent security review, production networking/secret management, HA/failure recovery and incident-response evidence.

## Evidence rules

- CI/internal validation = engineering/release evidence.
- Production-like certification = exact-SHA release-candidate evidence.
- Real production deployment = target evidence.
- Customer acceptance = independent acceptance evidence.
- Certification never transfers automatically across SHAs.
- Never fabricate production configuration, credentials, provider evidence or compliance certification.
- Never place secrets in GitHub issues, commits, documentation or chat.
