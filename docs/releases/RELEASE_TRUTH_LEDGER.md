# Release Truth Ledger

**Last reconciled:** 2026-09-16
**Authority:** Git metadata + GitHub release records + explicit certification and deployment evidence

## Semantics

- **TAGGED** — Git tag exists and resolves to the recorded object.
- **BUILT** — build/CI evidence exists for the exact release commit or artifact.
- **CERTIFIED** — explicit certification evidence exists for the exact release commit.
- **DEPLOYED** — verified deployment evidence exists for the exact release identity.
- **EXTERNALLY_ACCEPTED** — independent Vendor/Reseller/Client acceptance evidence exists.

These states are independent and must not be inferred from release names.

## Current release identities

| Release / candidate | Commit | Tag | Certification | Deployment | External acceptance |
|---|---|---|---|---|---|
| `v1.4.2` | `dba0bb672deb1236b6724bb8851526e656f47967` | VERIFIED | **CERTIFIED** — Run `35108008066` / Job `104834133092` | **NOT VERIFIED / no evidence** | Pending |
| `v1.4.1` | `f7f5062feb125c7ca50263f74a0e40bc4abfa591` | VERIFIED | **CERTIFIED** — Run `34696339261` | **NOT VERIFIED / no evidence** | Pending |
| `v1.4.0-rc.4` | `4cadd2df003d72de43546466a47e2c66062002c6` | Historical candidate | **CERTIFIED** — Run `34693535048` | No evidence | Pending |
| `v1.3.8` | `fd1e74b6b4c1701f7443efc202bad161ff19618c` | VERIFIED | **CERTIFIED** — Run `34052885700` | **NOT DEPLOYED** — Run `34060615390` failed before remote deployment | Pending |
| `v1.4.0-rc.1` | `b2e2517ce0a38dc4fecd97c047328f703bdd7de6` | Historical candidate | **NOT CERTIFIED** — Run `34497132748` had 1 failed Product Gate | Not eligible | Pending |
| current `main` | post-`v1.4.2` documentation reconciliation commits | Not a release | **NOT CERTIFIED as a new release** | Not eligible | Pending |

## v1.4.2 certification checkpoint

Production Certification Run `35108008066` passed for exact SHA `dba0bb672deb1236b6724bb8851526e656f47967`, with certification job `104834133092`.

The certified gates included backend compile/Ruff, 811 backend tests, frontend contract/unit/build validation, database migration and single-head checks, OCR/Persian `fas`, backend dependency E2E, Auth P0, tenant isolation/RBAC P0, conversation isolation, Employee → Run → AI → Result, Files → Knowledge → Memory, API keys, Workflow → Approval → Schedule, Orders → Sales → Invoice → Billing, Reports/Analytics isolation, Unified WorkItem Human/Agent, frontend Playwright (6 passed), immutable evidence manifest and evidence upload. Product Gate Failures: **0**.

Evidence artifact: `production-certification-evidence-v1.4.2-dba0bb672deb1236b6724bb8851526e656f47967`, artifact ID `10450993330`.

A non-gating `CERTIFICATION FIXTURE CLEANUP FAIL: DBAPIError` was observed in the Tenant/RBAC area. The certification result remained PASS and Product Gate Failures remained 0; this note must not be interpreted as a claim that every cleanup log was clean.

## v1.4.2 release checkpoint

- Annotated Git tag: `v1.4.2`.
- Tag target commit: `dba0bb672deb1236b6724bb8851526e656f47967`.
- GitHub Release: published, not draft, not prerelease.
- Five edition packages were published: customer, reseller, runtime, self-hosted, vendor.
- `EDITION-RELEASE-MANIFEST.json` and `SHA256SUMS` were published.
- Release assets were verified; exact asset SHA256 values are part of the release evidence.

## Stage 9 release checkpoint

The v1.4.2 certified SHA includes the current planned Stage 9 slices:

1. capability-aware routing;
2. task/risk/cost-aware model selection;
3. queue-aware workload balancing;
4. persisted balancing evidence;
5. telemetry-backed Agent fitness;
6. Agent version fitness;
7. promotion evidence;
8. governed promotion;
9. governed rollback planning;
10. workforce capacity forecasting;
11. governed workforce scaling.

The optimization layer remains subordinate to the governed execution substrate. It does not directly bypass identity, policy, approval, budget, lifecycle, concurrency, audit or execution controls.

## Workflow approval certification fix

PR #530 fixed the release-certification blocker in the approved workflow path: the API no longer performs an invalid `waiting -> waiting` transition. The approved path leaves the step waiting, sets the run pending and enqueues resume; the executor owns the durable `waiting -> success` transition. Rejected steps still transition `waiting -> failed`.

PR #530 merged at the certified release SHA `dba0bb672deb1236b6724bb8851526e656f47967` after all 9 PR workflows succeeded.

## Production infrastructure baseline

Recommended initial external target is 8 vCPU / 16 GB RAM / 150–200 GB NVMe/SSD on Ubuntu 24.04 LTS, with TLS ingress, hardened firewall, encrypted off-host backups and centralized observability. See `docs/current/PRODUCTION_SERVER_BASELINE.md`.

No server provisioning is implied by this recommendation.

## External production boundary

The following remain open regardless of `v1.4.2` certification:

- real production target and deployed-identity verification;
- live provider validation;
- measured production SLO/SLI and error budget;
- real backup/restore/DR with RPO/RTO;
- external Vendor → Reseller → Client runtime isolation/RBAC;
- deployed-target DAST;
- independent penetration test/security review;
- production networking and secret-management lifecycle evidence;
- HA/failure recovery and incident-response rehearsal;
- staffed alert ownership/on-call evidence;
- final external certification and customer acceptance (#210/#269).

## Current interpretation

- Latest published and exact-SHA certified release: **v1.4.2 / `dba0bb672...`**.
- Current engineering `main`: post-release documentation reconciliation; **not certified as a new release**.
- Production deployment: **PENDING REAL INFRASTRUCTURE**.
- Customer acceptance: **PENDING**.
- Live provider validation: **PENDING**.

## Next action

Preserve the exact-SHA boundary. For external production, deploy only a frozen certified release identity and attach deployment, DR, SLO, security and acceptance evidence to that same SHA. For any future code promotion, freeze the final SHA and run fresh certification before release publication.
