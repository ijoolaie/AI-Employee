# AI-Employee Master Hand-off — 2026-10-11

## Current verified repository state

- Repository: `ijoolaie/AI-Employee`
- Latest merged work in this hand-off: PR #1039, squash merge commit `27c44ac33a92c636e552950cdfa2f983255e40a8`.
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
- #1029 remains a draft for renewal UX and has not been merged.

## Open work / acceptance gates

1. **PR #1029 — renewal UX:** original CI failed on React render purity (`Date.now()` during render). Commit `7a9a97a6c54ea8c33cef298b69ef83cf6183c4a7` moves the check into effect-driven refresh logic. This fix has not been validated by fresh CI; the branch is behind current `main` and needs careful reconciliation with #1028 before review.
2. **Support manual acceptance:** verify create → reload → reply/thread → attachment download. Test both ticket participants, foreign tenant denial, deleted/missing files, count/type/size policy, and concurrent attachment reuse/conflict handling.
3. **World manual QA:** test desktop and mobile viewport, keyboard/touch controls, accessibility, console errors and room lease expiry behavior.
4. **Payments / wallet:** live provider verification, signed/replay-safe callbacks, explicit USDT network policy, and World Credit remain blocked until authoritative verification and a durable append-only ledger with atomic replay-safe accounting are implemented.
5. **Release:** no production certification claim; stay on the documented `v1.4.17` release boundary unless a separately certified release is produced.

## PR disposition

- #1039: merged.
- #1027: closed as an outdated draft; its legacy-inventory feature remains merged in #1025. A current-main documentation reconciliation is tracked in PR #1040.
- #1029: open, draft; do not merge until branch reconciliation and exact-head CI pass.
- #1040: open documentation PR; update CURRENT_STATUS and CURRENT_PRIORITIES after #1039 and preserve the release/validation boundaries.

## Next recommended sequence

1. Reconcile #1029 onto current `main`, preserving #1028 expiry status and fail-closed access behavior.
2. Run frontend lint, unit/contracts, production build, Playwright and all exact-head CI checks.
3. Review #1029 diff for stale copy and security boundaries; only then request merge approval.
4. Complete manual support and World Mode acceptance QA, then update this hand-off with observed results rather than inferred status.
