# Issue #1350 — Finish-Line Rule and Bounded Completion Plan

**Status:** Active project rule, effective 2026-11-22  
**Tracker:** https://github.com/ijoolaie/AI-Employee/issues/1350  
**Baseline reviewed:** `origin/main` = `5c81d84559bdfa7c23cd89824caf7569176554bc`

## 1. Permanent finish-line rule

Issue #1350 is a finite delivery project, not an open-ended security research program. The approved Issue body and the architecture decisions recorded in `MULTI_VENDOR_PORTAL_ARCHITECTURE_2026-11-02.md` are the scope boundary.

From this date onward:

1. **Scope freeze.** Do not add features, new architectural workstreams, new matrix dimensions, or extra acceptance requirements to Issue #1350 unless the project owner explicitly approves a scope change.
2. **No moving finish line.** A newly noticed edge case is not automatically a new task. First classify it as: (a) already covered by merged evidence, (b) a concrete defect that violates an explicit Issue requirement, (c) not applicable because the capability does not exist, or (d) outside scope / future work. Only category (b) may enter the remaining implementation queue.
3. **Evidence reuse.** Merged PRs, passing exact-head CI, existing live integration tests, source inspection and accepted product decisions count as evidence. Do not recreate a test or PR merely to restate an already-proven behavior.
4. **Representative acceptance, not combinatorial exhaustion.** Use the smallest representative positive and negative cases that prove each explicit requirement across the supported Vendor, Reseller and Customer ownership paths. Do not attempt every mathematically possible Actor × Resource × Action × Delivery combination.
5. **Bounded notification acceptance.** Notifications/Outbox are part of background-job isolation only to the extent needed to prove tenant ownership, delegated actor/grant revalidation, recipient/content isolation and safe failure at the actual provider boundary for the supported Email/WhatsApp flows. Do not pursue an exhaustive channel/provider/worker permutation matrix.
6. **Audit scope is the approved requirement.** Prove that the sensitive administration and portal-context operations explicitly required by Issue #1350 retain actor and target context in the existing audit mechanism. Do not invent an immutable ledger, new Outbox audit events, or a universal failure-audit policy. Those are separate future product/security decisions unless a concrete missing required event is found.
7. **Migration scope is bounded.** Verify the migration/reconciliation plan and synthetic compatibility coverage for existing tenants. No historical production snapshot, Staging/Production rehearsal, or real-account backfill is required to finish this engineering issue; those remain under the separate approved rollout/production gate (#19).
8. **Human UX is a single acceptance checkpoint.** Review the actual Vendor, Reseller and Customer portal flows once against the approved distinct-workflow/navigation/identity requirement. Record accepted or rejected findings. Do not repeatedly reopen visual acceptance for preference-only refinements.
9. **No speculative implementation.** If a product decision is genuinely missing, record one concise decision request and pause only the affected item. Do not build a guessed solution or expand the issue around it.
10. **One final pass.** Once the fixed checklist below is green, prepare the final evidence summary and close Issue #1350. Do not launch another general audit after the final pass.

Security and data integrity are not being waived. The change is to remove unbounded process overhead: retain the repository's normal required checks, focused regression tests and clear evidence; do not demand redundant tests, every conceivable permutation, optional workflows, or unrelated PR cleanup as conditions of this issue.

## 2. Fixed acceptance checklist

| ID | Explicit requirement | Completion evidence | Current disposition |
|---|---|---|---|
| A | Multi-Vendor hierarchy, default Vendor and authorized provisioning | Merged provisioning, registration, lifecycle and hierarchy PRs; existing model/API tests | Implemented; verify current merged baseline once |
| B | Scoped, non-escalating RBAC and delegated portal access | Merged action grants, portal grants, policy/delegation checks and negative sibling/cross-Vendor tests | Implemented; representative evidence exists |
| C | Primary identity remains separate from delegated portal context | Merged portal switching/session and async Run/Workflow actor provenance work | Implemented; representative evidence exists |
| D | Tenant isolation across API, search, reports, files, exports and background jobs | Merged portal live-API, file/search/report/export and worker tenant-fence tests | Substantially implemented; one bounded final coverage review only |
| E | Public registration and membership activation lifecycle | Merged public signup, entitlement/payment/Demo and user lifecycle PRs | Implemented; verify against Issue language, no new flow |
| F | Distinct Vendor, Reseller and Customer experiences | Existing portal routes/layouts plus PR #1452 portal-switch navigation change | Human visual/flow acceptance is outstanding |
| G | Sensitive admin and portal-context actions are auditable | Existing audit attribution tests for grant, portal activation/switch and delegated user lifecycle | Confirm only explicitly required events; no new ledger project |
| H | Existing-tenant compatibility and migration plan | Existing migration/backfill rehearsal on synthetic PostgreSQL fixtures plus documented compatibility plan | Engineering evidence exists; production snapshot/backfill is outside this issue |
| I | Positive/negative security acceptance and regression | Existing merged CI and representative live PostgreSQL acceptance | Run one final targeted regression/CI review; no combinatorial expansion |

A row is complete when its stated evidence exists. A row is not reopened because a different test style, extra provider, hypothetical actor, or additional documentation format could also be added.

## 3. Prioritized remaining work

### P0 — Consolidate existing PR state (first; no new feature code)

Review the remaining open PRs and mark each as one of: mergeable required work, superseded by merged PRs, unrelated maintenance, or human-review item. Do not merge stale branches simply to reduce the open count.

Known dispositions from the current GitHub snapshot:

- **#1477** duplicates the tenant-qualified Run worker lookup already merged as **#1478**. Treat as superseded; no new implementation is needed.
- **#1454** overlaps the hierarchical handoff recipient/tenant evidence subsequently merged in **#1456** and **#1458**, with further Email/WhatsApp evidence in **#1499–#1506**. Compare final diff before disposition; do not repeat its matrix.
- **#1450 and #1451** contain delegated usage/invoice/report coverage. Later merged PRs **#1486, #1487, #1493 and #1498** add usage/report artifact and real async Run evidence. Reuse those merged proofs; retain only a concrete unique assertion if it is still missing from main.
- **#1428 and #1432** are older file lifecycle/sibling-isolation drafts. Later merged **#1429, #1431 and #1455** cover direct/nested file lifecycle and sibling denial. Treat as likely superseded after final diff comparison.
- **#1433** is a dated 2026-11-08 handoff and is stale relative to the current mainline handoff. Do not use it as current project status.
- **#1452** contains the only identified outstanding portal navigation/visual acceptance change (`mode-switch.tsx`) plus `.gitignore` worktree hygiene. It needs a single human product/UX review; do not claim acceptance from CI.
- **#1436, #1439, #1441–#1444** are Dependabot dependency updates, not Issue #1350 acceptance gates. Handle through normal dependency maintenance, independently of project completion.

This list is a disposition guide, not an instruction to close PRs automatically. Before any PR action, check its current head/base, diff, required checks and whether the relevant behavior is already in `main`.

### P1 — One human portal acceptance checkpoint

Review Vendor, Reseller and Customer portal identity, navigation, allowed switching and denied switching against the approved architecture. Use the actual application, not synthetic screenshots. Record one concise accepted/rejected result and only fix concrete violations of the approved requirement. No preference-driven redesign.

### P2 — Close only explicit audit/migration decisions

- Audit: confirm required sensitive administration and portal-context events have actor, actor tenant, target context and outcome in the existing audit mechanism. If present, mark complete. If absent, add only the missing required event(s). Do not design a hash-chain or blanket failure ledger.
- Migration: accept the existing synthetic PostgreSQL migration/backfill rehearsal and compatibility plan as engineering evidence. Production historical snapshot review and live backfill belong to the separate rollout gate, not this issue.

### P3 — One final bounded technical acceptance pass

Run/review the repository's required CI on the final candidate and a focused set of existing tests covering: hierarchy and grants; portal switching; sibling/cross-Vendor denial; search/files/reports/exports; async Run/Workflow actor provenance; Email/WhatsApp tenant/content/provider fences. Reuse existing test modules. Add a test only when a specific explicit acceptance row lacks evidence.

### P4 — Finalize and close

Update the current status and handoff with the fixed checklist, exact merged PR references, final main SHA and known limitations. Confirm no required Issue #1350 work remains, then close Issue #1350. Keep production rollout, external certification and Issue #19 separate.

## 4. Explicitly not required to close Issue #1350

- Realtime WebSocket/SSE implementation (not in the approved Issue scope and not present as a delivered portal transport requirement).
- Exhaustive Actor × Resource × Action or Actor × Hierarchy × Delivery Kind cartesian products.
- New immutable Audit Ledger architecture or universal failure-audit policy.
- Tenant-managed custom-role CRUD without an approved product contract.
- Historical production/staging permission backfill or real customer data mutation.
- New cache subsystem when no server response/data cache exists.
- Daily monitoring automation, unrelated dependency upgrades, broad UI redesign, or unrelated product work.
- Production deployment, payment activation, or closing the separate production evidence gate (#19).

## 5. Operating cadence and change control

- Start each work session from this file and the current `origin/main`; do not revive stale handoff instructions that conflict with this rule.
- Work in the existing authorized project worktree; preserve dirty checkouts and all existing worktrees.
- Before coding, state the exact acceptance row and the already-existing evidence. If no explicit row is missing, do not code.
- Prefer one coherent PR for a bounded acceptance slice over chains of documentation-only or one-assertion PRs.
- Run focused tests and the repository's required CI. Do not run broad repeated suites without a concrete reason.
- New scope requires explicit owner approval and must be tracked separately from Issue #1350.
- Never weaken a real authorization/data-isolation check to make a test pass. Pragmatism means avoiding redundant process, not waiving actual security requirements.

## 6. Review snapshot and confidence boundary

At the time of this review, GitHub reported 300 most-recent PR records: 262 merged, 14 open and 24 closed. The Issue #1350 implementation window spans PR numbers #1353–#1506 (154 PRs; 139 merged, 14 open and 1 closed); the detailed open-PR snapshot and relevant merged PR references above are based on GitHub state observed on 2026-11-22. Counts are a point-in-time snapshot and must be refreshed before final PR disposition.

The current verified `origin/main` at the start of this review was `5c81d84559bdfa7c23cd89824caf7569176554bc`. This document does not claim that human UX acceptance, final PR cleanup, final acceptance CI, production rollout or Issue closure has occurred.

