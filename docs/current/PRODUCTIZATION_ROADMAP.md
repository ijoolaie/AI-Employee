# AI Employee Platform — Productization & Delivery Roadmap

## Current position — 2026-09-05

V1.4 remains the frozen architecture foundation. V1.5 is the Human + Agent operating-model extension. Phase 11 is complete, Phase 12 is operationally hardened, Phase 13 engineering is complete, and Phase 14.1–14.16 engineering is complete. Production-like infrastructure validation is complete in CI. The tracked P1 engineering/productization gates are reconciled as implemented/complete, and the latest Stage 7 engineering contracts are complete where applicable.

The current engineering main baseline is `44e1c0f339e2440bafe9f4e122d2b63dc2fc09c2`. This is an engineering baseline, not an accepted production identity.

The remaining roadmap is intentionally ordered so **External Production Certification & Customer Acceptance is the final gate**. The gaps below are explicitly tracked so that no previously identified production, operational, security, commercial or productization requirement is lost between roadmap, status and acceptance records.

## Completed engineering stages

### Stage 1 — Phase 14.11: Certification Readiness & Cross-Platform Hardening
**Issue #285 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

### Stage 2 — Phase 14.12: Tenant-Fair Scheduling & Resource Isolation
**Issue #286 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

### Stage 3 — Phase 14.13: Load, Stress & Capacity Validation
**Issue #287 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

### Stage 4 — Phase 14.14: Security, Privacy & Compliance Engineering Extensions
**Issue #288 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

### Stage 5 — Phase 14.15: Capacity, Cost & Operational Optimization
**Issue #289 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

### Stage 6 — Phase 14.16: V1.5 Human + Agent Operating Model
**Issue #290 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

PR #312 merged at `7657b4244a47af95960e5854fa52f92a0dbe618b`. The tenant-scoped workspace read model combines WorkItems, pending workflow/tool approvals and Human/Agent executor queue counts while preserving existing authorization and mutation boundaries.

## Engineering reconciliation checkpoints after infrastructure validation

- **PR #315** — production-like infrastructure lifecycle, persistence and isolated PostgreSQL backup/restore; CI run `33884955068` passed.
- **PR #320** — immutable-release build evidence from an exact release SHA, local image identities, CycloneDX SBOMs and CI build metadata. External registry publication, signed attestation and production release acceptance remain pending.
- **PR #323** — production-like HA/failure-recovery engineering rehearsal. Target failover/RTO/RPO certification remains external.
- **PR #324** — SLO/error-budget engineering contract with deterministic objectives and synthetic observations. Live target measurement remains external.
- **PR #325** — Stripe/Shopify provider integration preflight. Live authentication, transactions and webhook behavior remain external.
- **PR #327** — alert ownership/routing contract. Live paging, staffed on-call coverage and human escalation remain external.
- **PR #329** — runtime isolation/RBAC real-stack CI gate. External Vendor/Reseller/Customer actor-matrix certification remains pending.
- **PR #330** — production network hardening contract. Deployed firewall/security-group/WAF/TLS/egress evidence remains external.
- **PR #331** — production secret-management contract. External secret-manager configuration, rotation/revocation and recovery remain pending.

The P1 gates are also reconciled: retention is engineering-implemented; HITL approval-path documentation is complete; canonical documentation/evidence reconciliation is complete; the operations dashboard is confirmed via `/admin/operations`; usage/budget/cost controls and deterministic anomaly/forecasting are implemented.

## Stage 7 — External Production Certification & Customer Acceptance
**Issues #269 / #210 / #19 — FINAL / EXTERNAL-PENDING**

Stage 7 is expanded into the following ordered work packages. Items marked **EXTERNAL** require the real deployment/customer/provider environment and cannot be closed from repository evidence alone. Items marked **MIXED** require repository readiness plus external execution/evidence. Items marked **ENGINEERING** are repository/product work.

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
| P1 | 7.16 Human-in-the-loop TODO reconciliation | ENGINEERING | Approval-path behavior documented accurately; no stale TODO claim remains |
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
