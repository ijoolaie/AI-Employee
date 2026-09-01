# Production Candidate Readiness — 2026-09-01

## Decision

The previous certified engineering identity remains `bcacbc0eb03b247ad00a232e4eb6324ce5c849df`. Its certification is not transferred to any later revision.

The independently validated Phase 6E candidate is now `728b7f447d3bc6376fb01d47730cdd70eaf07746`.

## Canonical v1.3.2 candidate

- Candidate branch: `release/v1.3.2-phase6e-candidate`
- Candidate source SHA: `728b7f447d3bc6376fb01d47730cdd70eaf07746`
- Release/tag: `v1.3.2`
- Tag target: exact commit `728b7f447d3bc6376fb01d47730cdd70eaf07746`
- Release state: GitHub prerelease
- Candidate status: **INTERNAL RELEASE EVIDENCE COMPLETE; EXTERNAL PRODUCTION PENDING**

The v1.3.2 identity is independent of the previous `v1.3.1` / `bcacbc0...` certification boundary.

## Independent validation evidence

### Phase 6E self-hosted rehearsal

- Workflow run: `33482911674`
- Exact revision: `728b7f447d3bc6376fb01d47730cdd70eaf07746`
- Rehearsal result: PASS
- Migration head: `p8_03_agent_binding`
- Health / migration / backup-restore / controlled recovery / evidence upload: PASS
- Monitoring: not configured in rehearsal
- Security: rehearsal-only
- External Vendor production acceptance: not established

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

## Remaining external-production gates

The repository contains workflows for production hardening, observability, recovery/DR, rollback and target deployment, but the existence of those workflows is not itself production-target evidence.

Remaining gates are:

1. production hardening on the actual target environment
2. target observability/monitoring evidence
3. target backup/restore and disaster-recovery evidence
4. controlled rollback evidence on the target
5. deployment of the exact `728b7f44...` revision to a real production target
6. target health/product smoke verification
7. final reconciliation of deployment, migration, artifact and checksum identities
8. external Vendor acceptance, followed by Reseller and Client acceptance

The production target workflow explicitly requires `PRODUCTION_DEPLOY_HOST`, `PRODUCTION_DEPLOY_USER`, `PRODUCTION_DEPLOY_SSH_KEY`, and `PRODUCTION_CONTAINER_REGISTRY`. Until an actual target is configured, target deployment and target-specific evidence cannot honestly be marked complete.

## Current gate

**Candidate reconciliation: RESOLVED.**

**Phase 6E self-hosted rehearsal: PASS.**

**Production Certification on candidate SHA: PASS.**

**Release packaging and checksum reconciliation: PASS.**

**v1.3.2 tag identity: VERIFIED.**

**Release assets: PRESENT.**

**External production target evidence: PENDING.**

**Vendor acceptance: NOT STARTED / NOT AVAILABLE.**

Do not claim Vendor, Reseller or Client production acceptance until independent external evidence exists for this exact release identity.
