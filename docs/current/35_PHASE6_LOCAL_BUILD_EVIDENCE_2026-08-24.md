# Phase 6 — Local Edition Package Verification Evidence — 2026-08-24

## Scope

This document records the local verification evidence for Phase 6A–6C on the `phase6-edition-delivery-separation` branch.

This is local evidence only. It does not claim GitHub Actions execution or production delivery.

## Source identity

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

## Evidence conclusion

Phase 6A, 6B and 6C have local execution evidence.

Phase 6D remains blocked only by external GitHub Actions capacity and Phase 6E remains an external production-delivery gate.

No production certification is claimed by this document.
