# Production Evidence Index

**Reconciled:** 2026-09-19  
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
| Repository | `ijoolaie/AI-Employee` |
| Latest published release | `v1.4.5` |
| Exact certified release SHA | `dba0bb672deb1236b6724bb8851526e656f47967` |
| Production Certification run | `35108008066` — PASS |
| Certification job | `104834133092` — PASS |
| Product Gate Failures | `0` |
| External production deployment | **PENDING** |
| External image registry/deployed digest evidence | **PENDING** |
| External signed provenance/attestation | **PENDING** |

### Current v1.4.5 engineering identity

- RC branch: `main`
- Exact release SHA: `cc94bc9536f4f95680bb7a183313914c116ffcf2`
- Engineering candidate baseline: `cc94bc9536f4f95680bb7a183313914c116ffcf2`
- release GitHub Actions engineering validation: **10/10 release-critical workflows PASS**
- Local production-like certification: **PASS_ENGINEERING_EVIDENCE_EXTERNAL_PENDING**
- release external deployment/certification: **PENDING**
- Do not transfer the `v1.4.2` certification onto release.

## Evidence matrix

| Gate | Evidence | Class | Status |
|---|---|---|---|
| v1.4.2 Exact-SHA Production Certification | Run `35108008066` | ENGINEERING | Complete |
| prior v1.4.2 certification product gates | Run `35108008066` | ENGINEERING | Complete — 0 failures |
| release GitHub Actions engineering validation | SHA `cc94bc...` | ENGINEERING | Complete — 10/10 PASS |
| Backend/frontend/DB engineering | Certification + release CI | ENGINEERING | Complete |
| Auth/RBAC/tenant isolation | Real-stack + release isolation gate | ENGINEERING | Complete; external actor matrix pending |
| Production-like infrastructure lifecycle | release infrastructure + local certification | ENGINEERING | Complete; real target pending |
| Backup/restore rehearsal | Production-like PostgreSQL validation | ENGINEERING | Complete; real target RPO/RTO pending |
| SLO/error-budget contract | SLO validator/manual | ENGINEERING | Complete; live measurement pending |
| Provider integration preflight | Provider validator | ENGINEERING | Complete; live provider validation pending |
| Runtime isolation/RBAC contract | release real-stack gate | ENGINEERING | Complete; external actor matrix pending |
| Network hardening contract | Network validator/workflow | ENGINEERING | Complete; deployed perimeter pending |
| Secret-management contract | Secret validator/workflow | ENGINEERING | Complete; external manager/rotation/recovery pending |
| Failure-recovery/incident contracts | release HA/rollback gates | ENGINEERING | Complete; target rehearsal pending |
| Alert routing contract | `ops/alerting/alert-routing.yml` + validator | ENGINEERING | Complete; live paging test pending |
| Real production deployment | Execution Pack Phase B | EXTERNAL-PENDING | Blocked |
| Real backup/restore/DR + RPO/RTO | Execution Pack Phase C | EXTERNAL-PENDING | Blocked |
| Production SLO/SLI/error budget | Execution Pack Phase D | EXTERNAL-PENDING | Blocked |
| Live provider validation | Execution Pack Phase E | EXTERNAL-PENDING | Blocked |
| Vendor → Reseller → Client isolation | Execution Pack Phase F / #19 | EXTERNAL-PENDING | Blocked |
| DAST on accepted target | Execution Pack Phase G | EXTERNAL-PENDING | Blocked |
| Independent penetration test | Execution Pack Phase G | EXTERNAL-PENDING | Blocked |
| Network hardening + secret lifecycle | Execution Pack Phase H | EXTERNAL-PENDING | Blocked |
| HA/failure recovery + incident drill | Execution Pack Phase I | EXTERNAL-PENDING | Blocked |
| Alert ownership/on-call test | Execution Pack Phase J | EXTERNAL-PENDING | Blocked |
| Vendor/Reseller acceptance | External acceptance | EXTERNAL-PENDING | Blocked |
| Customer acceptance | Execution Pack final sequence / #269 | EXTERNAL-PENDING | Blocked |
| Final commercial go-live authorization | Final gate | EXTERNAL-PENDING | Blocked by P0 evidence |

## Release binding rule

Every completed external evidence record must identify exact release tag/SHA, deployment timestamp, target/environment, relevant artifact/image digest, operator/owner, and evidence artifact/log reference.

No evidence transfers automatically across SHAs. Documentation cannot substitute for target evidence.
