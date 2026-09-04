# Current Priorities

**Reconciled:** 2026-09-04

## Ordered remaining work

Phase 13 and Phase 14.1–14.9 engineering are complete. The remaining work is now intentionally sequenced so that **External Production Certification & Customer Acceptance is the final stage**.

### Stage 1 — Certification Readiness & Cross-Platform Hardening
**Issue #285 — IN PROGRESS**

- normalize shell-script line endings across platforms;
- add fail-fast application configuration preflight to the local certification harness;
- improve reproducibility and secret-safe evidence handling;
- reconcile all status/readiness documents after completion.

### Stage 2 — Tenant-Fair Scheduling & Resource Isolation
**Issue #286 — ENGINEERING COMPLETE / DOCUMENTATION RECONCILED**

- explicit per-tenant fairness/resource shares;
- starvation protection;
- measurable fairness and negative-path regression tests;
- preserve RBAC, tenant isolation and approval boundaries.

### Stage 3 — Load, Stress & Capacity Validation
**Issue #287 — QUEUED**

- reproducible API/WorkItem/queue-worker load scenarios;
- routing, cost-control and recovery stress paths;
- measurable thresholds and retained evidence artifacts;
- reconcile results to exact commit/artifact identities.

### Stage 4 — Security, Privacy & Compliance Engineering Extensions
**Issue #288 — QUEUED**

- threat-model refresh;
- security regression expansion;
- privacy/data-retention boundary checks;
- compliance-control mapping and pentest-ready scope/runbook.

External pentest/attestation remains external evidence and is not fabricated by repository work.

### Stage 5 — Capacity, Cost & Operational Optimization
**Issue #289 — QUEUED**

- capacity model and sizing guidance;
- cost-per-WorkItem visibility;
- budget/resource optimization;
- operational runbooks and guardrails.

### Stage 6 — V1.5 Human + Agent Operating Model
**Issue #290 — QUEUED**

- formalize Human + Agent operating-model contracts on unified WorkItem;
- align Platform/Reseller/Client UX and APIs;
- governance, approvals and auditability;
- migrate remaining Employee-backed capabilities incrementally and safely.

### Stage 7 — External Production Certification & Customer Acceptance
**Issues #269 / #210 / #19 — FINAL / EXTERNAL-PENDING**

Only after Stages 1–6 are complete and their documentation is reconciled:

- freeze one exact immutable release candidate;
- reconcile artifacts, migrations and checksums;
- deploy that exact identity to the real target;
- collect provider, production SLO/error-budget and DR RPO/RTO evidence;
- complete security/compliance review and external rollback evidence;
- execute ordered Vendor → Reseller → Client acceptance where applicable;
- record exceptions/residual risks and the final certification decision.

This is the final stage. CI, local runtime validation, browser acceptance or rehearsal evidence cannot substitute for independent external evidence.

## Completed baseline

- Phase 11 Unified Execution acceptance — complete.
- Phase 12 P12.1–P12.6 — implemented and operationally hardened.
- Phase 13 Agent Teams & Marketplace — engineering complete.
- Phase 14.1–14.9 — engineering complete.
- Phase 14.10 local production-like certification harness — implemented; successful local run remains engineering evidence only.

## Evidence rules

- CI/internal certification = engineering evidence.
- Local real-stack validation = local evidence.
- External production/customer acceptance = independent external evidence.
- Certification never transfers automatically across commit SHAs.
- Never fabricate production configuration, customer acceptance, provider evidence or compliance certification merely to satisfy a gate.
