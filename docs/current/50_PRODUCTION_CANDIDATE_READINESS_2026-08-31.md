# Production Candidate Readiness — 2026-09-01

## Decision

The previously certified engineering candidate remains `bcacbc0eb03b247ad00a232e4eb6324ce5c849df` and is not being re-certified or retargeted.

The current `main` tip is `728b7f447d3bc6376fb01d47730cdd70eaf07746`, which contains the Phase 6E published-frontend-port validation fix. Git evidence shows that the post-`bcacbc0` lineage is not documentation-only; therefore the previous readiness statement that the intervening changes were documentation-only is obsolete and is superseded by this record.

## New candidate decision

A separate immutable candidate branch has been created:

- Candidate branch: `release/v1.3.2-candidate`
- Candidate source SHA: `728b7f447d3bc6376fb01d47730cdd70eaf07746`
- Candidate status: **PROPOSED — NOT CERTIFIED**
- Reason for selection: contains the validated Phase 6E published-host-port fix and is the exact revision used by self-hosted rehearsal run `33482911674`.

This does **not** transfer any certification from `bcacbc0...` to `728b7f44...`.

## Existing certification boundary

- Previous Production Certification: `33369071987`
- Previously certified commit: `bcacbc0eb03b247ad00a232e4eb6324ce5c849df`
- Previous Human real-stack gate: PASS
- Previous Agent real-stack gate: PASS
- Previous product gate failures: `0`

Those results remain attributable only to `bcacbc0...`.

## Independent rehearsal evidence for proposed candidate

- Workflow run: `33482911674`
- Exact revision: `728b7f447d3bc6376fb01d47730cdd70eaf07746`
- Release label supplied to rehearsal: `v1.3.1`
- Rehearsal result: PASS
- Artifact: `phase6e-self-hosted-rehearsal-v1.3.1`
- Artifact SHA-256: `2305cefc54eb31eaf40da95564b2c64461aaf43512658766a28a0c0895278da9`
- Migration head recorded: `p8_03_agent_binding`
- Health / migration / backup-restore / recovery / evidence upload: PASS
- Monitoring: not configured in rehearsal
- Security: rehearsal-only
- External Vendor production acceptance: not established

The rehearsal evidence is valid for `728b7f44...` only.

## Required independent certification

Before external production promotion, the proposed candidate must independently pass the production certification gates on the exact candidate SHA. No existing certification is inherited.

After certification, the same exact SHA must be used to establish:

1. intentional immutable product version/tag
2. exact source commit identity
3. migration identity/head
4. runtime artifact identity
5. Vendor artifact SHA-256
6. Reseller artifact SHA-256
7. Customer artifact SHA-256
8. release/certification evidence

Only then may the Vendor → Reseller → Customer external acceptance sequence begin.

## Current gate

**Candidate reconciliation: RESOLVED** — `728b7f44...` is now isolated as a separate proposed candidate branch.

**Production Certification: PENDING** — certification must run independently on `release/v1.3.2-candidate` / `728b7f44...`.

**Vendor acceptance: NOT STARTED**.

Do not create or retarget a production release tag until the independent certification and exact artifact/checksum reconciliation succeed.
