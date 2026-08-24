# Release Artifact Package

## Purpose

This document defines the Phase 4A release-artifact contract for AI Employee.

A release package is built from one immutable Git commit/tag and contains only approved runtime inputs. It is not a source snapshot and must never contain credentials, customer data, local state, or development caches.

## Build

For a tagged release:

```bash
python scripts/build_release_package.py v1.1.1
```

The command requires Alembic to be installed and verifies that the repository has exactly one authoritative migration head.

The package builder records:

- release version;
- exact source commit SHA;
- source tag;
- source commit timestamp;
- Alembic migration head;
- certification-evidence reference;
- approved runtime allowlist;
- packaged file inventory.

The RELEASE-MANIFEST.json contract includes the canonical release identity field source_commit_sha. This field MUST equal the exact Git HEAD commit from which the release artifact was built. It MUST be the 40-character Git commit SHA and MUST NOT be inferred from the release version.
## Artifact outputs

```text
dist/release/
├── v1.1.1/
│   └── ai-employee-v1.1.1/
│       ├── RELEASE-MANIFEST.json
│       ├── backend/...
│       ├── frontend/...
│       ├── delivery/...
│       └── docker-compose.production.yml
├── ai-employee-v1.1.1-runtime.tar.gz
└── SHA256SUMS
```

The archive metadata is normalized so the same source commit produces deterministic package bytes. `SHA256SUMS` is generated from the final archive.

## Runtime allowlist

The package currently includes:

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

The builder rejects known secret-file names and scans packaged text for private-key material and common API-key formats. Real credentials must be supplied by the deployment environment, never by the release archive.

## CI release gate

`.github/workflows/release-artifact.yml` runs only for a `v*` tag or explicit manual dispatch. It checks out the exact release commit, resolves the Alembic head, builds the package, verifies `SHA256SUMS`, and uploads the archive as a retained GitHub Actions artifact.

## Phase 4A acceptance

- [x] Versioned runtime artifact builder.
- [x] Exact commit identity in release manifest.
- [x] Migration head recorded and single-head enforced.
- [x] Release artifact checksum generated.
- [x] Deterministic archive metadata.
- [x] Secret-file exclusion and content scan.
- [x] CI workflow for tag/manual release packaging.
- [ ] Execute the first real release-tag build after Actions capacity is available.
- [ ] Attach the resulting artifact/checksum to the immutable release record.

## Next Phase 4 slice

After the first successful Phase 4A certification, continue with **Phase 4B — environment/configuration template generation**. Do not add production secrets to the artifact.
