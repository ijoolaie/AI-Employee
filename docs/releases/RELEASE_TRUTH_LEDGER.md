# Release Truth Ledger

**Last reconciled:** 2026-08-27
**Authority:** Git metadata + GitHub release records + explicit certification evidence

## Semantics

- **TAGGED** — Git tag exists and resolves to the recorded object.
- **BUILT** — build/CI evidence exists for the exact release commit or artifact.
- **CERTIFIED** — explicit certification evidence exists.
- **DEPLOYED** — deployment evidence exists.
- **EXTERNALLY_ACCEPTED** — external Vendor/Reseller/Client acceptance evidence exists.

These states are independent.

## Tags currently present

| Tag | Tag ref/object SHA | Underlying commit SHA | Type | Classification |
|---|---|---|---|---|
| v1.0.0 | `175f6454107a2a408a8d2b1f033886f7fd0a5749` | `175f6454107a2a408a8d2b1f033886f7fd0a5749` | lightweight | Historical release |
| v1.0.0-rc.8 | `80e607043b5bee38513ac41036fd24013d650d12` | `a6daf9db52f68c07972642baddb36bcddb88c287` | annotated | Historical RC |
| v1.0.0-rc.9 | `4c6b96e0ee521e54150a3ad42154d3cf3484e4f2` | `2941c046f96fc1de6c53a9db14293471370912c2` | annotated | Historical RC |
| v1.0.1 | `2d23a01098f432145ecaea14b2500fe520ad0bf7` | `2d23a01098f432145ecaea14b2500fe520ad0bf7` | lightweight | Historical release |
| v1.1.0 | `ab477b84a3f9f2441d2029a732a21d534fd217b9` | `ab477b84a3f9f2441d2029a732a21d534fd217b9` | lightweight | Historical release |
| v1.1.1 | `70ca7ad2e1a0abb0850fc1ebb9c4b81b482e13fd` | `70ca7ad2e1a0abb0850fc1ebb9c4b81b482e13fd` | lightweight | Historical release |
| v1.1.2 | `b3c1f1a7f388d24935511bbd966a4aec7e38d1a6` | `f68ecf2df7dc2c9904906c3ef477be02aed98720` | annotated | Historical release |
| v1.2.1 | `45b04b239d3c31a3a97dcd29c8ae183d6435f535` | `38ee6a0b6764ca7e3d666ba35184428b3c293864` | annotated | Historical release |
| v1.2.1-final | `97190d4d37392fbe2554bb5cc9d20fe4f01bebf3` | `3994280138bcaf4ef983d8e6bb3d5bbe80a2c561` | annotated | Production-certified baseline |
| v1.2.2 | `6df2127449a92a5f6cf89a529374522d273053e1` | `66394f88fbbdacd583614e8001aae5780d8d7cf0` | annotated | Published release; certification record inherits prior baseline |
| v1.3.0 | `f7c8ea7cd843c31d8bd447f36d2ae69cb2e9330b` | `73ae16ca51f4cced83e3f03cb5dc0e6239287471` | annotated | Published development/product-expansion release |

## v1.3.0 reconciliation

GitHub has a published, non-draft, non-prerelease release named `AI Employee v1.3.0`, published on 2026-08-26. Its release body describes it as a roadmap-preparation/product-evolution release and explicitly says certification is pending. The annotated tag `v1.3.0` resolves to commit `73ae16ca51f4cced83e3f03cb5dc0e6239287471`. `main` is currently 113 commits ahead of that commit and has no divergence behind it.

## Production baseline

The strongest explicit production certification record found is `v1.2.1-final`, whose release record cites the tag ref and an explicit certification run. The `v1.2.2` release is published, but its body reproduces the v1.2.1-final certification record rather than presenting a distinct new certification run. Therefore v1.2.2 is not promoted here to a separately certified baseline without additional evidence.

## Current interpretation

- Latest published release: **v1.3.0**.
- Current certified controlled-deployment baseline: **v1.2.0**, according to the authoritative release reconciliation; the strongest explicit production certification artifact is **v1.2.1-final**.
- v1.2.2: published release with inherited certification text; separate certification remains unproven.
- v1.3.0: published development/product-expansion release; not production-certified by its own release record.
- Current `main`: development frontier, 113 commits ahead of v1.3.0.

## Next audit

Map every release tag to CI runs/artifacts and deployment evidence. Do not assign BUILT, DEPLOYED or EXTERNALLY_ACCEPTED from naming alone.