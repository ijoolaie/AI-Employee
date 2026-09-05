# Production Evidence Index

**Prepared:** 2026-09-05  
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
| Main baseline at index creation | `62211f75dec6c060c2ab85ed980178c3deac1c93` |
| Immutable production tag | **PENDING — external release freeze** |
| Container image digests | **PENDING — no external image registry/release pipeline supplied** |
| SBOM | **PENDING — attach to immutable release when published** |
| Build provenance | **PENDING — attach to immutable release when published** |

The baseline above is a repository engineering identity, not a production certification identity.

## Evidence matrix

| Gate | Evidence source / artifact | Class | Status | Release binding |
|---|---|---|---|---|
| Certification-readiness hardening | Phase 14.11 / PR #291 | ENGINEERING | Complete | merged main history |
| Tenant resource shares | Phase 14.12 / PR #292 | ENGINEERING | Complete | merged main history |
| Bounded synthetic capacity | Phase 14.13 / PR #306; artifact SHA `1f19b7d7ee6adc0623904bec76eaed4619ee88bca02af7d65107dae7ae925845` | ENGINEERING | Complete | historical engineering evidence |
| Security/privacy hardening | Phase 14.14 / PR #310; commit `0789d091ab8f804d7bfc853470b9df42108085ed`; artifact SHA `209a4b4a4249cd7c26cf17f83eb77a9b59de012416a2053632d7a5bc19844696` | ENGINEERING | Complete | historical engineering evidence |
| Capacity/cost optimization | Phase 14.15 / PR #311; commit `56984bc793ba3119f8c6d45bf9b03f738ce2d59e` | ENGINEERING | Complete | historical engineering evidence |
| Workspace read model | Phase 14.16 / PR #312; commit `7657b4244a47af95960e5854fa52f92a0dbe618b` | ENGINEERING | Complete | historical engineering evidence |
| Production-like infrastructure lifecycle | PR #315; merge `93c717969a192ae5b90b909c2c4e8aaa89bea50a`; run `33884955068` | ENGINEERING | Complete | CI run, not real production |
| Data retention/lifecycle implementation | `backend/app/services/retention_service.py`, `backend/scripts/enforce_retention.py`, `docs/current/31_DATA_RETENTION_LIFECYCLE.md` | ENGINEERING | Complete | current main baseline |
| HITL TODO reconciliation | `backend/app/services/run_service.py` update `eec953cd7db43dd515f66c830d4d76038c1ce528` | ENGINEERING | Complete | current main baseline |
| Usage/budget controls | `/api/v1/usage/optimization` + frontend usage surface | ENGINEERING | Complete | current main baseline |
| Cost anomaly/forecast | `/api/v1/usage/cost-forecast` + deterministic anomaly tests | ENGINEERING | Complete | current main baseline |
| Operations dashboard | Existing `/admin/operations` surface | ENGINEERING | Complete | current main baseline |
| Release manifest generation | `scripts/production_release_manifest.sh` + `.github/workflows/release-manifest.yml` | ENGINEERING | Complete | source identity only |
| Real production deployment | `PRODUCTION_CERTIFICATION_EXECUTION_PACK.md` Phase B | EXTERNAL-PENDING | Blocked | requires operator-controlled target |
| Real backup/restore/DR + RPO/RTO | Execution Pack Phase C | EXTERNAL-PENDING | Blocked | requires real infrastructure |
| Production SLO/SLI/error budget | Execution Pack Phase D | EXTERNAL-PENDING | Blocked | requires real traffic/monitoring |
| Live provider validation | Execution Pack Phase E | EXTERNAL-PENDING | Blocked | requires production-safe provider credentials |
| Vendor → Reseller → Client runtime isolation | Execution Pack Phase F / issue #19 | EXTERNAL-PENDING | Blocked | requires deployed target and actor matrix |
| DAST | Execution Pack Phase G | EXTERNAL-PENDING | Blocked | requires deployed target |
| Independent penetration test | Execution Pack Phase G | EXTERNAL-PENDING | Blocked | requires independent tester |
| Network hardening + secret lifecycle | Execution Pack Phase H | EXTERNAL-PENDING | Blocked | requires real network/secret manager |
| HA/failure recovery + incident drill | Execution Pack Phase I | EXTERNAL-PENDING | Blocked | requires real target and controlled failure permission |
| Alert ownership/on-call test | Execution Pack Phase J | EXTERNAL-PENDING | Blocked | requires monitoring and named operators |
| Customer acceptance | Execution Pack final sequence / issue #269 | EXTERNAL-PENDING | Blocked | requires customer acceptance owner and criteria |

## Release-manifest limitations

The current release-manifest workflow records source SHA/tag and dependency lockfile checksums without exposing secrets. It intentionally leaves container image digests, SBOM and provenance empty because no external image registry/build-attestation pipeline is currently available. Those fields must be populated before external certification; placeholders must not be interpreted as evidence.

## Required external inputs

To convert the pending rows into external evidence, the project needs:

1. An operator-controlled staging/production target with compute, DNS/TLS and ingress access.
2. PostgreSQL, Redis and object-storage access plus an isolated restore target.
3. Production-safe provider credentials delivered through the runtime secret-management mechanism; never commit or paste secret values into the repository.
4. Monitoring/alerting access and named primary/backup on-call ownership.
5. Permission to execute controlled backup/restore, failure and DR scenarios.
6. An independent security tester for the penetration assessment.
7. A customer acceptance owner and written acceptance criteria.

## Governing document

Use `docs/current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md` for the ordered execution sequence. Use `docs/current/PRODUCTION_GAP_REGISTER_2026-09-04.md` for the canonical gap classification. Update this index whenever a gate receives new evidence, and always record the exact release SHA/tag that the evidence covers.
