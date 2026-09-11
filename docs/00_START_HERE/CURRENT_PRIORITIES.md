# Current Priorities

**Reconciled:** 2026-09-11  
**Latest certified release:** `v1.3.8`  
**Certified commit:** `fd1e74b6b4c1701f7443efc202bad161ff19618c`  
**Current mainline:** `649f8ceaedb35c4f9e61a56faaf5c58956821c1d`  
**Current status:** PRODUCTION HARDENING / SYSTEMATIC EXECUTION-BOUNDARY AUDIT

## Executive priority

The old `v1.4.0-rc.1` blocker is historical. Current work has moved to execution-boundary correctness after PRs #462–#479. Mainline is not certified because no fresh Production Certification has been run against the current exact SHA.

## P1 — next correctness boundary

1. Design a durable lease/fencing model for stale `running` `WorkflowRun` and `Run` ownership (Issue #480).
2. Preserve fail-closed semantics: a redelivered worker must not blindly replay `running` execution.
3. Make ownership transfer explicit and durable so an old worker cannot continue side effects after recovery.
4. Preserve provider durable-call fences and existing child Run identity; never create a replacement execution solely because a worker disappeared.
5. Define bounded recovery policy for workflows without `deadline_at`/runtime limits.
6. Add deterministic crash/recovery tests covering worker death before and after child/provider side-effect boundaries.
7. Run all required gates on the exact corrected HEAD and merge only when green.
8. Rerun Production Certification on the exact resulting SHA before declaring a new release certified.

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

## Certification checkpoint

- Latest certified release: `v1.3.8`
- Certified commit: `fd1e74b6b4c1701f7443efc202bad161ff19618c`
- Previous RC certification: `34497132748` — historical, failed one Agent WorkItem Product Gate
- Current mainline: `649f8ceaedb35c4f9e61a56faaf5c58956821c1d`
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
