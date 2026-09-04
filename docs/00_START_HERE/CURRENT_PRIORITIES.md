# Current Priorities

**Reconciled:** 2026-09-04

## Ordered remaining work

Phase 13 and Phase 14.1–14.15 engineering are complete. Phase 14.11 certification-readiness hardening is also complete. The remaining work is intentionally sequenced so that **External Production Certification & Customer Acceptance is the final stage**.

### Stage 1 — Certification Readiness & Cross-Platform Hardening
**Issue #285 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

PR #291 delivered the fail-fast configuration preflight, cross-platform LF normalization, reproducibility/secret-safe evidence handling and canonical documentation reconciliation. This stage remains engineering evidence only and does not satisfy external certification.

### Stage 2 — Tenant-Fair Scheduling & Resource Isolation
**Issue #286 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

Tenant fairness, starvation protection and resource shares are backed by Redis runtime evidence.

### Stage 3 — Load, Stress & Capacity Validation
**Issue #287 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

Phase 14.13 has a bounded synthetic CI evidence harness covering API load, scheduler/routing capacity, tenant resource admission and lease-expiry recovery.

### Stage 4 — Security, Privacy & Compliance Engineering Extensions
**Issue #288 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

Phase 14.14 engineering evidence is complete on merged main SHA `0789d091ab8f804d7bfc853470b9df42108085ed`. Security gate, regression tests, Ruff, `pip-audit`, CodeQL, full CI, architecture, observability and rollback/alerting checks passed. Security evidence artifact: `phase-14-14-security-27e19b67ac58776796b3f3db89dd402cbc958a45`, SHA256 `209a4b4a4249cd7c26cf17f83eb77a9b59de012416a2053632d7a5bc19844696`. External pentest/certification remains external evidence.

### Stage 5 — Capacity, Cost & Operational Optimization
**Issue #289 — ENGINEERING COMPLETE / PR #311 MERGED**

Phase 14.15 delivers measured monthly unit economics, cost per successful WorkItem, plan budget utilization/warning signals, optimization actions and worker-sizing decision support based on observed throughput with explicit headroom. CI passed for CodeQL, full backend/frontend CI, architecture, security/privacy, observability and rollback/alerting. Production capacity certification remains external.

### Stage 6 — V1.5 Human + Agent Operating Model
**Issue #290 — QUEUED / NEXT**

Formalize Human + Agent operating-model contracts, governance, approvals, auditability and remaining capability migration.

### Stage 7 — External Production Certification & Customer Acceptance
**Issues #269 / #210 / #19 — FINAL / EXTERNAL-PENDING**

Only after Stages 1–6 are complete and documentation is reconciled: freeze an immutable release, deploy that exact identity to the real target, collect provider/SLO/DR evidence, complete applicable independent security/compliance review, execute ordered acceptance and record the final decision.

## Evidence rules

- CI/internal load and security validation = engineering evidence.
- Local real-stack validation = local evidence.
- External production/customer acceptance = independent external evidence.
- Certification never transfers automatically across commit SHAs.
- Never fabricate production configuration, customer acceptance, provider evidence or compliance certification.
