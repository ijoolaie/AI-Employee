# Production Readiness Status

**Status date:** 2026-09-12  
**Latest certified candidate:** `v1.4.0-rc.4`  
**Certified candidate SHA:** `4cadd2df003d72de43546466a47e2c66062002c6`  
**Certification run:** `34693535048` — SUCCESS  
**Current mainline:** `main` — documentation reconciliation commits landed after the certified SHA; therefore a fresh exact-SHA certification is required before final release promotion.

## Current release and project boundary

The repository has completed the tracked engineering hardening and the `v1.4.0-rc.4` exact-SHA Production Certification suite passed. PR #499 also removed the SQLAlchemy workflow FK metadata cycle warning without weakening FK integrity.

The certified candidate and the current documentation-reconciled mainline must remain distinct. A certification result is bound to the exact SHA tested and does not transfer to later commits, even when those commits are documentation-only.

Before external certification, the remaining program is Stage 7 external execution and target verification. Repository implementation and CI/release verification remain distinct from external production certification. No repository state alone establishes live deployment, provider operation, measured production SLO attainment, customer acceptance, commercial go-live, or independent certification.

## Ordered remaining work

| Priority | Work package | Class | Status |
|---|---|---|---|
| P0 | Immutable release & release identity | Mixed | Candidate `v1.4.0-rc.4` certified at exact SHA; final release freeze pending |
| P0 | External production deployment | External | Pending real target |
| P0 | Real backup/restore & DR with RPO/RTO | External | Pending real target |
| P0 | Production SLO/SLI & error budget | Mixed | Engineering contract complete; target measurements pending |
| P0 | Live provider validation | External | Pending real providers |
| P0 | Vendor → Reseller → Client runtime isolation/RBAC (#19) | External | Engineering CI gate complete; external actor evidence pending |
| P0 | DAST | Mixed | CI baseline scan complete; deployed authenticated scan pending |
| P0 | Independent penetration test/security review | External | Pending independent evidence |
| P0 | Production networking hardening | Mixed | Engineering contract complete; target perimeter evidence pending |
| P0 | Secret management/rotation/recovery | Mixed | Engineering contract complete; target lifecycle evidence pending |
| P0 | HA/failure-recovery rehearsal | Mixed | Engineering rehearsal complete; target rehearsal pending |
| P0 | Incident-response drill | Mixed | Engineering simulation complete; live operational drill pending |
| P0 | Alert ownership/on-call escalation | Mixed | Engineering routing contract complete; live paging/on-call evidence pending |
| P0 | Final external certification & customer acceptance (#210/#269) | External | Final gate; blocked by missing P0 evidence |
| P1 | Data retention & lifecycle enforcement | Mixed | Engineering implemented; target verification remains external |
| P1 | Human-in-the-loop TODO reconciliation | Engineering | Engineering complete |
| P1 | Documentation consolidation/evidence index | Engineering | Reconciled 2026-09-12 |
| P1 | Platform operations dashboard | Engineering | Engineering complete via `/admin/operations` |
| P1 | Customer usage/budget/cost controls | Mixed | Engineering implemented; target billing/operations validation remains external |
| P1 | Cost anomaly detection/forecasting | Engineering | Engineering implemented |

Canonical detailed register: `docs/current/PRODUCTION_GAP_REGISTER_2026-09-04.md`.

## Latest certification evidence

Production Certification Run `34693535048` passed for exact SHA `4cadd2df003d72de43546466a47e2c66062002c6`, release identity `v1.4.0-rc.4`. The certification covered the exact-SHA identity, backend/frontend validation, migrations, production-like infrastructure/readiness, OCR runtime/extraction, product gates with zero failures, and Playwright E2E.

Additional post-merge engineering evidence on the certified mainline included successful SLO Contract Manual v2 (`34693267741`), Delivery Manifest Bundle (`34693267680`) and Production Compose Validation (`34693267659`).

These are engineering/release evidence only. They do not establish external production deployment or customer acceptance.

## Production infrastructure validation evidence

PR #315 merged to `main` at `93c717969a192ae5b90b909c2c4e8aaa89bea50a`. Validation run `33884955068` passed on GitHub-hosted Linux infrastructure. The run validated the production Compose contract, built the API/Worker/Beat/Frontend images, started PostgreSQL/Redis/storage, waited for dependency readiness, applied Alembic migrations, started API/Worker/Beat/Frontend, verified PostgreSQL and Redis persistence across restart, verified API dependency readiness and Frontend HTTP reachability, and executed a real PostgreSQL custom-format `pg_dump` plus isolated `pg_restore`. The ephemeral environment was torn down after the run.

This evidence demonstrates repository production-like lifecycle/recovery behavior. It does **not** establish real production deployment, provider behavior, measured production SLO/error budget, durable target backup cadence, target-environment RPO/RTO, external rollback rehearsal, security/compliance certification or customer acceptance.

## Stage 7 acceptance rule

All required external records must be attached to **one exact immutable release identity**: release SHA/tag and checksums, real-target deployment, live provider validation, measured production SLO/error budget, target backup/restore and RPO/RTO, applicable independent security/compliance evidence, ordered Vendor → Reseller → Client acceptance, rollback/failure-recovery evidence, and final exceptions/residual-risk disposition.

Local/CI evidence, synthetic load, simulated providers, local RBAC acceptance and repository security scans are supporting engineering evidence only.

## Security rule

No production host, private key, registry credential, webhook secret, payment secret, customer data or environment-specific access token belongs in Git history. Missing required production inputs must fail closed.
