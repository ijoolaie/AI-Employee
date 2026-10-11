# AI-Employee Master Hand-off — 2026-10-11

## Latest checkpoint — 2026-10-11 16:21 +03:30

### User-observed UI gaps (verified against current source)

- **Customer support entry point:** the generic tenant sidebar shown in the running app has Unified Inbox and Conversations but no support-ticket entry. Those screens represent customer-channel conversations and are not the support escalation workspace.
- The implemented ticket UI is `frontend/app/(reseller)/reseller/support/page.tsx` at `/reseller/support`. The reseller layout guards the route and redirects tenants whose `tenant_kind !== "reseller"` to `/dashboard`; this is why a generic tenant account cannot simply use the reseller page. Do not weaken that guard to make the menu item appear.
- Issue [#1043](https://github.com/ijoolaie/AI-Employee/issues/1043) tracks an authorized customer-tenant support entry and workflow, distinct from Unified Inbox, with tenant-isolated ticket/thread persistence and attachment access. The user has not yet confirmed manual ticket create/reload/reply acceptance in the local stack.
- **World graphics:** `frontend/features/world/WorldViewport.tsx` still constructs the office scene from procedural Three.js primitives (box-based floor tiles, walls, desks and simple procedural characters). PR #1041 is lease-renewal UX only and does not materially redesign the scene. The user's report that the World looks unchanged is consistent with the current implementation.
- Issue [#1044](https://github.com/ijoolaie/AI-Employee/issues/1044) tracks the visual redesign against `docs/blueprint/AI_COMPANY_WORLD_GAMEPLAY_SPEC.md`, requiring actual before/after screenshots at desktop and mobile sizes and regression checks for controls, room authorization and accessibility. Do not claim the redesign is implemented until code changes and screenshots prove it.

### Current open PR disposition (checked at this checkpoint)

- [#1040 docs](https://github.com/ijoolaie/AI-Employee/pull/1040): open, non-Draft, mergeable. Current head `783e5cc9feb266d01013ed6325ea31008949a939`; exact-head CodeQL run `38136817003` completed successfully. Documentation-only; no runtime test claim. Recommended disposition: ready for final review/merge, but do not merge without explicit approval.
- [#1041 World lease renewal](https://github.com/ijoolaie/AI-Employee/pull/1041): open, non-Draft, mergeable. Exact head `528750ce9fbac51690d3da6a660394ed6896cbb8`; CI, CodeQL, Production Infrastructure Validation, HA Failure Recovery Validation and Ephemeral DAST all succeeded. No submitted reviews or inline threads were present at this check. Functional renewal UX only; World visual redesign and local visual QA remain outstanding. Recommended disposition: review-ready, but do not merge without explicit approval.
- [#1042 support attachment concurrency](https://github.com/ijoolaie/AI-Employee/pull/1042): open, Draft, mergeable. Exact head `4bebbdcdce78dc5e43276cbaa7aac9136c5fdf4e`; all 11 workflow runs succeeded; backend suite 1452 passed, 1 deselected; workstation Docker build succeeded, 13 support-message tests passed and real PostgreSQL + HTTP API race regression passed (1 test, 2.63s). No schema/migration changes. Recommended disposition: technically validated but keep Draft pending explicit approval/review. This does not solve the missing customer support navigation in #1043.

No PR was merged during this checkpoint. The latest certified release remains `v1.4.17`; CI success is not production certification.


## Current verified repository state

- Repository: `ijoolaie/AI-Employee`
- Latest merged work in this hand-off: PR #1039, squash merge commit `27c44ac33a92c636e552950cdfa2f983255e40a8`. PRs #1040 (docs), #1041 (World lease renewal UX), and #1042 (support attachment concurrency) remain open and unmerged.
- PR #1039 exact tested head: `9febc1124b28f53b8b8b4ba5c09a8f26bb978dfa`; reported CI passed, including isolated PostgreSQL migration/persistence tests, backend tests, frontend lint/build, Playwright browser regressions, CodeQL, DAST, architecture, security/privacy and infrastructure checks.
- Latest published certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Engineering merges and green CI are not production deployment or release certification.

## Merged implementation slices

### Reseller support
- #1031: tenant-scoped support escalation message threads.
- #1033: tenant-safe message attachments and participant-scoped downloads.
- #1035: reseller support conversation workspace.
- #1036: persisted reseller-created tickets across page reloads.
- #1039: PostgreSQL-backed HTTP API persistence/tenant-isolation regression plus Playwright reload regression.

Coverage boundary: the Playwright reload regression mocks the API; the backend API regression separately exercises PostgreSQL and tenant isolation.

### AI Company World
- #1016: server-authorized room access gate.
- #1018: validated room scene configuration API.
- #1019: room furniture editor.
- #1021: tenant-scoped employee placements (presentation only).
- #1023: stale layout write protection.
- #1025: audited, dry-run-first legacy room inventory reconciliation.
- #1028: room lease expiry communication.
- #1029: closed as superseded by PR #1041; it was not merged. Its stale branch is not a source of truth.

## Open work / acceptance gates

1. **PR #1041 — renewal UX replacement:** created from current main rather than merging the diverged #1029 branch. Exact head `528750ce9fbac51690d3da6a660394ed6896cbb8` passed CI, CodeQL, Production Infrastructure Validation, HA Failure Recovery Validation and Ephemeral DAST. Backend `room_inventory_access` returns `granted=false, reason=lease_expired` for expired leases. Review remains required; do not merge without explicit approval. PR #1029 is closed as superseded and was not merged.
2. **Support manual acceptance:** verify create → reload → reply/thread → attachment download. Automated tests now cover concurrent attachment reuse: PR #1042 exact head `4bebbdcdce78dc5e43276cbaa7aac9136c5fdf4e` passed local Docker unit tests (13 passed) and the real PostgreSQL + HTTP API race regression (1 passed). Still manually test both ticket participants, foreign-tenant denial, deleted/missing files, and count/type/size policy.
3. **World manual QA:** test desktop and mobile viewport, keyboard/touch controls, accessibility, console errors and room lease expiry behavior.
4. **Payments / wallet:** live provider verification, signed/replay-safe callbacks, explicit USDT network policy, and World Credit remain blocked until authoritative verification and a durable append-only ledger with atomic replay-safe accounting are implemented.
5. **Release:** no production certification claim; stay on the documented `v1.4.17` release boundary unless a separately certified release is produced.

## PR disposition

- #1039: merged.
- #1027: closed as an outdated draft; its legacy-inventory feature remains merged in #1025. A current-main documentation reconciliation is tracked in PR #1040.
- #1029: closed as superseded, not merged; PR #1041 is the reconciled replacement and has passed exact-head automated checks.
- #1041: open, ready for review, unmerged; exact-head CI/security/infrastructure/recovery/DAST checks passed and backend expiry contract was verified. No submitted reviews or inline review threads are present as of this check. Await review and explicit merge approval.
- #1042: open Draft, unmerged; exact head `4bebbdcdce78dc5e43276cbaa7aac9136c5fdf4e` passed all 11 workflow runs, backend suite (1452 passed, 1 deselected), local Docker build, 13 support-message unit tests, and the local real PostgreSQL + HTTP API concurrency regression (1 passed in 2.63s). No schema/migration changes. Await review and explicit merge approval.
- #1040: open documentation PR; reconciles CURRENT_STATUS, CURRENT_PRIORITIES, Changelog and this hand-off after #1039/#1041/#1042 while preserving release/validation boundaries. Current head `8a844330e0ce01962f1fdd9c47bcd3c05bf313e4` has a successful CodeQL workflow run `38134175993`.

## Next recommended sequence

1. Code review the PR #1042 race fix and confirm exact-head checks; automated/local regression is green, but keep it Draft until explicit user approval.
2. Review PR #1041 diff and successful exact-head CI, preserving #1028 expiry status and fail-closed access behavior; wait for explicit merge approval.
3. Manually validate World Mode expiry/renewal and desktop/mobile behavior; CI is not a substitute for local visual QA.
4. Complete manual support acceptance: create → reload → reply/thread → authorized attachment download, including both participants, foreign-tenant denial, missing/deleted files and policy limits. Concurrency is covered by automated/local PostgreSQL regression.
5. Update this hand-off with observed manual QA results rather than inferred status.
