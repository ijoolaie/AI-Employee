# Release Artifact Package

## Status

**Contract status:** Active template/specification  
**Current certified release example:** `v1.2.0`  
**Release truth:** `docs/current/39_RELEASE_TRUTH_V1.2.0.md`

## Purpose

A release package is built from one immutable Git commit/tag and contains only approved runtime inputs. It is not a source snapshot and must never contain credentials, customer data, local state, or development caches.

## Build

For a tagged release:

```bash
python scripts/build_release_package.py v1.2.0
```

The version above is the current certified-release example, not a hard-coded future release requirement.

The command verifies that the repository has exactly one authoritative Alembic migration head and records:

- release version;
- exact source commit SHA;
- source tag;
- source commit timestamp;
- Alembic migration head;
- certification-evidence reference;
- approved runtime allowlist;
- packaged file inventory.

`source_commit_sha` MUST equal the exact immutable Git commit used to build the artifact. It MUST be the 40-character Git commit SHA and MUST NOT be inferred from the version string.

## Artifact outputs

```text
dist/release/
├── <version>/
│   └── ai-employee-<version>/
│       ├── RELEASE-MANIFEST.json
│       ├── backend/...
│       ├── frontend/...
│       ├── delivery/...
│       └── docker-compose.production.yml
├── ai-employee-<version>-runtime.tar.gz
└── SHA256SUMS
```

Archive metadata is normalized so the same source commit produces deterministic package bytes. `SHA256SUMS` is generated from the final archive.

## Runtime allowlist

The package includes approved runtime material such as:

- `backend/app`
- `backend/alembic`
- `backend/alembic.ini`
- `backend/Dockerfile`
- `backend/requirements.txt`
- `frontend`
- `delivery`
- `docker-compose.production.yml`
- `README.md`
- `CHANGELOG.md`

Tests, development environments, caches, generated frontend state, local storage and Git metadata are excluded.

## Secret boundary

The builder rejects known secret-file names and scans packaged text for private-key material and common API-key formats. Real credentials are supplied by deployment environments, never by the release archive.

## CI release gate

`.github/workflows/release-artifact.yml` runs for a `v*` tag or explicit manual dispatch. It checks out the exact release revision, resolves the Alembic head, builds the package, verifies checksums, and uploads retained Actions artifacts.

## Current evidence

The current certified controlled release is **v1.2.0**:

- Release workflow run: `32738347495`
- Runtime artifact: `ai-employee-v1.2.0-runtime`
- Editions artifact: `ai-employee-v1.2.0-editions`

This evidence is release-system evidence only. It does not by itself certify an externally deployed production target.

## Acceptance

- [x] Versioned runtime artifact builder.
- [x] Exact commit identity in release manifest.
- [x] Migration head recorded and single-head enforced.
- [x] Release artifact checksum generated.
- [x] Deterministic archive metadata.
- [x] Secret-file exclusion and content scan.
- [x] CI workflow for tag/manual release packaging.
- [x] Real release-system evidence retained for v1.2.0.

## Next artifact work

Future release/package changes must preserve the distinction between:

- current certified vendor release;
- active implementation baseline;
- historical release evidence;
- externally deployed production evidence.
