# Public Repository Branch Audit — 2026-08-24

## Scope

Reviewed the remote branches flagged by `scripts/public_repository_audit.py` against the current Phase 6 delivery branch:

`phase6-edition-delivery-separation` at commit `f68ecf2df7dc2c9904906c3ef477be02aed98720`.

## Findings

### Safe stale branches

The following branches are strictly behind the current Phase 6 branch and contain no commits ahead of it:

- `phase5-commercial-production-foundation-v2`
- `phase5-commercial-production-foundation-v3`
- `phase5-commercial-production-foundation-v4`
- `phase5-commercial-production-foundation-v5`
- `phase5-commercial-production-foundation-v6`
- `phase5-commercial-production-foundation-v7`
- `phase5-release-policy`
- `phase5-release-policy-temp`
- `phase5-release-policy-v2`
- `phase5-release-policy-v3`
- `release/edition-model-v2`

These branches are historical/experimental and do not contain commits that are ahead of the current delivery branch.

### Historical branch retained intentionally

`release/edition-model` is different: it is diverged from the current Phase 6 branch and contains **9 commits not present in the current branch**. Those commits include the original edition delivery workflow, delivery manifests and release-channel documentation. The functionality has since been superseded/reworked in Phase 6, but the branch is retained as a historical reference until final publicization archival policy is agreed.

## Publicization decision

- Stale Phase 5/release-policy branches: **safe candidates for deletion** before making the repository public.
- `release/edition-model-v2`: **safe candidate for deletion** after confirming no external dependency references it.
- `release/edition-model`: **retain as historical reference** for now.

## Limitation

The connected GitHub operations available to this workflow do not expose a remote branch-delete mutation. No branch was deleted automatically. Deletion should be performed from an authenticated Git client after this audit, using an explicit branch list.

## Recommended deletion command

```powershell
git push origin --delete `
  phase5-commercial-production-foundation-v2 `
  phase5-commercial-production-foundation-v3 `
  phase5-commercial-production-foundation-v4 `
  phase5-commercial-production-foundation-v5 `
  phase5-commercial-production-foundation-v6 `
  phase5-commercial-production-foundation-v7 `
  phase5-release-policy `
  phase5-release-policy-temp `
  phase5-release-policy-v2 `
  phase5-release-policy-v3 `
  release/edition-model-v2
```

Run this only after confirming no open PR, deployment system, documentation link, or external automation depends on one of these historical refs.
