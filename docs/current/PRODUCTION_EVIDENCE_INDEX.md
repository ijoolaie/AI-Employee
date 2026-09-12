# Production Evidence Index

**Reconciled:** 2026-09-12  
**Repository:** `ijoolaie/AI-Employee`  
**Purpose:** keep engineering evidence and external-production certification evidence traceable to an immutable release identity.

## Evidence classification

- **ENGINEERING** — repository, CI, local Docker, synthetic-load, simulated-provider, or unit-test evidence. It demonstrates implementation/readiness but does not certify a real production target.
- **EXTERNAL-PENDING** — evidence that can only be completed against a real deployment, real provider, real customer workflow, or independent external assessment.
- **EXTERNAL** — completed evidence captured against the accepted immutable release on a real target.

No P0 external gate may be marked complete from ENGINEERING evidence alone.

## Current release baseline

| Field | Value |
|---|---|
| Repository | `ijoolaie/AI-Employee` |
| Latest exact-SHA certified candidate | `v1.4.0-rc.4` / `4cadd2df003d72de43546466a47e2c66062002c6` |
| Certification run | `34693535048` — SUCCESS |
| Current mainline after documentation reconciliation | Later documentation commits after the certified candidate; fresh exact-SHA certification required for final release promotion |
| Immutable production tag | **PENDING — external release freeze** |
| Container image digests | **PENDING — no external image registry/release pipeline supplied** |
| SBOM | **ENGINEERING-CAPTURED for API/frontend images; attach to immutable published release** |
| Build provenance | **ENGINEERING-CAPTURED CI build metadata; signed/verified external attestation pending** |

The certified candidate above is an immutable engineering/release identity. It is not a claim of production deployment.

## Evidence matrix

| Gate | Evidence source / artifact | Class | Status | Release binding |
|---|---|---|---|---|
| Exact-SHA Production Certification | Run `34693535048`, release identity `v1.4.0-rc.4` | ENGINEERING | Complete | `4cadd2df003d72de43546466a47e2c66062002c6` |
| ORM FK DDL-cycle hardening | PR #499 | ENGINEERING | Complete | merged before certification SHA |
| Certification product gates | Run `34693535048` | ENGINEERING | Complete — 0 failures | `4cadd2df003d72de43546466a47e2c66062002c6` |
| Production-like infrastructure lifecycle | PR #315; merge `93c717969a192ae5b90b909c2c4e8aaa89bea50a`; run `33884955068` | ENGINEERING | Complete | CI run, not real production |
| Data retention/lifecycle implementation | `backend/app/services/retention_service.py`, `backend/scripts/enforce_retention.py`, `docs/current/31_DATA_RETENTION_LIFECYCLE.md` | ENGINEERING | Complete | current main baseline |
| HITL TODO reconciliation | `backend/app/services/run_service.py` update `eec953cd7db43dd515f66c830d4d76038c1ce528` | ENGINEERING | Complete | current main baseline |
| Usage/budget controls | `/api/v1/usage/optimization` + frontend usage surface | ENGINEERING | Complete | current main baseline |
| Cost anomaly/forecast | `/api/v1/usage/cost-forecast` + deterministic anomaly tests | ENGINEERING | Complete | current main baseline |
| Operations dashboard | Existing `/admin/operations` surface | ENGINEERING | Complete | current main baseline |
| Release manifest generation | `scripts/production_release_manifest.sh` + `.github/workflows/release-manifest.yml` | ENGINEERING | Complete | source identity |
| Immutable release build evidence | PR #320 / `.github/workflows/immutable-release-evidence.yml` | ENGINEERING | Complete | exact CI release SHA; registry publication still pending |
| SLO/error-budget contract | Phase 14 SLO validator + CI evidence; SLO Contract Manual v2 run `34693267741` | ENGINEERING | Complete | certified mainline checkpoint; live measurement pending |
| Provider integration preflight | Phase 14 provider validator + CI evidence | ENGINEERING | Complete | live provider validation pending |
| HA/failure-recovery smoke | Phase 14 failure-recovery smoke + CI evidence | ENGINEERING | Complete | production HA/RTO/RPO still external |
| Incident-response drill contract | Phase 14 incident drill + CI evidence | ENGINEERING | Complete | live human/on-call drill still external |
| Alert ownership/routing contract | `ops/alerting/alert-routing.yml` + validator | ENGINEERING | Complete | live paging/routing test still external |
| Runtime isolation + RBAC contract | `backend/scripts/e2e_tenant_rbac_verify.py` + `.github/workflows/runtime-isolation-rbac-contract.yml` + `docs/current/PHASE_14_RUNTIME_ISOLATION_RBAC_ENGINEERING.md` | ENGINEERING | Complete | ephemeral real-stack CI; external actor matrix pending |
| Production network hardening contract | `scripts/validate_production_network_hardening.py` + workflow + docs | ENGINEERING | Complete | compose/private-network contract; deployed perimeter still external |
| Production secret management contract | `scripts/validate_production_secret_management.py` + workflow + docs | ENGINEERING | Complete | secret wiring/leakage boundary; external manager/rotation/recovery pending |
| Delivery manifest bundle | Run `34693267680` | ENGINEERING | SUCCESS | certified mainline checkpoint |
| Production Compose Validation | Run `34693267659` | ENGINEERING | SUCCESS | certified mainline checkpoint |
| Real production deployment | `PRODUCTION_CERTIFICATION_EXECUTION_PACK.md` Phase B | EXTERNAL-PENDING | Blocked | requires operator-controlled target |
| Real backup/restore/DR + RPO/RTO | Execution Pack Phase C | EXTERNAL-PENDING | Blocked | requires real infrastructure |
| Production SLO/SLI/error budget | Execution Pack Phase D | EXTERNAL-PENDING | Blocked | requires real traffic/monitoring |
| Live provider validation | Execution Pack Phase E | EXTERNAL-PENDING | Blocked | requires production-safe provider credentials |
| Vendor → Reseller → Client runtime isolation | Execution Pack Phase F / issue #19 | EXTERNAL-PENDING | Blocked | requires deployed target and actor matrix |
| DAST | Execution Pack Phase G | EXTERNAL-PENDING | Blocked | requires deployed target |
| Independent penetration test | Execution Pack Phase G | EXTERNAL-PENDING | Blocked | requires independent tester |
| Network hardening + secret lifecycle | Execution Pack Phase H | EXTERNAL-PENDING | Blocked | engineering contracts complete; deployed perimeter and secret manager remain external |
| HA/failure recovery + incident drill | Execution Pack Phase I | EXTERNAL-PENDING | Blocked | requires real target and controlled failure permission |
| Alert ownership/on-call test | Execution Pack Phase J | EXTERNAL-PENDING | Blocked | requires monitoring and named operators |
| Customer acceptance | Execution Pack final sequence / issue #269 | EXTERNAL-PENDING | Blocked | requires customer acceptance owner and criteria |

## Release-manifest limitations

The immutable-release CI workflow builds API/frontend images from an exact release SHA, captures local image identities, generates CycloneDX SBOMs, and records CI build metadata. This is stronger engineering evidence than source-only manifest generation. It does **not** create an externally published registry digest, signed attestation, production deployment identity, or customer acceptance record. Those remain external gates.

## External evidence boundary

The `v1.4.0-rc.4` certification is the latest exact-SHA release-candidate evidence. Subsequent documentation reconciliation commits are deliberately not back-attributed to that certification. A release promoted from the reconciled mainline must first receive a fresh exact-SHA certification, then all external records must bind to that same immutable release identity.

## Required external inputs

To convert the pending rows into external evidence, the project needs:

1. An operator-controlled staging/production target with compute, DNS/TLS and ingress access.
2. PostgreSQL, Redis and object-storage access plus an isolated restore target.
3. Production-safe provider credentials delivered through the runtime secret-management mechanism; never commit or paste secret values into the repository.
4. An approved external secret manager with rotation/revocation and recovery procedures.
5. Monitoring/alerting access and named primary/backup on-call ownership.
6. Permission to execute controlled backup/restore, failure, DR and secret-rotation scenarios.
7. An independent security tester for the penetration assessment.
8. A customer acceptance owner and written acceptance criteria.

## Governing document

Use `docs/current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md` for the ordered execution sequence. Use `docs/current/PRODUCTION_GAP_REGISTER_2026-09-04.md` for the canonical gap classification. Update this index whenever a gate receives new evidence, and always record the exact release SHA/tag that the evidence covers.
