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
| Latest published release | `v1.4.6` |
| Exact certified release SHA | `f3d60031332450ba616e2a1c705e85c0c2c5aefd` |
| Production Certification run | `35427967347` — PASS (exact `v1.4.6` tag) |
| Certification job | `105857140334` — PASS |
| Product Gate Failures | `0` |
| External production deployment | **PENDING** |
| External image registry/deployed digest evidence | **PENDING** |
| External signed provenance/attestation | **PENDING** |

### Current v1.4.6 certified release identity

- Release tag: `v1.4.6`
- Exact certified SHA: `f3d60031332450ba616e2a1c705e85c0c2c5aefd`
- Production Certification run: `35427967347` — PASS
- Product Gate Failures: `0`
- Evidence artifact: `production-certification-evidence-v1.4.6-f3d60031332450ba616e2a1c705e85c0c2c5aefd`
- Artifact SHA256: `fc12afd3da164e1d1787bc11e2a39d3c3d019e84d3c9516ddf7819f79e905d4d`
- External production deployment: **PENDING** (`production_deployment_claimed=false`)
- Certification is bound only to the exact SHA above; it does not transfer to another SHA.

### Historical v1.4.5 RC1 engineering identity

- RC branch: `release/v1.4.5-rc1`
- Exact RC1 SHA: `0976537441ebc2560624022bfaabb33096f5011c`
- Engineering candidate baseline: `a9d5cdd`
- RC1 GitHub Actions engineering validation: **10/10 current release-critical workflows PASS**
- Local production-like certification: **PASS_ENGINEERING_EVIDENCE_EXTERNAL_PENDING**
- RC1 external deployment/certification: **PENDING**
- Do not transfer any historical certification onto RC1.

## Evidence matrix

| Gate | Evidence | Class | Status |
|---|---|---|---|
| v1.4.6 Exact-SHA Production Certification | Run `35427967347` | ENGINEERING | Complete — exact tag/SHA, 0 Product Gate failures |
| v1.4.6 certification product gates | Run `35427967347` | ENGINEERING | Complete — 0 failures |
| RC1 GitHub Actions engineering validation | SHA `097653...` | ENGINEERING | Historical — 10/10 PASS |
| Backend/frontend/DB engineering | Certification + RC1 CI | ENGINEERING | Complete |
| Auth/RBAC/tenant isolation | Real-stack + RC1 isolation gate | ENGINEERING | Complete; external actor matrix pending |
| Production-like infrastructure lifecycle | RC1 infrastructure + local certification | ENGINEERING | Complete; real target pending |
| Backup/restore rehearsal | Production-like PostgreSQL validation | ENGINEERING | Complete; real target RPO/RTO pending |
| SLO/error-budget contract | SLO validator/manual | ENGINEERING | Complete; live measurement pending |
| Provider integration preflight | Provider validator | ENGINEERING | Complete; live provider validation pending |
| Runtime isolation/RBAC contract | RC1 real-stack gate | ENGINEERING | Complete; external actor matrix pending |
| Network hardening contract | Network validator/workflow | ENGINEERING | Complete; deployed perimeter pending |
| Secret-management contract | Secret validator/workflow | ENGINEERING | Complete; external manager/rotation/recovery pending |
| Failure-recovery/incident contracts | RC1 HA/rollback gates | ENGINEERING | Complete; target rehearsal pending |
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
