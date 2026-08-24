# Phase 6 — Edition-Separated Delivery Implementation Plan

## Goal

Produce three separately named delivery artifacts from one authoritative source release:

- Vendor Edition
- Reseller Edition
- Customer Edition

Do not create permanent source forks. Edition differences are represented by package profile, manifest, configuration, release channel and delivery revision while runtime authorization remains server-enforced.

## Phase 6A — Contract and nomenclature

Status: **COMPLETE**

- define three edition profiles;
- define release matrix;
- define profile-specific manifest requirements;
- document rollback identity rules;
- preserve Vendor → Reseller → Customer hierarchy.

## Phase 6B — Profile packaging

Status: **COMPLETE — LOCAL VERIFIED**

- add machine-readable profile metadata;
- add one local builder for all three profiles;
- generate profile manifests from one source release;
- reject secret material;
- preserve one vendor commit SHA across all generated packages.

## Phase 6C — Local verification

Status: **COMPLETE — LOCAL VERIFIED 2026-08-24**

- validate all three profiles;
- verify immutable vendor identity;
- verify reseller/customer ancestry references;
- verify no profile claims unsupported authority;
- verify package naming and revision rules;
- verify rollback metadata;
- generate and validate the Vendor, Reseller and Customer archives from one source commit.

Local evidence is recorded in `docs/current/35_PHASE6_LOCAL_BUILD_EVIDENCE_2026-08-24.md`.

## Phase 6D — Release-system integration

Status: **WORKFLOW READY — EXTERNAL ACTIONS EXECUTION EVIDENCE PENDING**

- [x] add profile package generation to release workflow;
- [x] manual release dispatch requires both a release version and an exact release ref;
- [x] checkout is explicitly pinned to the requested release ref;
- [x] the checked-out commit SHA is passed to the three-edition builder;
- [x] release workflow validates the base checksum and all three edition packages;
- [x] runtime and edition packages are uploaded as workflow artifacts;
- [ ] attach Vendor, Reseller and Customer artifacts to the same immutable vendor release in a successful GitHub Actions run;
- [ ] publish per-edition checksums and combined edition release manifest from a successful Actions run;
- [ ] verify artifact generation on the first successful post-reset Actions run.

The workflow correction was committed to `main` as `4391875222a6c8f1ddf8a3f3448b8e6d51b6454b`.

The corrected manual dispatch contract is:

```text
version = vX.Y.Z
ref     = exact branch, tag, or commit SHA
```

The workflow then checks out that exact ref, records the actual `git rev-parse HEAD`, and uses that SHA for Vendor/Reseller/Customer package generation. Tag pushes continue to derive both version and release ref from the pushed tag.

**Execution boundary:** this document does not claim a successful GitHub Actions run until a real workflow-dispatch or tag-triggered run exists and its jobs/artifacts have been inspected.

## Phase 6E — Production delivery

Status: **EXTERNAL GATE**

- deliver a real Vendor environment;
- deliver a real Reseller environment;
- deliver a real Customer environment;
- capture environment-specific monitoring, recovery, security and handoff evidence.

## Non-goals

Phase 6 does not:

- create three independent codebases;
- duplicate migrations or application logic;
- weaken tenant or RBAC enforcement;
- expose vendor secrets to downstream editions;
- claim production certification without production evidence.

## Definition of done

Phase 6 is complete when the same immutable vendor commit deterministically produces three validated artifacts, each with a distinct edition profile and revision identity, and the release evidence records all three artifacts.
