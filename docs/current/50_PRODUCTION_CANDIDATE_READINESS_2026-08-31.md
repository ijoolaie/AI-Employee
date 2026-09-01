# Production Candidate Readiness — 2026-09-01

## Decision

The previous certified engineering identity remains `bcacbc0eb03b247ad00a232e4eb6324ce5c849df`. Its certification is not transferred to any later revision.

The independently validated Phase 6E candidate is `728b7f447d3bc6376fb01d47730cdd70eaf07746`.

## Canonical v1.3.2 candidate

- Candidate branch: `release/v1.3.2-phase6e-candidate`
- Candidate source SHA: `728b7f447d3bc6376fb01d47730cdd70eaf07746`
- Release/tag: `v1.3.2`
- Tag target: exact commit `728b7f447d3bc6376fb01d47730cdd70eaf07746`
- Release state: GitHub prerelease
- Current delivery scope: **LOCAL PRODUCTION-LIKE VALIDATION → CUSTOMER DELIVERY**
- Local candidate evidence status: **INTERNAL RELEASE EVIDENCE COMPLETE; LOCAL FINAL ACCEPTANCE REMAINS**

The v1.3.2 identity is independent of the previous `v1.3.1` / `bcacbc0...` certification boundary.

## Scope boundary

The current project objective is temporary execution and complete validation on the owner's local workstation, followed by customer delivery. No external production server, external registry, Vendor, Reseller or live customer environment is currently available or required for this validation cycle.

The repository contains external-production workflows. Those workflows describe a future deployment context and must not be satisfied with fabricated hosts, credentials, registries or acceptance records.

## Independent validation evidence

### Phase 6E self-hosted rehearsal

- Workflow run: `33482911674`
- Exact revision: `728b7f447d3bc6376fb01d47730cdd70eaf07746`
- Rehearsal result: PASS
- Migration head: `p8_03_agent_binding`
- Health / migration / backup-restore / controlled recovery / evidence upload: PASS
- Monitoring: `NOT_CONFIGURED_IN_REHEARSAL`
- Security: `REHEARSAL_ONLY`
- External Vendor production acceptance: not established and not required for the current local-only cycle

### Production Certification

- Workflow run: `33484435738`
- Exact revision: `728b7f447d3bc6376fb01d47730cdd70eaf07746`
- Result: PASS

Certification applies only to the exact tested SHA.

### Release packaging

- Workflow run: `33486097337`
- Exact revision: `728b7f447d3bc6376fb01d47730cdd70eaf07746`
- Result: PASS

Canonical artifacts:

- `ai-employee-v1.3.2-runtime`
  - SHA-256: `bdcfe2aabaa2e94d038b57ee2629083eef48bc566257319cd552df8ce1593324`
- `ai-employee-v1.3.2-editions`
  - SHA-256: `fb41dfe569610d129f36caff0df3e9e330607c86e731ba78f0cc862d3017833c`

Both artifacts are from Run `33486097337` and are bound to the exact candidate SHA above. The corresponding assets are attached to the `v1.3.2` GitHub prerelease.

## Invalidated packaging attempts

The following must not be used as v1.3.2 evidence:

- Run `33485801162`: package names were `v1.3.2`, but artifact metadata identified the old `bcacbc0...` source.
- Run `33485442018`: package artifacts were named `v1.3.1` and therefore do not establish v1.3.2 release identity.

The naming/source mismatch is resolved by the canonical Run `33486097337`.

## Remaining local acceptance gates

The next gates are **local**, not external-production gates:

1. Run the repository's production hardening/security checks against the local production-like stack and exact candidate revision where applicable.
2. Run the repository's observability/monitoring contract checks locally and record the explicit boundary of what can and cannot be exercised without an external alert provider.
3. Reconfirm local backup/restore and disaster-recovery evidence for the exact candidate identity.
4. Reconfirm the controlled rollback path locally and bind the evidence to the exact candidate/known-good identities.
5. Run final local health/readiness/product smoke/E2E verification against `v1.3.2`.
6. Reconcile local deployment revision, migration head, artifact identities and checksums into one evidence manifest.
7. If all local acceptance gates pass, prepare the customer delivery package and handoff documentation.

## Future external-production gates

These are intentionally **not blockers for the current local delivery cycle**:

- external production target deployment
- external target observability/monitoring
- external target recovery/DR and rollback
- live payment/provider certification
- live WhatsApp outbound provider certification
- independent Vendor → Reseller → Client acceptance

If an external production deployment is later required, the existing deployment workflow requires `PRODUCTION_DEPLOY_HOST`, `PRODUCTION_DEPLOY_USER`, `PRODUCTION_DEPLOY_SSH_KEY`, and `PRODUCTION_CONTAINER_REGISTRY`. Those values must come from a real environment and must never be fabricated for testing.

## Current gate

**Candidate reconciliation: RESOLVED.**

**Phase 6E self-hosted rehearsal: PASS.**

**Production Certification on candidate SHA: PASS.**

**Release packaging and checksum reconciliation: PASS.**

**v1.3.2 tag identity: VERIFIED.**

**Release assets: PRESENT.**

**Local final acceptance: IN PROGRESS.**

**External production target: NOT REQUIRED FOR CURRENT SCOPE.**

**Vendor acceptance: NOT STARTED / NOT REQUIRED FOR CURRENT SCOPE.**

Do not claim external production, Vendor, Reseller or Client acceptance until the corresponding independent environment and evidence actually exist.
