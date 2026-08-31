# Version & Release Reconciliation — historical checkpoint

> **SUPERSEDED:** This 2026-08-27 checkpoint is retained as historical evidence. The current implementation/release position is maintained in `docs/current/49_CURRENT_STATE_RECONCILIATION_2026-08-31.md`.

## Historical purpose

Product releases, architecture baselines, documentation revisions, Git tags and execution waves are separate namespaces. This file records the release state as understood on 2026-08-27 and must not override the later current-state reconciliation.

## Historical release truth

### v1.2.0

The release-truth system identified `v1.2.0` as the certified controlled-deployment release line, with external production/commercial certification still open in that reconciliation record.

### v1.2.1-final

The Git tag `v1.2.1-final` is an annotated tag whose underlying commit is `3994280138bcaf4ef983d8e6bb3d5bbe80a2c561`. Its published release record contains explicit production certification and CI certification evidence.

### v1.2.2

The Git tag `v1.2.2` is an annotated tag whose underlying commit is `66394f88fbbdacd583614e8001aae5780d8d7cf0`. A GitHub release exists, but its body reproduces the v1.2.1-final certification record and identifies the v1.2.1-final tag. This checkpoint therefore did not infer distinct v1.2.2 certification.

### v1.3.0

The published `v1.3.0` release resolves to commit `73ae16ca51f4cced83e3f03cb5dc0e6239287471`. Its release record described certification as pending and positioned the release as development/product expansion.

At this checkpoint, `main` was reported as 113 commits ahead of v1.3.0. A later Git comparison reports **221 commits ahead**, so the 113-commit statement is historical and no longer current.

## V1.4 and V1.5

V1.4 remains an architecture/execution baseline rather than an automatic product release. V1.5 is an architecture extension implementing the Human + Agent operating model rather than a product version by itself.

## Current authority

For the current state as of 2026-08-31, use:

- `docs/current/49_CURRENT_STATE_RECONCILIATION_2026-08-31.md`
- `docs/current/STATUS.md`
- `docs/00_START_HERE/CURRENT_STATUS.md`
- `docs/current/PRODUCTIZATION_ROADMAP.md`

The current reconciliation establishes that `main` is the implementation baseline, while `v1.3.0` remains the latest published product release. It also distinguishes GitHub/CI verification from external production evidence.
