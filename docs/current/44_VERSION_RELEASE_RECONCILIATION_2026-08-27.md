# Version & Release Reconciliation — 2026-08-27

## Status

**AUTHORITATIVE RECONCILIATION CHECKPOINT**

Product releases, architecture baselines, documentation revisions, Git tags and execution waves are separate namespaces.

## Executive decision

### v1.2.0 — CURRENT CERTIFIED CONTROLLED-DEPLOYMENT RELEASE LINE

The existing release-truth system identifies v1.2.0 as the current certified controlled-deployment release line, with external production/commercial certification still open in that reconciliation record.

### v1.2.1-final — EXPLICIT PRODUCTION-CERTIFIED BASELINE

The Git tag `v1.2.1-final` is an annotated tag whose underlying commit is `3994280138bcaf4ef983d8e6bb3d5bbe80a2c561`. Its published release record contains explicit production certification and CI certification evidence.

### v1.2.2 — PUBLISHED RELEASE, CERTIFICATION EVIDENCE INHERITED

The Git tag `v1.2.2` is an annotated tag whose underlying commit is `66394f88fbbdacd583614e8001aae5780d8d7cf0`. A GitHub release exists, but its body reproduces the v1.2.1-final certification record and identifies the v1.2.1-final tag. Therefore this reconciliation does not infer a distinct v1.2.2 certification without a separate certification run.

### v1.3.0 — PUBLISHED DEVELOPMENT / PRODUCT-EXPANSION RELEASE

GitHub contains a published, non-draft, non-prerelease release `v1.3.0`. Its annotated tag ref object is `f7c8ea7cd843c31d8bd447f36d2ae69cb2e9330b`, resolving to commit `73ae16ca51f4cced83e3f03cb5dc0e6239287471`. The release body explicitly describes certification as pending and calls the release a roadmap-preparation/product-evolution release.

Therefore v1.3.0 is a real published release, but **must not be classified as production-certified** from its release record.

`main` is currently 113 commits ahead of the v1.3.0 commit and has no commits behind it relative to that base.

## V1.4 — ARCHITECTURE + EXECUTION BASELINE

V1.4 is not equivalent to a `v1.4.0` product release.

- Architecture Blueprint: FROZEN
- Execution Baseline: ACTIVE
- Initial implementation wave: COMPLETE
- Product release certification: NOT CLAIMED

Completed initial wave: PRs #69–#73.

## V1.5 — AGENTIC OPERATING MODEL

V1.5 is an architecture extension, not a product release. Its direction is Agent-first with a shared Human + Agent execution model.

## Canonical version namespaces

### Product Release
`vMAJOR.MINOR.PATCH`

### Architecture Baseline
`V<baseline> Blueprint`

### Execution Wave
`V<baseline> Execution Wave <n>`

### Documentation Revision
Documentation package versions are not product releases.

## Version matrix

| Identifier | Namespace | Classification | Authority |
|---|---|---|---|
| v1.2.0 | Product Release | Certified controlled-deployment line | Current release reconciliation |
| v1.2.1-final | Product Release | Explicit production-certified baseline | GitHub release + certification record |
| v1.2.2 | Product Release | Published; distinct certification unproven | GitHub release record |
| v1.3.0 | Product Release | Published development/product-expansion release | Git tag + GitHub release |
| V1.4 Blueprint | Architecture | Frozen | Active blueprint |
| V1.4 Execution Wave 1 | Execution | Implemented | PRs #69–#73 |
| V1.5 Agentic Operating Model | Architecture | Active extension | Active blueprint |

## Governance rules

1. Git tags must be reconciled to underlying commits, especially annotated tags.
2. A tag or GitHub release does not prove production deployment.
3. A release must not inherit certification merely because an older release was certified.
4. Architecture and execution versions do not automatically create product releases.
5. Historical handoff documents cannot override this reconciliation.
6. Current status must distinguish latest published release from latest certified production baseline.

## Current project position

```text
LATEST PUBLISHED RELEASE
v1.3.0
    |
    +-- Development / product-expansion release
    +-- Certification pending
    |
CURRENT DEVELOPMENT FRONTIER
main (113 commits ahead of v1.3.0)
    |
    +-- V1.4 frozen architecture baseline
    +-- V1.5 Human + Agent operating-model extension
    +-- Documentation + code truth reconciliation
    +-- Next: Unified WorkItem / Agent execution foundation
```

## References

- `docs/releases/RELEASE_TRUTH_LEDGER.md`
- `docs/releases/GIT_TAG_AND_RELEASE_POLICY.md`
- `docs/00_START_HERE/CURRENT_STATUS.md`
- `docs/current/STATUS.md`
- `docs/current/PRODUCTIZATION_ROADMAP.md`
- `docs/blueprint/V1.4_MASTER_BLUEPRINT.md`
- `docs/blueprint/V1.5_AGENTIC_OPERATING_MODEL.md`