# Current Priorities

**Reconciled:** 2026-09-04

## Priority 0 — Preserve verified identities and evidence

Preserve canonical release identities, completed acceptance evidence, runtime hardening evidence and the authoritative Alembic graph. Do not inherit certification across SHAs.

## Priority 1 — Phase 14.10 external production evidence

Phase 14.1–14.9 engineering implementation is complete. The active frontier is the external evidence gate: fresh immutable release candidate, artifact identity, deployment evidence, live provider validation, measured production SLO/error-budget evidence, measured DR RPO/RTO evidence, security/compliance review, rollback readiness and ordered Vendor → Reseller → Client acceptance where applicable.

## Priority 2 — Production hardening and external certification

Continue environment-specific certification for the current implementation. Keep repository CI, local runtime evidence and external production/customer evidence explicitly separated.

## Priority 3 — Customer delivery package

Prepare customer delivery and handoff material for the current implementation scope. Do not claim customer deployment or acceptance before an actual customer event exists.

## Priority 4 — Unified execution and workspace hardening

Continue validating Platform, Reseller and Client actions against real WorkItem and Agent APIs while preserving tenant, RBAC, approval and audit boundaries.

## Priority 5 — Compatibility migration

Continue moving changed Employee-backed capabilities toward the unified Human/Agent execution model without destructive model replacement.

## Phase 14 completion record

Engineering workstreams 14.1–14.9 are complete:

- queue/worker isolation;
- concurrency/backpressure hardening;
- routing/scheduling;
- tenant-scoped cost controls;
- SLO/reliability/observability instrumentation;
- disaster recovery/backup/restore baseline;
- security/compliance hardening;
- regression/release gates;
- incident response/operational readiness.

Phase 14.10 is **EXTERNAL-PENDING** and is not satisfied by CI or repository tests.

## Active external gates

- #210 — consolidated immutable release and external-production gate;
- #19 — Vendor → Reseller → Client runtime isolation/RBAC evidence;
- #269 — Phase 14.10 evidence package and acceptance decision boundary.

These issues remain open until independent evidence is complete and reconciled to one exact accepted release identity.

## Future conditional external production

Only when a real external target exists:

- freeze the exact release candidate;
- configure the real deployment context;
- collect deployment, provider, observability and recovery evidence;
- execute Vendor → Reseller → Client acceptance where applicable;
- record the final certification decision against the exact release identity.

Never fabricate production configuration merely to satisfy CI.

## Evidence boundary

- CI/internal certification = engineering evidence.
- Local real-stack validation = local evidence.
- External production and customer acceptance require independent external evidence.
- Phase 14.1–14.9 completion does not change canonical release certification identities.
