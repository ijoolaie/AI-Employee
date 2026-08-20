# Release Audit — v1.0.1 / productization baseline

## Audit scope

This audit records the transition from the certified RC8/RC9 release line into the published `v1.0.1` baseline and the subsequent productization work. It must not be interpreted as a request to restart completed RC8/RC9 certification.

## Published release

- **Published version:** `v1.0.1`
- **Published release commit:** `2d23a01098f432145ecaea14b2500fe520ad0bf7`
- **Current `main`:** contains post-release CI/release-topology changes and is intentionally distinct from the published release until the next release is cut.

The release line has completed implementation, certification, product acceptance, production hardening, deployment readiness, and release evidence gates. Later work must be evaluated by affected behavior rather than by blindly rerunning every historical gate.

## Certification and deployment evidence

| Test / check | Result |
|---|---|
| Architecture Guard | **PASS** |
| Production Compose Validation | **PASS** |
| Production Certification | **PASS** |
| Product Acceptance | **PASS** |
| Production Hardening | **PASS** |
| PostgreSQL backup/restore smoke | **PASS** |
| Redis persistence/restore smoke | **PASS** |
| Disaster Recovery | **PASS** |
| Production Observability contract | **PASS** |
| Failure detection / rollback contract | **PASS** |
| Notification delivery contract | **PASS** |
| Deployment Readiness | **PASS** |
| Local production Compose validation | **PASS** |
| Local production API/frontend/worker/beat/PostgreSQL/Redis readiness | **PASS** |
| Controlled local API failure detection and recovery | **PASS** |

## Release integrity rule

The repository must distinguish three states:

1. **Published release** — an immutable Git tag and exact commit.
2. **Current main** — ongoing development after the published release.
3. **Certified delivery baseline** — the exact revision for which required evidence was recorded.

A later `main` commit is not automatically part of a published release.

## Productization direction

The next work is commercial productization rather than re-certification of completed gates. The authoritative roadmap is `docs/current/PRODUCTIZATION_ROADMAP.md` and separates:

- Vendor Edition
- Reseller Edition
- Customer Edition
- Repeatable Delivery Package
- Commercial Production

Each downstream edition must remain isolated from the control plane of the edition above it.

## Remaining release/productization gates

1. Keep release documentation synchronized with the published tag and current `main` delta.
2. Establish the next immutable release baseline after the post-v1.0.1 CI/release-topology work is green.
3. Implement and test vendor/reseller/customer edition boundaries.
4. Build a reproducible delivery package with manifest, checksums, installation, migration, backup/restore, rollback, and acceptance procedures.
5. Define supported upgrade and compatibility paths.
6. Where an actual external production target exists, record live deployment, external alert delivery, and live rollback evidence separately from local Docker evidence.

## Important environment distinction

Local production-like deployment and rollback evidence proves repository deployment/recovery behavior. It does not fabricate evidence for an external production host, registry, alert provider, or live customer environment.
