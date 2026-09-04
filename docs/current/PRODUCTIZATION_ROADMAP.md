# AI Employee Platform — Productization & Delivery Roadmap

## Current position — 2026-09-04

V1.4 remains the frozen architecture foundation. V1.5 is the Human + Agent operating-model extension. Phase 11 is complete, Phase 12 is operationally hardened, Phase 13 engineering is complete, and Phase 14.1–14.16 engineering is complete. Phase 14.11 certification-readiness hardening is complete through merged PR #291. Phase 14.14 is backed by repository security/privacy regression, dependency-audit and CodeQL evidence. Phase 14.15 is backed by green repository CI and reconciled engineering evidence. Phase 14.16 adds the first unified Human + Agent workspace read model over WorkItems and pending approval queues. Production-like infrastructure validation is also complete in CI.

The remaining roadmap is intentionally ordered so **External Production Certification & Customer Acceptance is the final gate**. The gaps below are now explicitly tracked so that no previously identified production, operational, security, commercial or productization requirement is lost between roadmap, status and acceptance records.

## Completed engineering stages

### Stage 1 — Phase 14.11: Certification Readiness & Cross-Platform Hardening
**Issue #285 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

### Stage 2 — Phase 14.12: Tenant-Fair Scheduling & Resource Isolation
**Issue #286 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

### Stage 3 — Phase 14.13: Load, Stress & Capacity Validation
**Issue #287 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

Bounded synthetic evidence passed 3/3 scenarios: API burst, scheduler/routing reservations, and tenant resource admission with lease-expiry recovery. This is engineering evidence only, not production/customer-scale capacity certification.

### Stage 4 — Phase 14.14: Security, Privacy & Compliance Engineering Extensions
**Issue #288 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

Security/privacy regression, dependency audit and CodeQL evidence passed. External security/compliance evidence remains external.

### Stage 5 — Phase 14.15: Capacity, Cost & Operational Optimization
**Issue #289 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

Measured unit economics, budget signals, optimization guidance and worker-sizing decision support are implemented. This is engineering decision support, not production capacity certification.

### Stage 6 — Phase 14.16: V1.5 Human + Agent Operating Model
**Issue #290 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

PR #312 merged at `7657b4244a47af95960e5854fa52f92a0dbe618b`. The tenant-scoped workspace read model combines WorkItems, pending workflow/tool approvals and Human/Agent executor queue counts while preserving existing authorization and mutation boundaries.

### Infrastructure Validation Checkpoint

PR #315 merged at `93c717969a192ae5b90b909c2c4e8aaa89bea50a`. CI run `33884955068` validated the production-like Compose topology, migrations, service startup/readiness, PostgreSQL/Redis restart persistence and real PostgreSQL backup/isolated restore. This is local/CI engineering evidence only and does not establish external production deployment, provider certification, production SLOs or target RPO/RTO.

## Stage 7 — External Production Certification & Customer Acceptance
**Issues #269 / #210 / #19 — FINAL / EXTERNAL-PENDING**

Stage 7 is expanded into the following ordered work packages. Items marked **EXTERNAL** require the real deployment/customer/provider environment and cannot be closed from repository evidence alone. Items marked **MIXED** require repository readiness plus external execution/evidence. Items marked **ENGINEERING** are repository/product work that should be completed before the final acceptance gate when applicable.

| Priority | Work package | Class | Exit evidence |
|---|---|---|---|
| P0 | 7.1 Immutable release & release identity | MIXED | One exact release SHA/tag, checksums, provenance and deployment identity |
| P0 | 7.2 External production infrastructure deployment | EXTERNAL | Real target deployment record and healthy runtime |
| P0 | 7.3 Real backup/restore & disaster-recovery drill | EXTERNAL | Target backup/restore evidence with measured RPO/RTO |
| P0 | 7.4 Production SLO, SLIs & error budget | MIXED | Defined SLOs plus measured target-environment evidence |
| P0 | 7.5 Live provider integration validation | EXTERNAL | Real AI/email/payment/storage/provider validation and failure behavior |
| P0 | 7.6 Vendor → Reseller → Client runtime isolation/RBAC certification | EXTERNAL | Ordered tenant/role isolation evidence on the real stack (#19) |
| P0 | 7.7 Dynamic application security testing (DAST) | MIXED | Running-stack scan results, triage and remediation evidence |
| P0 | 7.8 Independent penetration test / security review | EXTERNAL | Independent report, remediation disposition and residual-risk acceptance |
| P0 | 7.9 Production networking hardening | MIXED | TLS/ingress/firewall/network-policy evidence on target |
| P0 | 7.10 Secret management, rotation & recovery | MIXED | External secret-store configuration, rotation test and recovery evidence |
| P0 | 7.11 High availability & failure-recovery rehearsal | MIXED | Failure injection/restart/failover evidence and recovery objectives |
| P0 | 7.12 Incident-response drill | MIXED | Executed incident scenario, timeline, actions and lessons learned |
| P0 | 7.13 Alert ownership & on-call escalation | MIXED | Named ownership, routing/escalation test and operational runbook |
| P0 | 7.14 Final external certification & customer acceptance | EXTERNAL | Ordered acceptance, final exceptions/residual-risk disposition and sign-off (#210/#269) |
| P1 | 7.15 Data retention & lifecycle enforcement | MIXED | Retention policy mapped to implementation plus target verification |
| P1 | 7.16 Human-in-the-loop TODO reconciliation | ENGINEERING | `run_service.py` approval-path TODO either implemented or explicitly retired/documented |
| P1 | 7.17 Documentation consolidation & evidence index | ENGINEERING | Canonical docs reconciled, stale claims removed, evidence index complete |
| P1 | 7.18 Platform operations dashboard | ENGINEERING | Operational view for health, queues, failures, capacity and tenant-safe visibility |
| P1 | 7.19 Customer usage, budget & cost controls | MIXED | Customer-visible usage/budget controls plus target billing/operations validation |
| P1 | 7.20 Cost anomaly detection & forecasting | ENGINEERING | Deterministic anomaly signals/forecasting with alert and audit behavior |

### Stage 7 sequencing rule

P0 items are release/certification blockers. P1 items are productization/operational completeness items and must not be represented as external certification evidence until independently verified. The final customer-acceptance decision cannot be recorded as complete while any required P0 evidence is missing.

### External evidence boundary

The following are explicitly **not substitutes** for Stage 7 external evidence: repository tests, PR CI, CodeQL, local Docker, GitHub-hosted production-like validation, bounded synthetic load, local RBAC acceptance, simulated provider behavior, or generated evidence artifacts. Certification does not transfer automatically across commit SHAs.

## Cross-cutting Definition of Done

Every stage and work package must preserve tenant isolation, RBAC, equivalent Human/Agent authorization, policy-driven approvals, scoped credentials, auditability, safe test execution, secret exclusion, one authoritative Alembic graph, reproducible CI/release artifacts, explicit evidence boundaries and documentation reconciliation before closure.

The canonical gap register is `docs/current/PRODUCTION_GAP_REGISTER_2026-09-04.md`.
