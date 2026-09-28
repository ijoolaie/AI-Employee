# Current Status

**Last reconciled:** 2026-09-28
**Latest certified release:** `v1.4.11`
**Certified release SHA:** `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`
**Stable Git tag:** `v1.4.11` — VERIFIED at the certified SHA
**GitHub Release:** `v1.4.11` — PUBLISHED
**Exact-SHA Production Certification:** Run `35848311037` — PASS
**Certification job:** `107139710452` — PASS
**Current engineering head:** `main / 783ab44fbd4e6922878114e1f599021b3e397fe7`
**Current status:** v1.4.11 RELEASE-CERTIFIED / LOCAL-ENGINEERING STAGE / EXTERNAL GATES OPEN

## Current release

- Release: `v1.4.11`
- Exact certified SHA: `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`
- Production Certification: PASS
- Product Gate failures: **0**
- Frontend Playwright: PASS
- Evidence artifact: `production-certification-evidence-v1.4.11-rc.1-90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`
- Evidence JSON SHA-256: `bfd75a37126bc3fcb98080d9f4a9522ae1d0c05ab05ca686f0be985f53334048`
- Artifact ID: `10744805746`
- Production deployment claimed by certification: **false**
- Stable Git tag: **VERIFIED**
- GitHub Release: **PUBLISHED**
- Current execution stage: **LOCAL / ENGINEERING**
- Current main head: **main / 783ab44fbd4e6922878114e1f599021b3e397fe7**
- External production & commercial gates: **OPEN — PENDING EXTERNAL EXECUTION**

Certification applies only to the exact certified SHA. Post-release code or documentation commits do not inherit certification.

## Executive truth

The latest repository-certified release is **v1.4.11 / `90dd5cb...`**.

The latest code-bearing engineering head is `e844d55e5053e9689f5afdca8aa6a4d4e75a2662`, containing the merged CI timeout process-termination fix from PR #826 and the governed Workforce runtime-binding fix from PR #827. The current main head `783ab44fbd4e6922878114e1f599021b3e397fe7` adds the documentation-only reconciliation from PR #828. Neither post-certification head is certified by the v1.4.11 exact-SHA evidence.

Repository engineering, CI, production-like validation, product completeness work and fresh exact-SHA Production Certification are complete for the v1.4.11 tracked scope.

The project is currently being executed on the developer/local environment. No external production target is being used at this stage. Therefore gates that require a real target, live providers, staffed operations or external acceptance are intentionally **OPEN — PENDING EXTERNAL EXECUTION**. They are not current engineering failures and do not block local development or repository-level certification.

## Post-v1.4.11 production-readiness audit

| Area | Status | Evidence boundary |
|---|---|---|
| Immutable release identity | PASS | Tag `v1.4.11` resolves to certified SHA; GitHub Release published |
| Repository production-like certification | PASS | Exact-SHA certification run 35848311037, Product Gates 0, Playwright PASS |
| Production Compose topology | PASS | `docker-compose.production.yml` defines PostgreSQL, Redis, API, worker, Beat and frontend with health/restart controls |
| Migration gate | PASS | Certification workflow runs `alembic upgrade head`, `alembic check`, and single-head validation |
| Backup/restore engineering path | PASS | Backup/restore scripts and local recovery evidence exist |
| Rollback engineering contract | PASS | Controlled rollback/recovery scripts and runbook exist |
| Observability/SLO engineering contract | PASS | Prometheus/SLO/error-budget engineering contract and alert-routing contract exist |
| Real production deployment | OPEN — PENDING EXTERNAL EXECUTION | No external target is currently in use; this gate is intentionally open |
| Deployed image/digest identity | OPEN — PENDING EXTERNAL EXECUTION | Requires an external registry and deployed target |
| TLS/DNS/firewall/ingress on target | OPEN — PENDING EXTERNAL EXECUTION | Target-layer responsibility; external target does not yet exist |
| Secret-manager lifecycle/rotation on target | OPEN — PENDING EXTERNAL EXECUTION | Requires external secret manager and target lifecycle |
| Live provider/payment integration | OPEN — PENDING EXTERNAL EXECUTION | Requires live provider credentials/target validation |
| Production SLO/SLI/error budget | OPEN — PENDING EXTERNAL EXECUTION | Requires real production traffic and monitoring |
| Real backup/restore and measured RPO/RTO | OPEN — PENDING EXTERNAL EXECUTION | Local rehearsal exists; target measurement awaits external deployment |
| Vendor → Reseller → Customer target isolation/RBAC | OPEN — PENDING EXTERNAL EXECUTION | Requires deployed target actor-matrix execution |
| Authenticated DAST on deployed target | OPEN — PENDING EXTERNAL EXECUTION | Requires a running external target |
| Independent penetration/security review | OPEN — PENDING EXTERNAL EXECUTION | Intentionally deferred to external/security-review phase |
| HA/failure recovery on target | OPEN — PENDING EXTERNAL EXECUTION | Engineering contract exists; target drill awaits external deployment |
| Incident response/on-call | OPEN — PENDING EXTERNAL EXECUTION | Requires staffed external operations |
| Vendor/Reseller/Customer acceptance | OPEN — PENDING EXTERNAL EXECUTION | Acceptance occurs only after external target execution |
| Commercial go-live | OPEN — FUTURE EXTERNAL GATE | Becomes mandatory when moving from local execution to external/commercial operation |

## Current-main post-certification engineering revalidation

Current-main validation is **engineering evidence only** and does not transfer the v1.4.11 exact-SHA certification.

The post-certification dependency update PR #809 is merged at `c9c3cf...`. PR #826 is merged at `d32845d...` for the CI timeout process-termination fix. PR #827 is merged at `e844d55...` for the governed Workforce runtime-binding fix. PR #828 is merged at `783ab44...` and is documentation-only. The PR #827 head passed its listed engineering/security gates; no claim is made here that the post-certification main head is release-certified.

The current-main evidence boundary remains:

`CURRENT MAIN ENGINEERING EVIDENCE` ≠ `V1.4.11 RELEASE CERTIFICATION` ≠ `EXTERNAL PRODUCTION EVIDENCE`.

## External-gate status rule

`OPEN — PENDING EXTERNAL EXECUTION` means the gate is intentionally unexecuted because the current project stage is local/engineering execution. It is neither PASS nor FAIL. Once an external target is provisioned, these gates become mandatory and must be evidenced before external/commercial go-live.

## Documentation authority rule

For current status, use this precedence:

1. `CURRENT_STATUS.md`
2. `CURRENT_PRIORITIES.md`
3. current roadmap/execution packs
4. dated historical audit documents
5. architecture/blueprint documents for architecture truth only

A blueprint, historical document or plan must not override current release/evidence truth.

## Security rule

No production host, private key, registry credential, webhook secret, payment secret, customer data or environment-specific access token belongs in Git history, GitHub issues, documentation or chat. Missing required production inputs must fail closed.
