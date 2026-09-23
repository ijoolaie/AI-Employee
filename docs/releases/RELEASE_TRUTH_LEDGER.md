# Release Truth Ledger

**Last reconciled:** 2026-09-23
**Authority:** Git metadata + GitHub release records + explicit certification and deployment evidence

## Semantics

- **TAGGED** — Git tag exists and resolves to the recorded object.
- **BUILT** — build/CI evidence exists for the exact release commit or artifact.
- **CERTIFIED** — explicit certification evidence exists for the exact release commit.
- **DEPLOYED** — verified deployment evidence exists for the exact release identity.
- **EXTERNALLY_ACCEPTED** — independent Vendor/Reseller/Customer acceptance evidence exists.

These states are independent and must not be inferred from release names. `OPEN / PENDING EXTERNAL EXECUTION` is a deliberate project-stage state, not a failure.

## Current release identities

| Release | Commit | Tag | Certification | Deployment | External acceptance |
|---|---|---|---|---|---|
| `v1.4.10` | `b09f3e35d512e3c4d21be9d930539cbbe1d2d451` | **VERIFIED** | **CERTIFIED** — Run `35840044046` / Job `107112696112` | **OPEN — PENDING EXTERNAL EXECUTION** | **OPEN — PENDING EXTERNAL EXECUTION** |
| `v1.4.9` | `f1ce20c010779f5273eb5d0051da24cdd57b33f6` | VERIFIED | **CERTIFIED** — Run `35575615877` / Job `106256713583` | **NOT VERIFIED** | Pending |
| `v1.4.8` | `4f7c4676850b546a1c6bdf219ab9401202302e2d` | VERIFIED | **CERTIFIED** — Run `35568392010` / Job `106234691683` | **NOT VERIFIED** | Pending |
| `v1.4.7` | `48a6df0ea8a2fb0624e831fbdea55ee4548807f6` | VERIFIED | **CERTIFIED** — Run `35498984521` / Job `106047204166` | **NOT VERIFIED** | Pending |
| `v1.4.6` | `f3d60031332450ba616e2a1c705e85c0c2c5aefd` | VERIFIED | **CERTIFIED** | **NOT VERIFIED** | Pending |
| `v1.4.5` | `cc94bc9536f4f95680bb7a183313914c116ffcf2` | VERIFIED | **FAILED PRODUCT CERTIFICATION** — historical immutable release | **NOT VERIFIED** | Not accepted |

## v1.4.10 promotion checkpoint

`v1.4.10` passed fresh exact-SHA Production Certification on 2026-09-23 and has now been promoted as the stable release.

- certified/checked-out SHA: `b09f3e35d512e3c4d21be9d930539cbbe1d2d451`;
- workflow run: `35840044046`;
- certification job: `107112696112`;
- Product Gate failures: **0**;
- frontend Playwright: **8/8 PASS**;
- evidence JSON SHA-256: `73b193ae14d886a8bda83e65a1486cff7d8bedeb04ec32d78f469dcf8037501b`;
- artifact ID: `10740739447`;
- stable Git tag: **VERIFIED** and resolves to the certified SHA;
- GitHub Release: **PUBLISHED** for `v1.4.10`;
- production deployment claimed by certification: **false**.

No source changes were made to the certified release commit after certification. Post-release documentation work is on top of the release boundary.

## External production boundary

The following remain intentionally open because the current project stage is local/engineering execution. They are independent of repository Production Certification:

- real production target and deployed-identity verification;
- live provider/payment/integration validation;
- measured production SLO/SLI and error budget;
- real backup/restore/DR with measured RPO/RTO;
- external Vendor → Reseller → Customer runtime isolation/RBAC;
- deployed-target authenticated DAST;
- independent penetration/security review;
- production networking/TLS and secret-management lifecycle evidence;
- HA/failure recovery and incident-response rehearsal;
- staffed alert ownership/on-call evidence;
- final Vendor → Reseller → Customer acceptance;
- residual-risk disposition and commercial go-live authorization.

These are not release-certification claims. They are future external gates, not current engineering failures.

## Current execution-stage rule

Until an external target is provisioned, deployment and external acceptance remain `OPEN — PENDING EXTERNAL EXECUTION`. When the project moves to external/commercial operation, these gates become mandatory and must be evidenced against the exact immutable release identity.

## Historical integrity rule

Do not retag, rewrite or reinterpret historical certified/failed releases. `v1.4.9` remains immutable at its certified SHA.
