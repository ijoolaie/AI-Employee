# Current Priorities

## Scope clarification

The current delivery objective is **temporary local execution and validation on the owner's workstation, followed by customer delivery**. An external production host, external registry, Vendor, Reseller, or live customer environment is **not a prerequisite for the current validation cycle**.

The repository contains external-production workflows for a later deployment context. Their prerequisites must not be fabricated or treated as blockers for the current local acceptance cycle.

## Priority 0 — Preserve v1.3.2 Release Identity

The canonical candidate is `v1.3.2` on `release/v1.3.2-phase6e-candidate` at exact commit `728b7f447d3bc6376fb01d47730cdd70eaf07746`. Phase 6E rehearsal, Production Certification and release packaging have passed on that exact identity. Do not rebuild, retag or replace it without a real defect.

## Priority 1 — Complete Local Final Acceptance

Continue validation on the local production-like stack using the exact `v1.3.2` release identity. The objective is to close every **local** test/evidence gap before customer delivery. Local evidence must remain explicitly labeled as local; it must not be represented as external production evidence.

Known local evidence boundary from the Phase 6E rehearsal:

- Health: PASS
- Migration: PASS
- Backup/restore: PASS
- Controlled recovery: PASS
- Evidence generation/upload: PASS
- Monitoring: `NOT_CONFIGURED_IN_REHEARSAL`
- Security: `REHEARSAL_ONLY`

Therefore the next local work must address the remaining monitoring/observability and security/hardening evidence that can be meaningfully exercised on the local production-like stack, plus any other local acceptance criteria found in the current runbooks/workflows.

## Priority 2 — Local Recovery / DR / Rollback Reconciliation

Confirm the repository's recovery, DR and rollback contracts against the local production-like stack where they are applicable. Preserve logs, artifacts and evidence and bind them to the exact `728b7f447...` revision.

## Priority 3 — Local End-to-End Delivery Verification

Run the final local health, readiness and product smoke/E2E checks on the exact release identity. Reconcile the deployed revision, migration head, runtime artifact and edition artifact identities.

## Priority 4 — Final Local Evidence Manifest

Build one authoritative local-delivery evidence manifest tying together version/tag, exact SHA, migration head, certification runs, runtime checksum, edition checksum, local deployment/recovery/rollback evidence and any explicit limitations.

## Priority 5 — Customer Delivery Package

After local final acceptance passes, prepare the customer delivery package and handoff documentation. Customer deployment/acceptance is a separate event and must not be claimed before it actually occurs.

## Priority 6 — External Production (Future / Conditional)

Only if a later business deployment requires an external production target, configure the required target and execute the repository's target-specific hardening, observability, recovery/DR, deployment and rollback workflows. Do not create fake values for `PRODUCTION_DEPLOY_HOST`, `PRODUCTION_DEPLOY_USER`, `PRODUCTION_DEPLOY_SSH_KEY` or `PRODUCTION_CONTAINER_REGISTRY` merely to satisfy those future workflows.

## Priority 7 — Vendor / Reseller / Client Acceptance (Future / Conditional)

External Vendor → Reseller → Client acceptance is outside the current local-only delivery scope. It can begin only when an actual external deployment/acceptance context exists and independent evidence is available.

## Priority 8 — Phase 12 Test Center & Evidence Platform

Expand existing test/evidence contracts into the first-class Phase 12 Test Center where repeatable acceptance proof is needed, without destabilizing the release candidate.

## Priority 9 — Compatibility Migration

Continue incremental migration of existing Employee-backed capabilities onto the unified Human/Agent execution model while preserving compatibility paths.

## Priority 10 — Downstream Productization

After local delivery readiness and execution stability, proceed with Phase 13 Agent Teams & Marketplace and Phase 14 Scale, Governance & Production according to the roadmap.

## Evidence boundary

- CI/internal certification is engineering evidence.
- Local production-like deployment/recovery evidence is valid local evidence.
- A GitHub release/tag is a release identity, not proof of external production deployment.
- External Vendor/Reseller/Client acceptance requires independent evidence.
- No acceptance state may be marked complete without the corresponding evidence.
