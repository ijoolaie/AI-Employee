# Production Evidence Index

**Reconciled:** 2026-09-16  
**Repository:** `ijoolaie/AI-Employee`  
**Purpose:** keep engineering evidence and external-production certification evidence traceable to an immutable release identity.

## Evidence classification

- **ENGINEERING** — repository, CI, local Docker, synthetic-load, simulated-provider, or test evidence. It demonstrates implementation/readiness but does not certify a real production target.
- **EXTERNAL-PENDING** — evidence that can only be completed against a real deployment, real provider, real customer workflow, or independent external assessment.
- **EXTERNAL** — completed evidence captured against the accepted immutable release on a real target.

No P0 external gate may be marked complete from ENGINEERING evidence alone.

## Current release baseline

| Field | Value |
|---|---|
| Repository | `ijoolaie/AI-Employee` |
| Latest published release | `v1.4.2` |
| Exact certified release SHA | `dba0bb672deb1236b6724bb8851526e656f47967` |
| Production Certification run | `35108008066` — PASS |
| Certification job | `104834133092` — PASS |
| Product Gate Failures | `0` |
| External production deployment | **PENDING** |
| External image registry/deployed digest evidence | **PENDING** |
| External signed provenance/attestation | **PENDING** |

## Evidence matrix

| Gate | Evidence | Class | Status |
|---|---|---|---|
| Exact-SHA Production Certification | Run `35108008066` | ENGINEERING | Complete |
| Certification product gates | Run `35108008066` | ENGINEERING | Complete — 0 failures |
| Backend/frontend/DB | Certification suite | ENGINEERING | Complete |
| Auth/RBAC/tenant isolation | Certification product gates | ENGINEERING | Complete; external actor matrix pending |
| Stage 9 governed optimization | `v1.4.2` certification | ENGINEERING | Complete |
| Production-like infrastructure lifecycle | CI production Compose validation | ENGINEERING | Complete; real target pending |
| Backup/restore rehearsal | Production-like PostgreSQL validation | ENGINEERING | Complete; real target RPO/RTO pending |
| SLO/error-budget contract | SLO validator/manual | ENGINEERING | Complete; live measurement pending |
| Provider integration preflight | Provider validator | ENGINEERING | Complete; live provider validation pending |
| Runtime isolation/RBAC contract | Real-stack CI gate | ENGINEERING | Complete; external actor matrix pending |
| Network hardening contract | Network validator/workflow | ENGINEERING | Complete; deployed perimeter pending |
| Secret-management contract | Secret validator/workflow | ENGINEERING | Complete; external manager/rotation/recovery pending |
| Failure-recovery/incident contracts | Engineering rehearsal | ENGINEERING | Complete; target rehearsal pending |
| Alert routing contract | `ops/alerting/alert-routing.yml` + validator | ENGINEERING | Complete; live paging test pending |
| Data retention/lifecycle | Retention service/scripts/tests | ENGINEERING | Complete; target lifecycle verification pending |
| Usage/budget/cost controls | Usage/forecast surfaces | ENGINEERING | Complete; target commercial validation pending |
| Real production deployment | Execution Pack Phase B | EXTERNAL-PENDING | Blocked |
| Real backup/restore/DR + RPO/RTO | Execution Pack Phase C | EXTERNAL-PENDING | Blocked |
| Production SLO/SLI/error budget | Execution Pack Phase D | EXTERNAL-PENDING | Blocked |
| Live provider validation | Execution Pack Phase E | EXTERNAL-PENDING | Blocked |
| Vendor → Reseller → Client isolation | Execution Pack Phase F / #19 | EXTERNAL-PENDING | Blocked |
| DAST | Execution Pack Phase G | EXTERNAL-PENDING | Blocked |
| Independent penetration test | Execution Pack Phase G | EXTERNAL-PENDING | Blocked |
| Network hardening + secret lifecycle | Execution Pack Phase H | EXTERNAL-PENDING | Blocked |
| HA/failure recovery + incident drill | Execution Pack Phase I | EXTERNAL-PENDING | Blocked |
| Alert ownership/on-call test | Execution Pack Phase J | EXTERNAL-PENDING | Blocked |
| Vendor/Reseller acceptance | External acceptance | EXTERNAL-PENDING | Blocked |
| Customer acceptance | Execution Pack final sequence / #269 | EXTERNAL-PENDING | Blocked |
| Final commercial go-live authorization | Final gate | EXTERNAL-PENDING | Blocked by P0 evidence |

## Required external inputs

1. Operator-controlled staging/production target with compute, DNS/TLS and ingress access.
2. PostgreSQL, Redis and object-storage access plus isolated restore target.
3. Production-safe provider credentials delivered through the runtime secret-management mechanism; never commit or paste secret values.
4. Approved external secret manager with rotation/revocation and recovery procedures.
5. Monitoring/alerting access and named primary/backup on-call ownership.
6. Permission to execute controlled backup/restore, failure, DR and secret-rotation scenarios.
7. Independent security tester for the penetration assessment.
8. Customer acceptance owner and written acceptance criteria.

## Release binding rule

Every completed external evidence record must identify:

- exact release tag;
- exact release SHA;
- deployment timestamp;
- target/environment identifier;
- relevant artifact/image digest;
- operator/owner;
- evidence artifact or log reference.

No evidence transfers automatically across SHAs. Documentation cannot substitute for target evidence.

## Governing documents

- `docs/current/PRODUCTION_GAP_REGISTER_2026-09-04.md`
- `docs/current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md`
- `docs/current/09_PRODUCTION_READINESS_STATUS.md`
- `docs/00_START_HERE/CURRENT_PRIORITIES.md`
- `docs/00_START_HERE/CURRENT_STATUS.md`
- `docs/releases/RELEASE_TRUTH_LEDGER.md`
