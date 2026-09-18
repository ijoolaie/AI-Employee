# Release Truth Ledger

**Last reconciled:** 2026-09-18
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
| `v1.4.5 RC1` | `0976537441ebc2560624022bfaabb33096f5011c` | Not published | **ENGINEERING-VALIDATED** — 10/10 current RC1 workflows PASS; local production-like certification PASS | **NOT VERIFIED** | Pending |
| `v1.4.5` engineering baseline | `a9d5cdd` | Not published | **ENGINEERING ONLY** — local production-like certification PASS on 2026-09-18 | **NOT VERIFIED** | Pending |
| `v1.4.2` | `dba0bb672deb1236b6724bb8851526e656f47967` | VERIFIED | **CERTIFIED** — Run `35108008066` / Job `104834133092` | **NOT VERIFIED / no evidence** | Pending |
| `v1.4.1` | `f7f5062feb125c7ca50263f74a0e40bc4abfa591` | VERIFIED | **CERTIFIED** — Run `34696339261` | **NOT VERIFIED / no evidence** | Pending |

## RC1 checkpoint

RC1 exact SHA `0976537441ebc2560624022bfaabb33096f5011c` passed the current engineering validation set:

- CI;
- CodeQL;
- Architecture Guard;
- Runtime Isolation/RBAC;
- HA Failure Recovery;
- Ephemeral DAST;
- Production Infrastructure;
- Security/Privacy/Compliance;
- Production Observability;
- Production Rollback & Alerting.

Result: **10/10 PASS**.

This is engineering/release-candidate evidence. It is not external production certification.

## v1.4.2 certification checkpoint

Production Certification Run `35108008066` passed for exact SHA `dba0bb672deb1236b6724bb8851526e656f47967`, with certification job `104834133092`.

## External production boundary

The following remain open regardless of RC1 engineering validation:

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

## Current interpretation

- Current RC1: **v1.4.5 / `097653...` — engineering-validated, external certification pending.**
- Latest published and exact-SHA certified release: **v1.4.2 / `dba0bb...`**.
- Production deployment: **PENDING REAL INFRASTRUCTURE**.
- Customer acceptance: **PENDING**.
- Live provider validation: **PENDING**.

## Next action

Preserve the exact-SHA boundary. If RC1 is approved as the release identity, publish/tag exactly that SHA and run any required final release certification against the same immutable identity before external deployment. Do not transfer evidence from `a9d5cdd` or `v1.4.2` onto another SHA.
