# Release Truth Ledger

**Last reconciled:** 2026-09-23
**Authority:** Git metadata + GitHub release records + explicit certification and deployment evidence

## Semantics

- **TAGGED** — Git tag exists and resolves to the recorded object.
- **BUILT** — build/CI evidence exists for the exact release commit or artifact.
- **CERTIFIED** — explicit certification evidence exists for the exact release commit.
- **DEPLOYED** — verified deployment evidence exists for the exact release identity.
- **EXTERNALLY_ACCEPTED** — independent Vendor/Reseller/Customer acceptance evidence exists.

These states are independent and must not be inferred from release names.

## Current release identities

| Release | Commit | Tag | Certification | Deployment | External acceptance |
|---|---|---|---|---|---|
| `v1.4.10` | `b09f3e35d512e3c4d21be9d930539cbbe1d2d451` | **NOT CREATED** | **CERTIFIED** — Run `35840044046` / Job `107112696112` | **NOT VERIFIED** | Pending |
| `v1.4.9` | `f1ce20c010779f5273eb5d0051da24cdd57b33f6` | VERIFIED | **CERTIFIED** — Run `35575615877` / Job `106256713583` | **NOT VERIFIED** | Pending |
| `v1.4.8` | `4f7c4676850b546a1c6bdf219ab9401202302e2d` | VERIFIED | **CERTIFIED** — Run `35568392010` / Job `106234691683` | **NOT VERIFIED** | Pending |
| `v1.4.7` | `48a6df0ea8a2fb0624e831fbdea55ee4548807f6` | VERIFIED | **CERTIFIED** — Run `35498984521` / Job `106047204166` | **NOT VERIFIED** | Pending |
| `v1.4.6` | `f3d60031332450ba616e2a1c705e85c0c2c5aefd` | VERIFIED | **CERTIFIED** | **NOT VERIFIED** | Pending |
| `v1.4.5` | `cc94bc9536f4f95680bb7a183313914c116ffcf2` | VERIFIED | **FAILED PRODUCT CERTIFICATION** — historical immutable release | **NOT VERIFIED** | Not accepted |

## v1.4.10 certification checkpoint

`v1.4.10` passed fresh exact-SHA Production Certification on 2026-09-23:

- target/checked-out SHA: `b09f3e35d512e3c4d21be9d930539cbbe1d2d451`;
- workflow run: `35840044046`;
- certification job: `107112696112`;
- Product Gate failures: **0**;
- frontend Playwright: **8/8 PASS**;
- certification result: **PASS**;
- production deployment claimed by certification: **false**;
- evidence artifact: `production-certification-evidence-v1.4.10-b09f3e35d512e3c4d21be9d930539cbbe1d2d451`;
- evidence JSON SHA-256: `73b193ae14d886a8bda83e65a1486cff7d8bedeb04ec32d78f469dcf8037501b`;
- artifact ID: `10740739447`.

Certification is bound to the exact SHA and does not by itself create a Git tag, GitHub Release, production deployment or customer acceptance.

## Release promotion state

The stable `v1.4.10` certification gate is now **PASS**, but the repository does not currently have a verified `v1.4.10` Git tag or GitHub Release. The available GitHub connection in this workflow does not expose tag/release creation, so no tag or release is being fabricated or inferred from certification.

When the stable tag is created externally, it must resolve exactly to:

`b09f3e35d512e3c4d21be9d930539cbbe1d2d451`

No source changes should be made to the certified commit after tagging.

## External production boundary

The following remain open independently of repository Production Certification:

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
- final external certification and customer acceptance.

These remain the commercial go-live boundary.

## Historical integrity rule

Do not retag, rewrite or reinterpret historical certified/failed releases. `v1.4.9` remains immutable at its certified SHA.
