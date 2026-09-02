# Current Priorities

## Scope clarification

The current delivery objective is **temporary local execution and validation on the owner's workstation, followed by customer delivery**. An external production host, external registry, Vendor, Reseller, or live customer environment is **not a prerequisite for the current validation cycle**.

The repository contains external-production workflows for a later deployment context. Their prerequisites must not be fabricated or treated as blockers for the current local acceptance cycle.

## Priority 0 — Preserve v1.3.2 Release Identity

The canonical candidate is `v1.3.2` on `release/v1.3.2-phase6e-candidate` at exact commit `728b7f447d3bc6376fb01d47730cdd70eaf07746`. Phase 6E rehearsal, Production Certification and release packaging have passed on that exact identity. Do not rebuild, retag or replace it without a real defect.

## Priority 1 — Preserve Completed Local Delivery Evidence

The six local Product Acceptance gates, runtime hardening, Redis/Beat recovery, backup/restore verification, migration audit and rollback evidence are complete. Do not rerun them merely to reproduce status. Rerun only after regression, relevant code/configuration change, a new release/candidate SHA, material environment change, or explicit evidence invalidation.

## Priority 2 — Customer Delivery Package

Prepare the customer delivery package and handoff documentation within the current local-delivery scope. Customer deployment/acceptance is a separate event and must not be claimed before it actually occurs.

## Priority 3 — Phase 12 Test Center & Evidence Platform

Expand the existing acceptance/evidence contracts into the first-class Phase 12 Test Center: safe execution, isolated data, run history, logs, artifacts, pass/fail evidence and exportable verification records.

The first engineering slice is intentionally backend-first:

**Test Definition → authorized Test Run creation → isolated execution context → Run lifecycle → persisted result → tenant-scoped retrieval → audit/evidence record.**

Do not replace the existing certified acceptance suite and do not weaken tenant, RBAC, audit or Human/Agent execution controls.

## Priority 4 — Workspace / Unified Execution Hardening

Continue validating Platform/Reseller/Client workspace actions against real WorkItem and Agent APIs, including role, tenant, authorization and audit boundaries.

## Priority 5 — Compatibility Migration

Continue incremental migration of existing Employee-backed capabilities onto the unified Human/Agent execution model while preserving compatibility paths.

## Priority 6 — External Production (Future / Conditional)

Only if a later business deployment requires an external production target, configure the required target and execute the repository's target-specific hardening, observability, recovery/DR, deployment and rollback workflows. Do not create fake values for `PRODUCTION_DEPLOY_HOST`, `PRODUCTION_DEPLOY_USER`, `PRODUCTION_DEPLOY_SSH_KEY` or `PRODUCTION_CONTAINER_REGISTRY` merely to satisfy those future workflows.

## Priority 7 — Vendor / Reseller / Client Acceptance (Future / Conditional)

External Vendor → Reseller → Client acceptance is outside the current local-only delivery scope. It can begin only when an actual external deployment/acceptance context exists and independent evidence is available.

## Priority 8 — Downstream Productization

After local delivery readiness and execution stability, proceed with Phase 13 Agent Teams & Marketplace and Phase 14 Scale, Governance & Production according to the roadmap.

## Completed local acceptance checkpoint

As of 2026-09-02, the following local gates are recorded as PASS and should not be repeated unless invalidated by regression, relevant code/configuration change, a new release/candidate SHA, material environment change, or explicit evidence invalidation:

- Tenant Isolation + RBAC + Knowledge P0 — PASS twice
- Conversation Tenant Isolation P0 — PASS
- Employee → Run → AI → Result — PASS
- Files → Knowledge → Memory — PASS
- Admin / Developer API Keys — PASS
- Workflow + Approval + Schedule — PASS

See `docs/current/51_LOCAL_FINAL_ACCEPTANCE_RECONCILIATION_2026-09-02.md` for the detailed evidence and incident-resolution record.

## Evidence boundary

- CI/internal certification is engineering evidence.
- Local production-like deployment/recovery evidence is valid local evidence.
- A GitHub release/tag is a release identity, not proof of external production deployment.
- External Vendor/Reseller/Client acceptance requires independent evidence.
- Phase 12 implementation evidence is engineering/product evidence and does not constitute external production certification.
- No acceptance state may be marked complete without the corresponding evidence.
