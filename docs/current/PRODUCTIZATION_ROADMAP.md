# AI Employee Platform — Productization & Delivery Roadmap

## Current position — 2026-09-04

V1.4 remains the frozen architecture foundation. V1.5 is the Human + Agent operating-model extension. Phase 11 is complete, Phase 12 is operationally hardened, Phase 13 engineering is complete, and Phase 14.1–14.13 engineering is complete. Phase 14.13 is backed by bounded synthetic CI load/capacity evidence finalized on main at `599cb8b167103e3627678739f8440d854cad55f1`; its test-merge evidence SHA is `98771d087bc658d633a99a63c9ef0476e13c18ae` and artifact SHA256 is `1f19b7d7ee6adc0623904bec76eaed4619ee88bca02af7d65107dae7ae925845`.

The remaining roadmap is intentionally ordered so **External Production Certification & Customer Acceptance is the final stage**.

### Stage 1 — Phase 14.11: Certification Readiness & Cross-Platform Hardening
**Issue #285 — IN PROGRESS**

Harden certification preflight, portability, reproducibility and secret-safe evidence boundaries.

### Stage 2 — Phase 14.12: Tenant-Fair Scheduling & Resource Isolation
**Issue #286 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

Redis-backed tenant resource caps, starvation protection and weighted virtual-finish service-share signals are implemented and runtime-tested.

### Stage 3 — Phase 14.13: Load, Stress & Capacity Validation
**Issue #287 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

Implemented a bounded synthetic load/capacity harness covering API burst behavior, scheduler/routing reservations, tenant resource admission and lease-expiry recovery. The dedicated CI workflow passed 3/3 scenarios and retained a SHA-bound artifact. This validates engineering behavior under the stated bounded thresholds; it does not establish production or customer-scale capacity.

### Stage 4 — Phase 14.14: Security, Privacy & Compliance Engineering Extensions
**Issue #288 — QUEUED**

Refresh threat modeling, expand security regression coverage, verify privacy/data-retention boundaries, map compliance controls and prepare external-pentest scope/runbook.

### Stage 5 — Phase 14.15: Capacity, Cost & Operational Optimization
**Issue #289 — QUEUED**

Use measured load results to establish capacity/sizing guidance, cost-per-WorkItem visibility, budget/resource optimization and operational runbooks.

### Stage 6 — Phase 14.16: V1.5 Human + Agent Operating Model
**Issue #290 — QUEUED**

Formalize the Human + Agent operating model on the unified WorkItem substrate and strengthen governance, approval and audit flows.

### Stage 7 — Phase 14.10: External Production Certification & Customer Acceptance
**Issues #269 / #210 / #19 — FINAL / EXTERNAL-PENDING**

Only after Stages 1–6 and their documentation are complete: freeze an immutable release, deploy that exact identity to the real target, collect live provider/SLO/DR evidence, complete applicable independent security/compliance review, execute ordered acceptance and record the final certification decision.

CI, repository tests, browser acceptance, local Docker validation and synthetic load evidence cannot substitute for independent external evidence.

## Cross-cutting Definition of Done

Every stage must preserve tenant isolation, RBAC, equivalent Human/Agent authorization, policy-driven approvals, scoped credentials, auditability, safe test execution, secret exclusion, one authoritative Alembic graph, reproducible CI/release artifacts, explicit evidence boundaries and documentation reconciliation before closure.
