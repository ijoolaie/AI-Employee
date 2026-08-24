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

Status: **COMPLETE — GITHUB ACTIONS VERIFIED 2026-08-24**

- [x] add profile package generation to release workflow;
- [x] manual release dispatch requires both a release version and an exact release ref;
- [x] checkout is explicitly pinned to the requested release ref;
- [x] the checked-out commit SHA is passed to the three-edition builder;
- [x] release workflow validates the base checksum and all three edition packages;
- [x] runtime and edition packages are uploaded as workflow artifacts;
- [x] successful GitHub Actions Release Artifact run completed and inspected;
- [x] Vendor, Reseller and Customer artifacts confirmed from that Actions run;
- [x] per-edition checksums and combined edition release manifest confirmed from that Actions run;
- [x] base runtime manifest, source identity, migration head, checksum and secret-exclusion policy inspected;
- [x] uploaded artifact archives passed ZIP/TAR integrity inspection.

### Verified execution

Release Artifact workflow run:

```text
run_id       = 32738347495
job_id       = 97466534302
release      = v1.2.0
source_sha   = c329929f1c7e972f626b7ee749c8a2f05a85eace
```

The run completed successfully through runtime packaging, release-note generation, Vendor/Reseller/Customer packaging, checksum verification and artifact upload.

### Verified uploaded artifacts

Runtime artifact:

```text
name   = ai-employee-v1.2.0-runtime
sha256 = a5e3b43f64f5145c2294b38e650ada0fede664bcbed8c1976dd7a20ffb343d85
```

Edition bundle:

```text
name   = ai-employee-v1.2.0-editions
sha256 = bae9941eeb65922d81a6d86141d10dc07cd868c3b924925cbdeeee66721262e0
```

Combined edition manifest:

```text
vendor   = ai-employee-v1.2.0-vendor.1.tar.gz
sha256   = 106e06b8faf430bf96bececdd5c652e81102f349b094628bcfd82c0ae0e55026

reseller = ai-employee-v1.2.0-reseller.1.tar.gz
sha256   = c8140f83d7d6c1c2e9547a9173349036b0c58ec6b229235142bc3a46dabcd484

customer = ai-employee-v1.2.0-customer.1.tar.gz
sha256   = 12cf516d08997bd6b26d727729fefdce15463daaa933a278a67f37a84a4ff62e
```

The runtime `RELEASE-MANIFEST.json` was inspected from the uploaded archive and records:

```text
release_version = v1.2.0
source_commit_sha = c329929f1c7e972f626b7ee749c8a2f05a85eace
source_tag = v1.2.0
migration_head = p5license02
file_count = 511
secrets_included = false
```

The uploaded runtime archive contained 680 TAR entries, passed archive integrity validation, and contained no production `.env` secret file; only `frontend/.env.example` was present. The edition bundle manifest records the same immutable source SHA for all three editions and its listed per-edition SHA-256 values were independently recomputed from the downloaded archives.

### Execution boundary

The Phase 6D execution boundary is now closed: the successful Actions run exists, the exact release identity was checked, all three edition artifacts were uploaded, and their manifest/checksum evidence was inspected. Phase 6E remains an external production-delivery gate and is not implied by this workflow evidence.

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

Phase 6D is complete when the same immutable vendor commit deterministically produces the runtime package plus three validated edition artifacts in GitHub Actions, each with a distinct edition profile and revision identity, and the release evidence records all artifact identities and checksums.

Phase 6 as a whole remains open until Phase 6E production delivery evidence exists.
