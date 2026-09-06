# Release Truth Ledger

**Last reconciled:** 2026-09-06  
**Authority:** Git metadata + GitHub release records + explicit certification and deployment evidence

## Semantics

- **TAGGED** — Git tag exists and resolves to the recorded object.
- **BUILT** — build/CI evidence exists for the exact release commit or artifact.
- **CERTIFIED** — explicit certification evidence exists for the exact release commit.
- **DEPLOYED** — verified deployment evidence exists for the exact release identity.
- **EXTERNALLY_ACCEPTED** — independent Vendor/Reseller/Client acceptance evidence exists.

These states are independent and must not be inferred from release names.

## Current release identity

| Release | Commit | Tag | Certification | Deployment | External acceptance |
|---|---|---|---|---|---|
| `v1.3.8` | `fd1e74b6b4c1701f7443efc202bad161ff19618c` | VERIFIED | **CERTIFIED** — Run `34052885700` | **NOT DEPLOYED** — Run `34060615390` failed at SSH configuration before remote deployment | Pending |

## v1.3.8 reconciliation

The `v1.3.8` Git tag resolves directly to commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`.

Production certification Run `34052885700` completed successfully. The run passed backend compilation/linting/tests, migration validation, frontend contract/unit/build checks, production-like OCR runtime and extraction, backend dependency E2E, product gates and critical frontend Playwright E2E.

A controlled live deployment was then attempted in Run `34060615390` using `release_ref=v1.3.8` and explicit `DEPLOY` confirmation. The job failed in `Configure SSH` because `PRODUCTION_SSH_PRIVATE_KEY`, `PRODUCTION_HOST`, `PRODUCTION_USER` and `PRODUCTION_KNOWN_HOSTS` were empty/missing. The actual deployment step and deployed-identity verification were skipped. Therefore there is no production deployment evidence from that run and no claim of host mutation.

## Historical release context

Older release records remain historical and do not override the current v1.3.8 truth. In particular, previous claims around `v1.2.0`, `v1.2.1-final`, `v1.2.2` and `v1.3.0` must be interpreted according to their original evidence boundaries. They are not the current deployment identity.

## Current interpretation

- Latest published release candidate: **v1.3.8**.
- Current certified release candidate: **v1.3.8 / `fd1e74b6...`**.
- Production deployment: **PENDING REAL INFRASTRUCTURE**.
- Customer acceptance: **PENDING**.
- Live provider validation: **PENDING**.
- Real target DR/SLO/security/perimeter evidence: **PENDING**.

## Next audit / action

Provision and configure a real production target, populate the protected `production` Environment without exposing secret values, rerun the controlled deployment for `v1.3.8`, and reconcile the resulting deployed commit and health evidence here. Do not mark `DEPLOYED` or `EXTERNALLY_ACCEPTED` from naming, workflow creation or certification alone.
