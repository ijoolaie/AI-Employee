# AI Employee Platform — Productization & Delivery Roadmap

## Current position — 2026-09-04

V1.4 remains the frozen architecture foundation. V1.5 is the Human + Agent operating-model extension. Phase 11 is complete, Phase 12 is operationally hardened, Phase 13 engineering is complete, and Phase 14.1–14.12 engineering is complete, with Phase 14.12 Redis runtime evidence merged at `ac9fdf7063b459b3be5d4e8104e5b1f34ecb284d`.

The remaining roadmap is intentionally ordered so **External Production Certification & Customer Acceptance is the final stage**.

## Ordered remaining stages

### Stage 1 — Phase 14.11: Certification Readiness & Cross-Platform Hardening
**Issue #285 — IN PROGRESS**

Harden the certification path before any external deployment: LF-normalize shell scripts, add deterministic application configuration preflight, improve local evidence reproducibility and preserve secret-safe evidence boundaries.

### Stage 2 — Phase 14.12: Tenant-Fair Scheduling & Resource Isolation
**Issue #286 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

Implemented with Redis-backed per-tenant resource caps, starvation-protection scheduling and weighted virtual-finish service-share signals. Runtime integration evidence exercises the production Lua admission paths and fixed-point Redis scores at `ac9fdf7063b459b3be5d4e8104e5b1f34ecb284d`.

### Stage 3 — Phase 14.13: Load, Stress & Capacity Validation
**Issue #287 — QUEUED**

Create reproducible load/stress scenarios across API, WorkItem execution, queues/workers, routing, cost controls and recovery paths, with measurable thresholds and exact artifact identity.

### Stage 4 — Phase 14.14: Security, Privacy & Compliance Engineering Extensions
**Issue #288 — QUEUED**

Refresh threat modeling, expand security regression coverage, verify privacy/data-retention boundaries, map compliance controls and prepare an external-pentest scope/runbook. External findings remain external evidence.

### Stage 5 — Phase 14.15: Capacity, Cost & Operational Optimization
**Issue #289 — QUEUED**

Use measured load results to establish capacity/sizing guidance, cost-per-WorkItem visibility, budget/resource optimization and operational runbooks without weakening tenant isolation or safety controls.

### Stage 6 — Phase 14.16: V1.5 Human + Agent Operating Model
**Issue #290 — QUEUED**

Formalize the Human + Agent operating model on the unified WorkItem substrate, align Platform/Reseller/Client UX and APIs, strengthen governance/approval/audit flows and migrate remaining Employee-backed capabilities incrementally.

### Stage 7 — Phase 14.10: External Production Certification & Customer Acceptance
**Issues #269 / #210 / #19 — FINAL / EXTERNAL-PENDING**

Only after Stages 1–6 are complete and their documentation is reconciled:

1. freeze one exact immutable release candidate;
2. reconcile artifacts, migrations and checksums;
3. deploy that exact identity to the real target;
4. collect live provider, production SLO/error-budget and DR RPO/RTO evidence;
5. complete applicable external security/compliance review and rollback evidence;
6. execute ordered Vendor → Reseller → Client acceptance;
7. record exceptions/residual risks and the final certification decision.

CI, repository tests, browser acceptance, local Docker validation and rehearsal evidence remain engineering evidence and cannot close Stage 7.

## Completed baseline

- Phase 11 Unified Execution — COMPLETE.
- Phase 12 Test Center P12.1–P12.6 — IMPLEMENTED / OPERATIONAL HARDENING.
- Phase 13 Agent Teams & Marketplace — ENGINEERING COMPLETE.
- Phase 14.1–14.9 — ENGINEERING COMPLETE.
- Phase 14.10 local certification harness — IMPLEMENTED; successful local run remains engineering evidence only.

## Cross-cutting Definition of Done

Every stage must preserve:

- backend-enforced tenant isolation;
- RBAC at API/service boundaries;
- equivalent authorization controls for Human and Agent execution;
- policy-driven approval for risky actions;
- scoped tools and credentials;
- auditability;
- safe test execution;
- secrets excluded from source/artifacts;
- one authoritative Alembic graph;
- reproducible CI/release artifacts;
- explicit local/CI/production evidence boundaries;
- documentation reconciliation before stage closure.

## Evidence boundary

Engineering implementation, CI, CodeQL, Architecture Guard, operational workflow results and local runtime evidence are distinct from external production evidence. None of them alone establishes live deployment, live third-party provider validation, measured production SLO attainment, customer acceptance, commercial go-live or independent certification.
