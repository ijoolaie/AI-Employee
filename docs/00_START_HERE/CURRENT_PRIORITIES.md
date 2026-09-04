# Current Priorities

**Reconciled:** 2026-09-04

## Ordered remaining work

Phase 13 and Phase 14.1–14.14 engineering are complete. The remaining work is intentionally sequenced so that **External Production Certification & Customer Acceptance is the final stage**.

### Stage 1 — Certification Readiness & Cross-Platform Hardening
**Issue #285 — IN PROGRESS**

Configuration preflight, cross-platform portability, reproducibility and secret-safe evidence handling remain in scope.

### Stage 2 — Tenant-Fair Scheduling & Resource Isolation
**Issue #286 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

Tenant fairness, starvation protection and resource shares are backed by Redis runtime evidence.

### Stage 3 — Load, Stress & Capacity Validation
**Issue #287 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

Phase 14.13 has a bounded synthetic CI evidence harness covering API load, scheduler/routing capacity, tenant resource admission and lease-expiry recovery. The evidence is bound to test-merge SHA `98771d087bc658d633a99a63c9ef0476e13c18ae`, final Phase 14.13 main SHA `599cb8b167103e3627678739f8440d854cad55f1`, and artifact SHA256 `1f19b7d7ee6adc0623904bec76eaed4619ee88bca02af7d65107dae7ae925845`.

### Stage 4 — Security, Privacy & Compliance Engineering Extensions
**Issue #288 — ENGINEERING COMPLETE / EVIDENCE RECONCILED**

Phase 14.14 engineering evidence is complete on merged main SHA `0789d091ab8f804d7bfc853470b9df42108085ed`. The dedicated security gate passed regression tests, Ruff and `pip-audit`; CodeQL Python/JavaScript, CI, architecture, observability and rollback/alerting checks also passed for the merge candidate. Security evidence artifact: `phase-14-14-security-27e19b67ac58776796b3f3db89dd402cbc958a45`, SHA256 `209a4b4a4249cd7c26cf17f83eb77a9b59de012416a2053632d7a5bc19844696`. External pentest/certification remains external evidence.

### Stage 5 — Capacity, Cost & Operational Optimization
**Issue #289 — QUEUED**

Use measured load results to establish capacity/sizing guidance, cost visibility and operational optimization.

### Stage 6 — V1.5 Human + Agent Operating Model
**Issue #290 — QUEUED**

Formalize Human + Agent operating-model contracts, governance, approvals, auditability and remaining capability migration.

### Stage 7 — External Production Certification & Customer Acceptance
**Issues #269 / #210 / #19 — FINAL / EXTERNAL-PENDING**

Only after Stages 1–6 are complete and documentation is reconciled: freeze an immutable release, deploy that exact identity to the real target, collect provider/SLO/DR evidence, complete applicable independent security/compliance review, execute ordered acceptance and record the final decision.

## Phase 14.14 engineering evidence

The merged Phase 14.14 implementation introduces a deterministic recursive redaction boundary for credentials, connection strings, tokens and direct PII in structured audit metadata and JSON logs, tenant-scoped authorization/tool-side-effect regression coverage, and a dedicated dependency/security gate. The refreshed threat model, privacy/retention boundary, compliance-control matrix and external-pentest-ready scope/runbook are recorded in `docs/current/PHASE_14_14_SECURITY_PRIVACY_COMPLIANCE.md`.

## Evidence rules

- CI/internal load and security validation = engineering evidence.
- Local real-stack validation = local evidence.
- External production/customer acceptance = independent external evidence.
- Certification never transfers automatically across commit SHAs.
- Never fabricate production configuration, customer acceptance, provider evidence or compliance certification.
