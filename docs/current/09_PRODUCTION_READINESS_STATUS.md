# Production Readiness Status

**Status date:** 2026-09-04

## Current release and project boundary

The repository's current engineering baseline includes the completed Phase 13 implementation and Phase 14.1–14.16 engineering workstreams. Phase 14.11 certification-readiness hardening is also complete. Before external certification, the remaining roadmap is Stage 7 only. **Phase 14.10 — External Production Certification & Customer Acceptance Evidence is Stage 7 and the final gate.**

Repository implementation and CI/release verification remain distinct from external production certification. No repository state alone establishes live deployment, provider operation, measured production SLO attainment, customer acceptance, commercial go-live, or independent certification.

## Ordered remaining work

| Stage | Issue | Status | Purpose |
|---|---:|---|---|
| 1 | #285 | **ENGINEERING COMPLETE / DOCUMENTATION RECONCILED** | Certification-readiness, configuration preflight, cross-platform portability |
| 2 | #286 | **ENGINEERING COMPLETE / DOCUMENTATION RECONCILED** | Tenant-fair scheduling and resource isolation with Redis runtime evidence |
| 3 | #287 | **ENGINEERING COMPLETE / EVIDENCE RECONCILED** | Bounded load/stress and measurable capacity validation |
| 4 | #288 | **ENGINEERING COMPLETE / EVIDENCE RECONCILED** | Security/privacy/compliance engineering extensions |
| 5 | #289 | **ENGINEERING COMPLETE / DOCUMENTATION RECONCILED** | Capacity, cost and operational optimization |
| 6 | #290 | **ENGINEERING COMPLETE / DOCUMENTATION RECONCILED** | V1.5 Human + Agent operating-model evolution |
| 7 | #269 / #210 / #19 | **FINAL / EXTERNAL-PENDING** | External deployment, provider/SLO/DR evidence and ordered acceptance |

Every engineering stage must reconcile the canonical status, priorities, roadmap and this production-readiness document before closure.

## Production infrastructure validation evidence

PR #315 merged to `main` at `93c717969a192ae5b90b909c2c4e8aaa89bea50a`. Validation run `33884955068` passed on GitHub-hosted Linux infrastructure. The run validated the production Compose contract, built the API/Worker/Beat/Frontend images, started PostgreSQL/Redis/storage, waited for dependency readiness, applied Alembic migrations, started API/Worker/Beat/Frontend, verified PostgreSQL and Redis persistence across restart, verified API dependency readiness and Frontend HTTP reachability, and executed a real PostgreSQL custom-format `pg_dump` plus isolated `pg_restore`. The ephemeral environment was torn down after the run.

This evidence demonstrates repository production-like lifecycle/recovery behavior. It does **not** establish real production deployment, provider behavior, measured production SLO/error budget, durable target backup cadence, target-environment RPO/RTO, external rollback rehearsal, security/compliance certification or customer acceptance.

## Phase 14.16 engineering evidence

PR #312 merged to `main` at `7657b4244a47af95960e5854fa52f92a0dbe618b`. It adds tenant-scoped `/api/v1/workspace`, a unified read model over WorkItems and pending workflow/tool approvals, and Human/Agent executor queue counts. Existing assignment and approval mutation APIs remain authoritative, and the workspace endpoint is protected by the existing `audit.read` permission boundary.

Verification: backend/frontend CI, Python/JavaScript CodeQL, architecture, production observability and production rollback/alerting checks passed on the merge candidate. This is engineering/productization evidence only. It does not establish production deployment, external customer acceptance, production SLO attainment or external certification.

## Phase 14.15 engineering evidence

PR #311 merged to `main` at `56984bc793ba3119f8c6d45bf9b03f738ce2d59e`. It adds measured monthly unit economics from existing tenant-scoped AI provider and Run records, cost per successful WorkItem, deterministic plan budget utilization states, actionable optimization guidance and worker-sizing decision support using observed throughput with explicit utilization headroom. The vendor platform-admin `/api/v1/admin/optimization` endpoint is protected by the existing platform-admin/vendor authorization boundary.

Verification: CodeQL, full backend/frontend CI, architecture, security/privacy, observability and rollback/alerting checks passed. This is engineering decision support only. It does not establish production worker capacity, provider throughput, production SLO attainment or customer-scale acceptance.

## Phase 14.11 certification-readiness evidence

PR #291 delivered fail-fast configuration preflight for the local certification harness, cross-platform LF normalization through `.gitattributes`, reproducibility/secret-safe evidence handling and canonical documentation reconciliation. This is engineering preparation only and does not satisfy external certification.

## Phase 14.14 engineering evidence

Phase 14.14 is merged to main at `0789d091ab8f804d7bfc853470b9df42108085ed`. The implementation adds deterministic recursive redaction for credentials, tokens, connection strings and direct PII before structured audit metadata is persisted or JSON logs are emitted; tenant-scoped authorization and tool-side-effect regression coverage; and a dedicated dependency/security gate.

Verification: security/privacy regression suite, Ruff and `pip-audit` passed; Python and JavaScript CodeQL passed; full CI, architecture, observability and rollback/alerting checks passed on the merge candidate. Security evidence artifact: `phase-14-14-security-27e19b67ac58776796b3f3db89dd402cbc958a45`, SHA256 `209a4b4a4249cd7c26cf17f83eb77a9b59de012416a2053632d7a5bc19844696`.

This is engineering preparation only. External pentest findings, legal compliance attestations and target production security evidence remain external.

## Stage 7 — External Production Certification

**Status: EXTERNAL-PENDING / FINAL STAGE.**

Required evidence must be attached to one exact immutable release identity: release SHA/tag and checksums, real-target deployment record, live provider validation, measured production SLO/error budget, target backup/restore with RPO/RTO, applicable independent security/compliance evidence, ordered Vendor → Reseller → Client acceptance, rollback evidence, and final exceptions/residual-risk disposition.

The existing repository, CI and synthetic load/security evidence cannot substitute for these external records.

## Security rule

No production host, private key, registry credential, webhook secret, payment secret, customer data or environment-specific access token belongs in Git history. Missing required production inputs must fail closed.
