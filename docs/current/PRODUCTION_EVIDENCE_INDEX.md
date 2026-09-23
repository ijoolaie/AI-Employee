# Production Evidence Index

**Reconciled:** 2026-09-23  
**Repository:** `ijoolaie/AI-Employee`  
**Purpose:** keep engineering evidence and external-production certification evidence traceable to an immutable release identity.

## Evidence classification

- **ENGINEERING** — repository, CI, local Docker, synthetic-load, simulated-provider, or test evidence.
- **OPEN-EXTERNAL** — an external gate intentionally left unexecuted because the current project stage is local/engineering.
- **EXTERNAL-PENDING** — evidence requiring a real deployment, real provider, real customer workflow, or independent external assessment once the external phase begins.
- **EXTERNAL** — completed evidence captured against the accepted immutable release on a real target.

No P0 external gate may be marked complete from ENGINEERING evidence alone. `OPEN-EXTERNAL` is not a failure; it records work intentionally deferred until an external target exists.

## Current release baseline

| Field | Value |
|---|---|
| Latest published release | `v1.4.11` |
| Exact certified release SHA | `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f` |
| Stable Git tag | **VERIFIED** |
| GitHub Release | **PUBLISHED** |
| Production Certification | Run `35848311037` / Job `107139710452` — PASS |
| Product Gate Failures | `0` |
| Frontend Playwright | **PASS** |
| External production deployment | **OPEN — PENDING EXTERNAL EXECUTION** |
| External image registry/deployed digest evidence | **PENDING** |
| External signed provenance/attestation | **PENDING** |

## v1.4.11 certification identity

- Release tag: `v1.4.11`
- Exact certified SHA: `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`
- Evidence artifact: `production-certification-evidence-v1.4.11-rc.1-90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`
- Evidence SHA256: `bfd75a37126bc3fcb98080d9f4a9522ae1d0c05ab05ca686f0be985f53334048`
- Artifact ID: `10744805746`
- `production_deployment_claimed=false`

## Evidence matrix

| Gate | Class | Status |
|---|---|---|
| v1.4.11 Exact-SHA Production Certification | ENGINEERING | PASS |
| Product gates / tenant isolation / RBAC | ENGINEERING | PASS |
| Frontend Playwright | ENGINEERING | PASS |
| Production-like infrastructure lifecycle | ENGINEERING | PASS |
| Backup/restore rehearsal | ENGINEERING | PASS; target RPO/RTO pending |
| SLO/error-budget engineering contract | ENGINEERING | PASS; live measurement pending |
| Provider integration preflight | ENGINEERING | PASS; live validation pending |
| Network hardening contract | ENGINEERING | PASS; deployed perimeter pending |
| Secret-management contract | ENGINEERING | PASS; external lifecycle pending |
| Failure-recovery/rollback contract | ENGINEERING | PASS; target rehearsal pending |
| Alert routing contract | ENGINEERING | PASS; live paging test pending |
| Real production deployment | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| Deployed image/digest identity | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| Real backup/restore/DR + measured RPO/RTO | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| Production SLO/SLI/error budget | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| Live provider/payment validation | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| Vendor → Reseller → Customer isolation | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| Authenticated DAST on accepted target | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| Independent penetration/security review | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| Network/TLS/secret lifecycle on target | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| HA/failure recovery + incident drill | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| Alert ownership/on-call test | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| Vendor → Reseller → Customer acceptance | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |
| Final commercial go-live authorization | OPEN-EXTERNAL | OPEN — PENDING EXTERNAL EXECUTION |

## Current execution-stage rule

The project is currently in **LOCAL / ENGINEERING EXECUTION**. External gates are intentionally open until an external deployment target, live integrations, staffed operations, or independent assessment is actually available. These open states are not defects and do not invalidate v1.4.11 repository certification.

## Release binding rule

Every completed external evidence record must identify exact release tag/SHA, deployment timestamp, target/environment, relevant artifact/image digest, operator/owner, and evidence artifact/log reference.

No evidence transfers automatically across SHAs. Documentation cannot substitute for target evidence.


## Post-v1.4.11 workforce governance evidence — 2026-09-23

Mainline post-certification engineering now includes PRs #641, #643, #644, #645, #646 and #647 covering CEO delegation, runtime-bound Manager proposal provenance, unrestricted role targeting with four first-party templates, workforce dashboard reporting and explicit workforce-role runtime enforcement. These changes are engineering evidence only and are not part of the immutable v1.4.11 certified snapshot.

Runtime role enforcement is fail-closed for missing/unknown roles and human-approval-required operations. Internal Manager operations additionally require matching governed runtime identity, durable Run identity and active CEO delegation.

SLA compliance is not claimed by the dashboard until a tenant-owned SLA target contract exists. External production evidence remains OPEN — PENDING EXTERNAL EXECUTION.
