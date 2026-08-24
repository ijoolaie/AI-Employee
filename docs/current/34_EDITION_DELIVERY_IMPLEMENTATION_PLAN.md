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

Status: **IN PROGRESS**

- add machine-readable profile metadata;
- add one local builder for all three profiles;
- generate profile manifests from one source release;
- reject secret material;
- preserve one vendor commit SHA across all generated packages.

## Phase 6C — Local verification

Status: **PLANNED**

- validate all three profiles;
- verify immutable vendor identity;
- verify reseller/customer ancestry references;
- verify no profile claims unsupported authority;
- verify package naming and revision rules;
- verify rollback metadata.

## Phase 6D — Release-system integration

Status: **BLOCKED ONLY BY EXTERNAL CI CAPACITY**

- add profile package generation to release workflow;
- attach all three artifacts to the same immutable vendor release;
- publish checksums and profile evidence;
- exercise on GitHub Actions when capacity is available.

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
