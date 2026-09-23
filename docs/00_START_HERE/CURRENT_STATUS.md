# Current Status

**Last reconciled:** 2026-09-23
**Latest certified release:** `v1.4.10`
**Certified release SHA:** `b09f3e35d512e3c4d21be9d930539cbbe1d2d451`
**Stable Git tag:** `v1.4.10` — VERIFIED at the certified SHA
**GitHub Release:** `v1.4.10` — PUBLISHED
**Exact-SHA Production Certification:** Run `35840044046` — PASS
**Certification job:** `107112696112` — PASS
**Current status:** v1.4.10 RELEASE-CERTIFIED / EXTERNAL PRODUCTION & COMMERCIAL ACCEPTANCE PENDING

## Current release

- Release: `v1.4.10`
- Exact certified SHA: `b09f3e35d512e3c4d21be9d930539cbbe1d2d451`
- Production Certification: PASS
- Product Gate failures: **0**
- Frontend Playwright: **8/8 PASS**
- Evidence artifact: `production-certification-evidence-v1.4.10-b09f3e35d512e3c4d21be9d930539cbbe1d2d451`
- Evidence JSON SHA-256: `73b193ae14d886a8bda83e65a1486cff7d8bedeb04ec32d78f469dcf8037501b`
- Artifact ID: `10740739447`
- Production deployment claimed by certification: **false**
- Stable Git tag: **VERIFIED**
- GitHub Release: **PUBLISHED**
- External/customer acceptance: **PENDING**

Certification applies only to the exact certified SHA. Post-release documentation commits do not inherit certification.

## Executive truth

The latest repository-certified release is **v1.4.10 / `b09f3e35...`**. The `v1.4.9` certification remains immutable at `f1ce20c010779f5273eb5d0051da24cdd57b33f6`.

Repository engineering, CI, production-like validation, product completeness work and fresh exact-SHA Production Certification are complete for the v1.4.10 tracked scope.

No evidence currently establishes real production deployment, live-provider operation, measured production SLO/DR, independent security review, staffed production operations or customer acceptance.

## Post-v1.4.10 production-readiness audit

| Area | Status | Evidence boundary |
|---|---|---|
| Immutable release identity | PASS | Tag `v1.4.10` resolves to certified SHA; GitHub Release published |
| Repository production-like certification | PASS | Exact-SHA certification run 35840044046, Product Gates 0, Playwright 8/8 |
| Production Compose topology | PASS | `docker-compose.production.yml` defines PostgreSQL, Redis, API, worker, Beat and frontend with health/restart controls |
| Migration gate | PASS | Certification workflow runs `alembic upgrade head`, `alembic check`, and single-head validation |
| Backup/restore engineering path | PASS | Backup/restore scripts and local recovery evidence exist |
| Rollback engineering contract | PASS | Controlled rollback/recovery scripts and runbook exist |
| Observability/SLO engineering contract | PASS | Prometheus/SLO/error-budget engineering contract and alert-routing contract exist |
| Real production deployment | NOT VERIFIED | No target-specific deployment evidence is present |
| Deployed image/digest identity | NOT VERIFIED | External registry/deployed digest evidence is pending |
| TLS/DNS/firewall/ingress on target | NOT VERIFIED | Repository Compose intentionally delegates public ingress to the target layer |
| Secret-manager lifecycle/rotation on target | NOT VERIFIED | Repository contract exists; real manager and rotation evidence is absent |
| Live provider/payment integration | NOT VERIFIED | Provider preflight exists; live target validation is pending |
| Production SLO/SLI/error budget | NOT VERIFIED | Engineering targets exist; real traffic measurement is pending |
| Real backup/restore and measured RPO/RTO | NOT VERIFIED | Local/engineering rehearsal exists; target measurement is pending |
| Vendor → Reseller → Customer target isolation/RBAC | NOT VERIFIED | Real-stack engineering gates exist; deployed actor-matrix evidence is pending |
| Authenticated DAST on deployed target | NOT VERIFIED | CI/security contracts exist; running-target DAST is pending |
| Independent penetration/security review | NOT VERIFIED | No independent assessment evidence in repository |
| HA/failure recovery on target | NOT VERIFIED | Engineering rollback/recovery contract exists; target drill is pending |
| Incident response/on-call | NOT VERIFIED | Operational contract exists; staffed target evidence is pending |
| Vendor/Reseller/Customer acceptance | NOT VERIFIED | External acceptance records are pending |
| Commercial go-live | NOT VERIFIED | Depends on all external P0 evidence and residual-risk disposition |

## Security rule

No production host, private key, registry credential, webhook secret, payment secret, customer data or environment-specific access token belongs in Git history, GitHub issues, documentation or chat. Missing required production inputs must fail closed.
