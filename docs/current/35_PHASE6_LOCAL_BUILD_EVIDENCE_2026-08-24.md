# Phase 6 — Edition Package Verification Evidence — 2026-08-24

## Scope

This document records the local verification evidence for Phase 6A–6C and the release-system readiness work for Phase 6D.

Local evidence does not claim GitHub Actions execution or production delivery. Phase 6D is only considered externally verified after a real Actions run has completed and its jobs/artifacts have been inspected.

## Source identity — local Phase 6A–6C evidence

- Branch: `phase6-edition-delivery-separation`
- Source commit used for package generation: `4ed4646b5c820a22bdfb51c92e5ca176243dc895`
- Profile validator source release identity: `v1.1.0`
- Profile validator source commit identity: `ab477b84a3f9f2441d2029a732a21d534fd217b9`

## Phase 6A — Profile contract validation

Command:

```text
python .\\scripts\\validate_edition_profiles.py
```

Result:

```text
phase6 edition profiles valid
vendor_release_tag=v1.1.0
vendor_commit_sha=ab477b84a3f9f2441d2029a732a21d534fd217b9
profiles=vendor,reseller,customer
```

Contract test:

```text
python -m pytest .\\backend\\tests\\test_phase6_edition_profiles.py -q
```

Result: `3 passed`.

## Phase 6B — Three-edition package generation

Command:

```text
python .\\scripts\\build_edition_packages.py v1.2.0 4ed4646b5c820a22bdfb51c92e5ca176243dc895 --vendor-revision 1 --reseller-revision 1 --customer-revision 1 --out .\\dist\\editions\\v1.2.0
```

Generated artifacts:

| Edition | Artifact | SHA-256 | Source commit |
|---|---|---|---|
| Vendor | `ai-employee-v1.2.0-vendor.1.tar.gz` | `e8d3b575c19646330cc0b6f9c88235b0cf7d8391fe0f9c67598f99a7be298af1` | `4ed4646b5c820a22bdfb51c92e5ca176243dc895` |
| Reseller | `ai-employee-v1.2.0-reseller.1.tar.gz` | `ef9d264ecb79640e5c110aaefa937f843572f2eca1942c2be953489eeb797cf8` | `4ed4646b5c820a22bdfb51c92e5ca176243dc895` |
| Customer | `ai-employee-v1.2.0-customer.1.tar.gz` | `389a203be7d6f31ff1cacc2c2d8ab53c3c34a3cdeb25f8f4615bb6dc57be9814` | `4ed4646b5c820a22bdfb51c92e5ca176243dc895` |

The generated output also contains `EDITION-RELEASE-MANIFEST.json`.

## Phase 6C — Package validation

Command:

```text
python .\\scripts\\validate_edition_packages.py .\\dist\\editions\\v1.2.0
```

Result:

```text
phase6 edition packages valid
vendor_release_tag=v1.2.0
vendor_commit_sha=4ed4646b5c820a22bdfb51c92e5ca176243dc895
artifacts=vendor,reseller,customer
```

## Phase 6D — Release-system integration readiness

### Workflow

`.github/workflows/release-artifact.yml` was corrected on `main` in commit:

`4391875222a6c8f1ddf8a3f3448b8e6d51b6454b`

The manual dispatch contract now requires:

```text
version = vX.Y.Z
ref     = exact branch, tag, or commit SHA
```

The workflow then:

1. derives the version and exact release ref;
2. checks out that exact ref;
3. records `git rev-parse HEAD` as the actual release commit;
4. validates edition profiles and contract tests;
5. builds the immutable runtime package;
6. builds Vendor, Reseller and Customer packages using the actual checked-out commit SHA;
7. verifies runtime and edition package checksums/metadata;
8. uploads runtime and edition artifacts to the workflow run.

### Execution evidence

A successful GitHub Actions run has **not yet been recorded in repository evidence**. The available GitHub integration in this session exposes workflow-run inspection and artifact retrieval, but does not expose a workflow-dispatch/tag-creation write operation. Therefore no Actions run is being fabricated or marked as successful.

### Required Phase 6D completion evidence

- [x] Release workflow contains three-edition package generation.
- [x] Manual dispatch is bound to an explicit exact release ref.
- [x] Builder receives the actual checked-out commit SHA.
- [x] Runtime checksum verification exists.
- [x] Three-edition package validation exists.
- [x] Runtime and edition artifacts are uploaded.
- [ ] Successful GitHub Actions execution recorded.
- [ ] Vendor, Reseller and Customer artifacts inspected from that run.
- [ ] Per-edition checksums and combined manifest confirmed from that run.

## Evidence conclusion

Phase 6A, 6B and 6C have local execution evidence. Phase 6D has implementation and workflow-readiness evidence, but **external Actions execution evidence remains pending**. Phase 6E remains an external production-delivery gate.

No production certification is claimed by this document.
