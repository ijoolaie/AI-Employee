# Release Truth Ledger

**Last reconciled:** 2026-09-21
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
| `v1.4.9` | `f1ce20c010779f5273eb5d0051da24cdd57b33f6` | VERIFIED | **CERTIFIED** — Run `35575615877` / Job `106256713583` | **NOT VERIFIED** | Pending |
| `v1.4.8` | `4f7c4676850b546a1c6bdf219ab9401202302e2d` | VERIFIED | **CERTIFIED** — Run `35568392010` / Job `106234691683` | **NOT VERIFIED** | Pending |
| `v1.4.7` | `48a6df0ea8a2fb0624e831fbdea55ee4548807f6` | VERIFIED | **CERTIFIED** — Run `35498984521` / Job `106047204166` | **NOT VERIFIED** | Pending |
| `v1.4.6` | `f3d60031332450ba616e2a1c705e85c0c2c5aefd` | VERIFIED | **CERTIFIED** | **NOT VERIFIED** | Pending |
| `v1.4.5` | `cc94bc9536f4f95680bb7a183313914c116ffcf2` | VERIFIED | **FAILED PRODUCT CERTIFICATION** — historical immutable release | **NOT VERIFIED** | Not accepted |

## v1.4.7 checkpoint

v1.4.7 passed exact-SHA Production Certification:

- target/checked-out SHA: `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`;
- Product Gate failures: 0;
- frontend Playwright: 6/6 PASS;
- immutable evidence artifact: `production-certification-evidence-v1.4.7-48a6df0ea8a2fb0624e831fbdea55ee4548807f6`;
- artifact digest: `sha256:86c82af5326bce9d6be634df8779bf0a0f28ca16503ee34095786858780e1427`;
- release assets include runtime and four edition packages plus manifest/checksums.

Production deployment was explicitly **not claimed** by the certification manifest.

## Historical candidate boundary

Earlier v1.4.5 RC1, v1.4.5 engineering baseline and v1.4.6 certification records remain useful historical evidence. They must not be presented as the current release checkpoint, and no certification is transferred from those SHAs to v1.4.7.

## External production boundary

The following remain open:

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

These are tracked by #210, #269 and #19.

## Current interpretation

- Current published release: **v1.4.9 / `f1ce20c...` — certified, not externally deployed.**
- Current `main`: **`f1ce20c010779f5273eb5d0051da24cdd57b33f6`**, same as the certified v1.4.9 tag.
- Production deployment: **PENDING REAL INFRASTRUCTURE**.
- Customer acceptance: **PENDING**.
- Live provider validation: **PENDING**.
- Commercial go-live: **PENDING external gates**.

Do not retag, rewrite or reinterpret historical certified/failed releases.