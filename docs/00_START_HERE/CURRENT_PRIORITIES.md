# Current Priorities

**Reconciled:** 2026-09-03

## Priority 0 — Preserve verified identities and evidence

Preserve canonical release identities, completed local acceptance evidence, runtime hardening evidence and the authoritative Alembic graph. Do not rerun completed suites merely to reproduce status; rerun when relevant regression risk or evidence invalidation exists.

## Priority 1 — Phase 14: Scale, Governance & Production

Phase 13 Agent Teams & Marketplace engineering implementation is complete. The next engineering frontier is Phase 14: queue isolation, concurrency and routing, cost controls, SLOs, disaster recovery, security/compliance, regression prevention, incident response and production-evidence readiness.

## Priority 2 — Production hardening and external evidence

Continue environment-specific certification for the current implementation. Keep repository CI, local runtime evidence and external production/customer evidence explicitly separated.

## Priority 3 — Customer delivery package

Prepare customer delivery and handoff material for the current local-delivery scope. Do not claim customer deployment or acceptance before an actual customer event exists.

## Priority 4 — Unified execution and workspace hardening

Continue validating Platform, Reseller and Client actions against real WorkItem and Agent APIs while preserving tenant, RBAC, approval and audit boundaries.

## Priority 5 — Compatibility migration

Continue moving changed Employee-backed capabilities toward the unified Human/Agent execution model without destructive model replacement.

## Phase 13 completion record

Phase 13 delivered TeamDefinition/TeamVersion contracts, tenant-local installation, WorkItem-backed execution, evaluation/version evidence, Marketplace publication/discovery/import, authorized Marketplace UI and Playwright acceptance coverage. Marketplace import records provenance and does not imply customer acceptance, production deployment or automatic AgentInstance provisioning.

## Future conditional external production

Only when a real external target exists:

- configure the real deployment context;
- collect deployment, observability and recovery evidence;
- execute Vendor → Reseller → Client acceptance where applicable.

Never fabricate production configuration merely to satisfy CI.

## Evidence boundary

- CI/internal certification = engineering evidence.
- Local real-stack validation = local evidence.
- External production and customer acceptance require independent external evidence.
- Phase 13 engineering completion does not change canonical release certification identities.
