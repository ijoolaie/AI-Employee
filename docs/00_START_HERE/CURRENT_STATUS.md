# Current Status

**Last reconciled:** 2026-09-01  
**Status:** v1.3.2 INTERNAL RELEASE EVIDENCE COMPLETE / PRODUCTION TARGET PENDING

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
| External production target | **NOT CONFIGURED / NOT AVAILABLE** |
| Vendor acceptance | **NOT STARTED** |
| Reseller acceptance | **NOT STARTED** |
| Customer acceptance | **NOT STARTED** |
| Architecture baseline | V1.4 (frozen) |
| Current architecture extension | V1.5 Agentic Operating Model |
| Phase 11 | **COMPLETE** — prior certification `33369071987`, Failed gates: 0; Issue #170 closed |
| Next execution frontier | Target-specific production hardening, deployment, recovery/DR, observability and rollback evidence |

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

## Invalidated attempts

Run `33485801162` is not v1.3.2 evidence because its artifact metadata pointed to the previous `bcacbc0...` source despite the v1.3.2 package naming. Run `33485442018` is not the canonical v1.3.2 package run.

## Evidence levels

- **AS-BUILT** — implementation exists and is wired into the application.
- **VERIFIED** — relevant automated or certification verification has passed.
- **EXTERNAL-PENDING** — source/tooling exists but independent external runtime/provider/customer evidence is missing.
- **DEFERRED** — outside current scope.

## Current priorities

1. Preserve the canonical `v1.3.2` identity and do not rebuild/re-tag without a real defect.
2. Obtain/configure a real production target and required deployment configuration.
3. Run target-specific production hardening, observability, recovery/DR and rollback evidence.
4. Deploy the exact `728b7f447...` revision and perform target smoke verification.
5. Reconcile deployment, migration and artifact/checksum evidence.
6. Only then begin Vendor → Reseller → Client acceptance.
7. Continue Test Center/evidence-platform work and compatibility migration without destabilizing the release candidate.

## Important boundaries

- CI/internal certification is not external production certification.
- A Git tag or GitHub release does not by itself prove deployment or production acceptance.
- `v1.3.2` is currently a prerelease and must remain so until the external production gates justify promotion.
- Vendor acceptance cannot be claimed when no external Vendor acceptance event exists.
- Historical documents cannot override this status file.
