# Phase 6 — Edition Package and Release-System Evidence — 2026-08-24

## Scope

This document records Phase 6A–6D evidence for the edition-separated delivery system and its v1.2.0 release integration.

Local evidence remains distinct from external production certification. Phase 6E is the external production-delivery gate.

## Phase 6A — Profile contract validation

The edition profile validator confirms the three supported delivery roles:

- Vendor
- Reseller
- Customer

The validator and contract test passed during the Phase 6 implementation evidence.

## Phase 6B — Three-edition package generation

The package builder generated Vendor, Reseller and Customer packages for the v1.2.0 delivery line and produced a combined `EDITION-RELEASE-MANIFEST.json`.

The generated package model keeps one shared vendor source tree and separates delivery through immutable release identity, configuration, entitlements and deployment revisions.

## Phase 6C — Package validation

Edition package validation passed for the generated Vendor, Reseller and Customer package set. The validator confirmed the v1.2.0 release identity and the three expected editions.

## Phase 6D — GitHub Actions release-system execution

### Verified execution

- **Workflow run:** `32738347495`
- **Runtime artifact:** `ai-employee-v1.2.0-runtime`
- **Editions artifact:** `ai-employee-v1.2.0-editions`
- **Runtime SHA-256:** `a5e3b43f64f5145c2294b38e650ada0fede664bcbed8c1976dd7a20ffb343d85`
- **Editions SHA-256:** `bae9941eeb65922d81a6d86141d10dc07cd868c3b924925cbdeeee66721262e`

The release workflow is bound to an explicit exact release ref, checks out that ref, records the actual checked-out commit SHA, validates edition profiles, builds the runtime and three edition packages, verifies checksums/metadata, and uploads the artifacts.

### Phase 6D completion

- [x] Release workflow contains three-edition package generation.
- [x] Manual dispatch is bound to an explicit exact release ref.
- [x] Builder receives the actual checked-out commit SHA.
- [x] Runtime checksum verification exists.
- [x] Three-edition package validation exists.
- [x] Runtime and edition artifacts are uploaded.
- [x] Successful GitHub Actions execution recorded — run `32738347495`.
- [x] Runtime and edition artifacts identified from that run.
- [x] Artifact checksums recorded in release certification.
- [x] Release certification document created.

## Release certification

See `docs/current/38_V1.2.0_RELEASE_CERTIFICATION_2026-08-24.md` for the formal v1.2.0 release decision and evidence boundary.

## Phase 6E — External production delivery

Phase 6E remains open. It requires a real production target, protected production environment, target secrets, deployment execution, monitoring, backup/restore, rollback rehearsal, payment/commercial verification where applicable, customer acceptance and target-specific security certification.

No external production certification is claimed here.
