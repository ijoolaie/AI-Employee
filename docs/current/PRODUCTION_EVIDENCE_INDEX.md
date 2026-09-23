# Production Evidence Index

**Reconciled:** 2026-09-23  
**Repository:** `ijoolaie/AI-Employee`  
**Purpose:** keep engineering evidence and external-production certification evidence traceable to an immutable release identity.

## Evidence classification

- **ENGINEERING** — repository, CI, local Docker, synthetic-load, simulated-provider, or test evidence.
- **EXTERNAL-PENDING** — evidence requiring a real deployment, real provider, real customer workflow, or independent external assessment.
- **EXTERNAL** — completed evidence captured against the accepted immutable release on a real target.

No P0 external gate may be marked complete from ENGINEERING evidence alone.

## Current release baseline

| Field | Value |
|---|---|
| Latest published release | `v1.4.10` |
| Exact certified release SHA | `b09f3e35d512e3c4d21be9d930539cbbe1d2d451` |
| Stable Git tag | **VERIFIED** |
| GitHub Release | **PUBLISHED** |
| Production Certification | Run `35840044046` / Job `107112696112` — PASS |
| Product Gate Failures | `0` |
| Frontend Playwright | `8/8 PASS` |
| External production deployment | **PENDING** |
| External image registry/deployed digest evidence | **PENDING** |
| External signed provenance/attestation | **PENDING** |

## v1.4.10 certification identity

- Release tag: `v1.4.10`
- Exact certified SHA: `b09f3e35d512e3c4d21be9d930539cbbe1d2d451`
- Evidence artifact: `production-certification-evidence-v1.4.10-b09f3e35d512e3c4d21be9d930539cbbe1d2d451`
- Evidence SHA256: `73b193ae14d886a8bda83e65a1486cff7d8bedeb04ec32d78f469dcf8037501b`
- Artifact ID: `10740739447`
- `production_deployment_claimed=false`

## Evidence matrix

| Gate | Class | Status |
|---|---|---|
| v1.4.10 Exact-SHA Production Certification | ENGINEERING | PASS |
| Product gates / tenant isolation / RBAC | ENGINEERING | PASS |
| Frontend Playwright | ENGINEERING | PASS — 8/8 |
| Production-like infrastructure lifecycle | ENGINEERING | PASS |
| Backup/restore rehearsal | ENGINEERING | PASS; target RPO/RTO pending |
| SLO/error-budget engineering contract | ENGINEERING | PASS; live measurement pending |
| Provider integration preflight | ENGINEERING | PASS; live validation pending |
| Network hardening contract | ENGINEERING | PASS; deployed perimeter pending |
| Secret-management contract | ENGINEERING | PASS; external lifecycle pending |
| Failure-recovery/rollback contract | ENGINEERING | PASS; target rehearsal pending |
| Alert routing contract | ENGINEERING | PASS; live paging test pending |
| Real production deployment | EXTERNAL-PENDING | NOT VERIFIED |
| Deployed image/digest identity | EXTERNAL-PENDING | NOT VERIFIED |
| Real backup/restore/DR + measured RPO/RTO | EXTERNAL-PENDING | NOT VERIFIED |
| Production SLO/SLI/error budget | EXTERNAL-PENDING | NOT VERIFIED |
| Live provider/payment validation | EXTERNAL-PENDING | NOT VERIFIED |
| Vendor → Reseller → Customer isolation | EXTERNAL-PENDING | NOT VERIFIED |
| Authenticated DAST on accepted target | EXTERNAL-PENDING | NOT VERIFIED |
| Independent penetration/security review | EXTERNAL-PENDING | NOT VERIFIED |
| Network/TLS/secret lifecycle on target | EXTERNAL-PENDING | NOT VERIFIED |
| HA/failure recovery + incident drill | EXTERNAL-PENDING | NOT VERIFIED |
| Alert ownership/on-call test | EXTERNAL-PENDING | NOT VERIFIED |
| Vendor → Reseller → Customer acceptance | EXTERNAL-PENDING | NOT VERIFIED |
| Final commercial go-live authorization | EXTERNAL-PENDING | NOT VERIFIED |

## Release binding rule

Every completed external evidence record must identify exact release tag/SHA, deployment timestamp, target/environment, relevant artifact/image digest, operator/owner, and evidence artifact/log reference.

No evidence transfers automatically across SHAs. Documentation cannot substitute for target evidence.
