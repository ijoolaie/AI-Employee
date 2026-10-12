## Latest verified checkpoint — 2026-10-12, World V2 visual review candidate

- PR [#1050](https://github.com/ijoolaie/AI-Employee/pull/1050) is the current Draft/unmerged review candidate on current `main`, exact head `c03dc95db96fade9cd30ce36d57b5c74bba8e928`. All five exact-head workflows passed on `c03dc95db96fade9cd30ce36d57b5c74bba8e928`: [CI](https://github.com/ijoolaie/AI-Employee/actions/runs/38212233176), [CodeQL](https://github.com/ijoolaie/AI-Employee/actions/runs/38212233247), [Production Infrastructure Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38212233168), [HA Failure Recovery Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38212233268), and [Ephemeral DAST Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38212233184).
- PR #1046 was closed unmerged as superseded; its latest source, Playwright screenshot capture, responsive viewport and static collision changes were carried into #1050.
- CI run 38212233176 produced artifact `world-visual-review-c3883a003fbd606d6f45b95411929a911a67183e` with desktop (1440×900) and mobile (390×844) screenshots. These are actual Playwright browser captures with deterministic mocked tenant/employee data.
- The screenshots are now ready for human review, but are not evidence of completed visual acceptance. Most character/furniture geometry remains procedural, some room signage clips at the current angle, and movement still lacks full pathfinding/obstacle avoidance.
- Do not merge #1050 until the user reviews the actual visuals. Next implementation gate after review: licensed authored assets, character/prop refinement, navigation and signage/layout corrections, then recapture.
- Latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

---

## Latest verified checkpoint — 2026-10-11 after PR #1040/#1041/#1042 merges

- PR #1040 documentation reconciliation merged at `467e6266540cd429b6e4156ac1a3f9ca00d96759`; CodeQL passed on its final PR head `6a5126d6aad9f88ccd29b91b2e66070272108c7a`.
- PR #1041 merged at `e1633e9bf000af045e2571d930b4eeefec30883f`; exact-head CI, CodeQL, infrastructure, HA recovery and DAST passed. Expired room access remains server-authoritative and fail-closed.
- PR #1042 merged at `cd1f218469d913e4e586e8a0c29b00dbb9d246ad`; all 11 exact-head workflows passed, along with backend (1452 passed, 1 deselected), local Docker build, 13 support-message tests, and real PostgreSQL + HTTP API concurrency regression.
- PR #1045 is closed unmerged after the user rejected its local visual result. PR #1046 remains Draft/unmerged; all five workflows passed on exact head `7f456bda345053e3ff2caf7697a1bc2a36199b19`, but actual desktop/mobile browser screenshots and visual acceptance are still missing. The repository has no GLB/GLTF/FBX/OBJ/BLEND or raster image assets; the current renderer remains primitive-built.
- Remaining gates: manual support create/reload/reply/authorized-attachment QA; customer-tenant support entry point tracked by #1043; and authored/licensed World assets plus actual-browser desktop/mobile visual QA tracked by #1044. Latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

---

## Latest verified checkpoint — 2026-10-11 after PR #1041/#1042 merges

- PR #1041 merged to `main` at `e1633e9bf000af045e2571d930b4eeefec30883f`. Exact head `528750ce9fbac51690d3da6a660394ed6896cbb8` passed CI, CodeQL, Production Infrastructure Validation, HA Failure Recovery Validation and Ephemeral DAST. The server remains authoritative; a renewal order does not itself grant room access.
- PR #1042 merged to `main` at `cd1f218469d913e4e586e8a0c29b00dbb9d246ad`. Exact head `4bebbdcdce78dc5e43276cbaa7aac9136c5fdf4e` passed all 11 workflow runs; backend suite 1452 passed, 1 deselected; local Docker build, 13 support-message tests, and real PostgreSQL + HTTP API concurrency regression passed. Manual support workflow/attachment QA is still outstanding.
- PR #1045 was closed unmerged after the user rejected its local visual result. It is not a completed redesign. PR #1046 carries the combined corrective diff against `main`; all five workflows passed on exact head `7f456bda345053e3ff2caf7697a1bc2a36199b19`, but it remains Draft because actual desktop/mobile browser screenshots and user visual acceptance are missing.
- World visual gaps remain: most employee/furniture geometry is primitive-built, collision-aware pathfinding is absent, and overflow staging is not a final design. Preserve the user's rejection as the acceptance boundary; do not merge #1046 as complete until runtime evidence and visual quality are addressed.
- PR #1040 remains the documentation reconciliation PR; its head was updated to record these dispositions and must be validated on its latest SHA. Latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

---

# AI-Employee Master Hand-off — 2026-10-11


## World visual redesign — approved art direction and active implementation — 2026-10-11

- The user explicitly approved an Idle Company Tycoon / Agent Office-like visual direction: polished stylized isometric 3D office, friendly varied cartoon employees, detailed workstations and rooms, warm/cool lighting, soft shadows and coherent materials. These games are visual references only; no proprietary assets or source code are to be copied.
- PR [#1045](https://github.com/ijoolaie/AI-Employee/pull/1045) was closed unmerged after the user rejected its local visual result. Its implementation history is included in the combined corrective diff of [#1046](https://github.com/ijoolaie/AI-Employee/pull/1046); do not treat #1045 as a completed redesign.
- Latest noted code commit: `11baed5f53d988addd757e07c88954cbae66d5a6` (moves decorative wall art to side walls so it does not cover rear glazing). Follow-on documentation commits exist on the PR branch; check the current PR head and exact-head workflows before reporting final validation.
- PR #1046 exact head `7f456bda345053e3ff2caf7697a1bc2a36199b19` passed CI, CodeQL, Production Infrastructure Validation, HA Failure Recovery Validation and Ephemeral DAST. Automated success does not validate visual quality. Real-browser desktop/mobile screenshots, console/performance inspection, and employee/input/accessibility/room-authorization regression checks remain outstanding. Keep #1046 Draft until those acceptance gates pass.
- Preserve employee selection, keyboard/touch input, accessibility, tenant authorization, fail-closed room expiry/API-error behavior and authoritative room-scene configuration. No release certification changes; latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

## Latest checkpoint — 2026-10-11 16:21 +03:30

### User-observed UI gaps (verified against current source)

- **Customer support entry point:** the generic tenant sidebar shown in the running app has Unified Inbox and Conversations but no support-ticket entry. Those screens represent customer-channel conversations and are not the support escalation workspace.
- The implemented ticket UI is `frontend/app/(reseller)/reseller/support/page.tsx` at `/reseller/support`. The reseller layout guards the route and redirects tenants whose `tenant_kind !== "reseller"` to `/dashboard`; this is why a generic tenant account cannot simply use the reseller page. Do not weaken that guard to make the menu item appear.
- Issue [#1043](https://github.com/ijoolaie/AI-Employee/issues/1043) tracks an authorized customer-tenant support entry and workflow, distinct from Unified Inbox, with tenant-isolated ticket/thread persistence and attachment access. The user has not yet confirmed manual ticket create/reload/reply acceptance in the local stack.
- **World graphics:** `frontend/features/world/WorldViewport.tsx` still constructs the office scene from procedural Three.js primitives (box-based floor tiles, walls, desks and simple procedural characters). PR #1041 is lease-renewal UX only and does not materially redesign the scene. The user's report that the World looks unchanged is consistent with the current implementation.
- Issue [#1044](https://github.com/ijoolaie/AI-Employee/issues/1044) tracks the visual redesign against `docs/blueprint/AI_COMPANY_WORLD_GAMEPLAY_SPEC.md`, requiring actual before/after screenshots at desktop and mobile sizes and regression checks for controls, room authorization and accessibility. Do not claim the redesign is implemented until code changes and screenshots prove it.

### Current open PR disposition (checked at this checkpoint)

- [#1040 docs](https://github.com/ijoolaie/AI-Employee/pull/1040): merged at `467e6266540cd429b6e4156ac1a3f9ca00d96759`; final documentation head CodeQL passed. No runtime test claim.
- [#1041 World lease renewal](https://github.com/ijoolaie/AI-Employee/pull/1041): merged at `e1633e9bf000af045e2571d930b4eeefec30883f`; exact PR head passed CI, CodeQL, Production Infrastructure Validation, HA Failure Recovery Validation and Ephemeral DAST. Functional renewal UX only; visual redesign remains separate.
- [#1042 support attachment concurrency](https://github.com/ijoolaie/AI-Employee/pull/1042): merged at `cd1f218469d913e4e586e8a0c29b00dbb9d246ad`. Exact head passed all 11 workflows; backend suite 1452 passed, 1 deselected; local Docker build, 13 support-message tests, and real PostgreSQL + HTTP API race regression passed. No schema/migration changes. This does not solve the missing customer support navigation in #1043.

PR #1041 and #1042 have since been merged as recorded in the latest checkpoint above. The latest certified release remains `v1.4.17`; CI success is not production certification.


## Current verified repository state

- Repository: `ijoolaie/AI-Employee`
- PR #1039 merged at `27c44ac33a92c636e552950cdfa2f983255e40a8`; subsequent merges: #1041 at `e1633e9bf000af045e2571d930b4eeefec30883f` and #1042 at `cd1f218469d913e4e586e8a0c29b00dbb9d246ad`. PR #1040 remains open for documentation reconciliation.
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

1. **PR #1041 — renewal UX replacement:** merged at `e1633e9bf000af045e2571d930b4eeefec30883f`. Exact head passed all five automated workflow gates. The backend returns `granted=false, reason=lease_expired` for expired leases. PR #1029 remains closed as superseded and was not merged.
2. **Support manual acceptance:** verify create → reload → reply/thread → attachment download. Automated tests now cover concurrent attachment reuse: PR #1042 exact head `4bebbdcdce78dc5e43276cbaa7aac9136c5fdf4e` passed local Docker unit tests (13 passed) and the real PostgreSQL + HTTP API race regression (1 passed). Still manually test both ticket participants, foreign-tenant denial, deleted/missing files, and count/type/size policy.
3. **World manual QA:** test desktop and mobile viewport, keyboard/touch controls, accessibility, console errors and room lease expiry behavior.
4. **Payments / wallet:** live provider verification, signed/replay-safe callbacks, explicit USDT network policy, and World Credit remain blocked until authoritative verification and a durable append-only ledger with atomic replay-safe accounting are implemented.
5. **Release:** no production certification claim; stay on the documented `v1.4.17` release boundary unless a separately certified release is produced.

## PR disposition

- #1039: merged.
- #1027: closed as an outdated draft; its legacy-inventory feature remains merged in #1025. A current-main documentation reconciliation is tracked in PR #1040.
- #1029: closed as superseded, not merged; PR #1041 is the reconciled replacement and has passed exact-head automated checks.
- #1041: merged at `e1633e9bf000af045e2571d930b4eeefec30883f`; exact-head CI/security/infrastructure/recovery/DAST checks passed.
- #1042: merged at `cd1f218469d913e4e586e8a0c29b00dbb9d246ad`; exact head passed all 11 workflow runs, backend suite (1452 passed, 1 deselected), local Docker build, 13 support-message unit tests, and real PostgreSQL + HTTP API concurrency regression (1 passed). No schema/migration changes.
- #1040: merged documentation reconciliation PR at `467e6266540cd429b6e4156ac1a3f9ca00d96759`; final exact head `6a5126d6aad9f88ccd29b91b2e66070272108c7a` passed CodeQL run `38164377498`.

## Next recommended sequence

1. PR #1042 is merged; next finish manual support acceptance: create → reload → reply/thread → authorized attachment download, including both participants, foreign-tenant denial, missing/deleted files and policy limits.
2. PR #1041 is merged; manually verify expiry/renewal UX and preserve #1028 expiry status plus fail-closed access behavior.
3. Manually validate World Mode expiry/renewal and desktop/mobile behavior; CI is not a substitute for local visual QA.
4. Complete manual support acceptance: create → reload → reply/thread → authorized attachment download, including both participants, foreign-tenant denial, missing/deleted files and policy limits. Concurrency is covered by automated/local PostgreSQL regression.
5. Update this hand-off with observed manual QA results rather than inferred status.
