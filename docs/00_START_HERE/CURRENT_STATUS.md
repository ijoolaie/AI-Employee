# Current Status

**Last reconciled:** 2026-09-02  
**Status:** v1.3.2 INTERNAL RELEASE EVIDENCE COMPLETE / LOCAL PRODUCT ACCEPTANCE GATES COMPLETE / LOCAL DELIVERY EVIDENCE COMPLETE / EXTERNAL PRODUCTION PENDING

## Where we are

| Dimension | Current truth |
|---|---|
| Current candidate release | `v1.3.2` prerelease |
| Candidate branch | `release/v1.3.2-phase6e-candidate` |
| Candidate SHA | `728b7f447d3bc6376fb01d47730cdd70eaf07746` |
| Phase 6E self-hosted rehearsal | **PASS** — Run `33482911674` |
| Production Certification | **PASS** — Run `33484435738` |
| Release packaging | **PASS** — Run `33486097337` |
| Migration head | `p8_03_agent_binding` |
| Release assets | Present on `v1.3.2` |
| Local Product Acceptance gates | **COMPLETE** — recorded 2026-09-02 |
| Local runtime hardening | **COMPLETE** — Redis/Beat recovery and API security-header smoke evidence recorded 2026-09-02 |
| Local DR / restore verification | **COMPLETE** — PostgreSQL custom-format backup and isolated restore verified 2026-09-02 |
| Migration graph audit | **COMPLETE** — single head and upgrade/downgrade coverage verified |
| Local rollback strategy | **DOCUMENTED** — Git/Compose rebuild and health/smoke verification path |
| Final local evidence | **COMPLETE** — evidence manifest recorded 2026-09-02 |
| External production target | **NOT CONFIGURED / NOT AVAILABLE** |
| Vendor acceptance | **NOT STARTED / NOT REQUIRED FOR CURRENT LOCAL SCOPE** |
| Reseller acceptance | **NOT STARTED / NOT REQUIRED FOR CURRENT LOCAL SCOPE** |
| Customer-environment acceptance | **NOT STARTED / NOT REQUIRED FOR CURRENT LOCAL SCOPE** |
| Architecture baseline | V1.4 (frozen) |
| Current architecture extension | V1.5 Agentic Operating Model |
| Phase 11 | **COMPLETE** — prior certification `33369071987`, Failed gates: 0; Issue #170 closed |
| Next execution frontier | Phase 12 Test Center & Evidence Platform, with ongoing workspace/execution hardening and external-production evidence remaining separate |

## Canonical v1.3.2 identity

- Tag: `v1.3.2`
- Exact commit: `728b7f447d3bc6376fb01d47730cdd70eaf07746`
- Candidate branch: `release/v1.3.2-phase6e-candidate`
- Migration: `p8_03_agent_binding`

The tag is bound to the exact candidate SHA. Certification applies only to that exact tested identity.

## v1.3.2 evidence

### Phase 6E self-hosted rehearsal

Run `33482911674` passed on `728b7f447...`. Health, migration, backup/restore, controlled recovery and evidence upload passed. Monitoring was not configured in the rehearsal and security evidence was rehearsal-only.

### Production Certification

Run `33484435738` passed on the exact candidate SHA. This is internal engineering/certification evidence, not external production acceptance.

### Release packaging

Run `33486097337` passed on the exact candidate SHA and produced the canonical v1.3.2 runtime and edition artifacts.

- Runtime SHA-256: `bdcfe2aabaa2e94d038b57ee2629083eef48bc566257319cd552df8ce1593324`
- Editions SHA-256: `fb41dfe569610d129f36caff0df3e9e330607c86e731ba78f0cc862d3017833c`

The corresponding assets are attached to the `v1.3.2` GitHub prerelease.

## Local Product Acceptance — 2026-09-02

The following local real-stack gates passed successfully and are recorded in `docs/current/51_LOCAL_FINAL_ACCEPTANCE_RECONCILIATION_2026-09-02.md`:

1. Tenant Isolation + RBAC + Knowledge P0 — PASS twice; each run cleaned its two certification tenants.
2. Conversation Tenant Isolation P0 — PASS.
3. Employee → Run → AI → Result — PASS.
4. Files → Knowledge → Memory — PASS.
5. Admin / Developer API Keys — PASS.
6. Workflow + Approval + Schedule — PASS, including approval creation/approval/resume and schedule lifecycle.

These completed gates must not be rerun merely to reproduce status. They should be rerun only for regression, relevant code/configuration change, a new release/candidate SHA, material environment change, or explicit evidence invalidation.

## Operational incidents resolved during acceptance

### Tenant fixture pollution

The local Tenant/RBAC certification initially accumulated `security-a-*` / `security-b-*` fixtures. The cleanup helper naming compatibility was corrected in merged PR #212, and local cleanup was verified with `remaining_security_tenants = 0`. The certification was then run twice successfully with cleanup on each run.

### Docker Compose Beat/Redis network mismatch

Workflow certification initially failed because Beat could not resolve `redis`. Runtime inspection showed Beat on `ai-employee_backend` while Redis/Worker/API/Postgres were on `ai-employee_default`. The local Compose stack was reconciled without deleting volumes. Workflow certification subsequently passed completely.

This was a local Docker network-state incident, not an application Workflow defect. If it recurs, inspect network membership/DNS before changing application code or database state.

## Local delivery evidence — 2026-09-02

- Docker / Compose runtime: PASS.
- Redis DNS connectivity from API, Worker and Beat: PASS.
- Redis PING: PASS.
- Celery Beat scheduling: PASS.
- API security-header smoke test: PASS.
- PostgreSQL custom-format backup: PASS.
- Isolated PostgreSQL restore: PASS; 53 tables restored and migration `p8_03_agent_binding` present.
- Migration graph: single head `p8_03_agent_binding`; migration upgrade/downgrade functions audited.
- Backup is excluded from Git under `artifacts/dr/`.
- Application rollback strategy is documented as known-good Git commit → rebuild application images → production Compose deployment → dependency/service health verification → application smoke verification.
- Immutable image rollback, destructive production rollback drill, production restore drill, measured production RPO/RTO and external production deployment remain unverified.

See `docs/LOCAL_RUNTIME_HARDENING_EVIDENCE_2026-09-02.md`, `docs/PRODUCTION_READINESS_DR_ROLLBACK_EVIDENCE_2026-09-02.md`, and `docs/FINAL_LOCAL_DELIVERY_EVIDENCE_MANIFEST_2026-09-02.md` for the detailed evidence boundaries.

## Invalidated attempts

Run `33485801162` is not v1.3.2 evidence because its artifact metadata pointed to the previous `bcacbc0...` source despite the v1.3.2 package naming. Run `33485442018` is not the canonical v1.3.2 package run.

## Evidence levels

- **AS-BUILT** — implementation exists and is wired into the application.
- **VERIFIED** — relevant automated or certification verification has passed.
- **EXTERNAL-PENDING** — source/tooling exists but independent external runtime/provider/customer evidence is missing.
- **DEFERRED** — outside current scope.

## Current priorities

1. Preserve the canonical `v1.3.2` identity and do not rebuild/re-tag without a real defect.
2. Preserve the completed local Product Acceptance, runtime hardening, DR/restore and rollback evidence; rerun only on invalidation.
3. Prepare the customer delivery package and handoff documentation within the current local-delivery scope.
4. Begin Phase 12 Test Center & Evidence Platform implementation using the existing acceptance/evidence contracts.
5. Continue Platform/Reseller/Client workspace validation against real WorkItem and Agent APIs as ongoing hardening.
6. Continue compatibility migration for existing Employee-backed capabilities without breaking the unified execution model.
7. Independently collect external production evidence only when a real deployment target exists.
8. Execute Phase 6E Vendor → Reseller → Client production delivery only when the required external context and evidence exist.

## Important boundaries

- CI/internal certification is not external production certification.
- A Git tag or GitHub release does not by itself prove deployment or production acceptance.
- `v1.3.2` remains a prerelease until the applicable release/promotion decision is supported by evidence.
- Vendor, Reseller and Customer-environment acceptance cannot be claimed when no corresponding external acceptance event exists.
- Phase 12 engineering evidence does not retroactively change the canonical v1.3.2 certification identity.
- No acceptance state may be marked complete without the corresponding evidence.
