## Latest World room layout checkpoint — 2026-10-10

- Current `main` SHA: `cc58accefb9ec8c2c7c6d1ed579471bcc164b401`.
- PR [#1016](https://github.com/ijoolaie/AI-Employee/pull/1016) merged at `c5a7dc43ca361814543ae5657a06a8469ac26c47` after exact-head CI, both CodeQL analyses, infrastructure, recovery and DAST checks passed. Room access fails closed on query errors and requires a valid future server expiry and room-instance ID; expiry is enforced at the Three.js scene boundary.
- PR [#1018](https://github.com/ijoolaie/AI-Employee/pull/1018) merged as `8c8c62e9c7b9e01f9c99d81035d6da9a557e0e2c`. The backend provides a versioned, bounded scene-config contract and tenant-scoped update endpoint; writes require matching tenant inventory, active catalogue item, active entitlement and unexpired lease.
- PR [#1019](https://github.com/ijoolaie/AI-Employee/pull/1019) merged at `cc58accefb9ec8c2c7c6d1ed579471bcc164b401` after all 14 exact-head checks passed. Main now includes the starter room furniture editor, validated saved-layout rendering and Playwright coverage. The UI supports only the starter preset and bounded built-in furniture placements.
- PR [#1021](https://github.com/ijoolaie/AI-Employee/pull/1021) is open as a **Draft** and not merged. It proposes tenant-scoped, active-employee placements in the room scene config and the corresponding editor/renderer support. Exact-head CI is pending; do not claim employee placement is implemented on main until this PR passes and merges.
- Employee placement is presentation-only. It must not change work assignments, employee status, permissions, AI runs or execution state. Only active employees in the tenant's authoritative office roster may be placed; system employees are not eligible unless explicitly exposed by that read model.
- Next: complete #1021 exact-head CI and review; then add safe handling for stale layout edits and employee deactivation, followed by audited legacy-inventory reconciliation, renewal/expiry UX, support workflow completion, and manual desktop/mobile QA.
- Payment boundary unchanged: provider-specific signed/authoritative verification, replay protection and amount/currency/order matching remain blocked. World Credit remains disabled until a durable append-only ledger and atomic replay-safe debit/credit exist.
- Release boundary unchanged: latest published exact-SHA certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Engineering merges and green CI do not certify a new release or enable production payments.

## Latest engineering checkpoint — persistent room inventory (2026-10-10, PR #1009)

- PR [#1009](https://github.com/ijoolaie/AI-Employee/pull/1009) merged to `main` as `e838c2e9a99dbc01a2e777724cc7d63c5b4a0903`.
- Added the `WorldRoomInventory` model and Alembic revision `20261010_world_room_inventory`, with a tenant-owned room slot tied one-to-one to a World feature entitlement.
- Approved room activation provisions a room inventory row. Renewal reuses the existing tenant/item slot. The DB enforces tenant/item uniqueness and entitlement uniqueness.
- Added `GET /world-commerce/room-inventory` to list the authenticated tenant's currently valid provisioned rooms, and `GET /world-commerce/room-inventory/{item_code}/access` for a server-side access decision. The latter denies missing inventory, suspended inventory, inactive/revoked entitlement, inactive catalogue item, expired lease, and a room lease with no expiry.
- All 20 reported PR-head checks and all 12 post-merge checks on exact merge SHA `e838c2e9a99dbc01a2e777724cc7d63c5b4a0903` completed successfully. Evidence includes backend regression tests, migration graph/upgrade/consistency, frontend smoke, both CodeQL analyses, DAST, infrastructure, RBAC and real-stack workflows.
- **Not yet implemented:** WorldViewport/Three.js does not call this endpoint yet, so the actual room scene is not unlocked or gated by it. This change is durable inventory plus API authorization only. Existing legacy entitlements are not bulk-backfilled into inventory and remain fail-closed until reconciled.
- **Next slice:** connect World Mode room interaction to the authenticated access endpoint and represent room availability only after a positive server response. Treat loading/error/unknown as denied, refresh around expiry, and add E2E tests for active lease, expired lease, missing inventory, cross-tenant access and API failure. Then design a separately audited legacy-inventory reconciliation operation.
- Release boundary unchanged: `v1.4.17` remains the latest published exact-SHA certified release at `b403c0dcdea579e017738a6fdea138c2b1a2999c`; green CI and merged code are not release certification.

## Latest engineering checkpoint — room lease status UI (2026-10-10, PR #1006)

- PR [#1006](https://github.com/ijoolaie/AI-Employee/pull/1006) merged to `main` as `ad381ed17c5f8dedd140644f975647d3ac53b925`.
- `frontend/features/world/WorldShell.tsx` reads `GET /world-commerce/entitlements` for the authenticated tenant and displays active room entitlement code and server-provided expiry. The panel refreshes every 30 seconds and shows a fail-closed message if the server state cannot be loaded.
- Frontend contract tests cover the endpoint, active-room filtering, server expiry, explicit scene-integration disclaimer, and unavailable-state behavior. All 8 reported pre-merge checks passed.
- All 9 post-merge checks on the exact merge SHA completed successfully: frontend, backend, infrastructure, DAST, both CodeQL analyses, Validate SLO contract, validate, and validate-and-package.
- **Not implemented:** entitlement-to-room-inventory mapping, scene-level authorization/unlock, persistence of room instances, customer self-service renewal UI, expiry notifications, provider verification, or World Credit ledger. Do not infer any of these from the status panel.
- **Next implementation slice:** design a tenant-scoped room inventory/instance model and a server-authoritative access contract keyed to the active entitlement and expiry. Fail closed for expired or unreconciled legacy leases and when authorization cannot be loaded. Only then let the 3D scene present/open a room; add backend/API tests, cross-tenant denial tests, migration checks, real-stack coverage and Playwright E2E. Keep order/payment/activation lifecycle separate and preserve two-person approval/activation guards.
- Release boundary unchanged: `v1.4.17` remains the latest published exact-SHA certified release at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Engineering merges and green CI do not certify a new release or prove external production readiness.

# AI Employee World — Master Handoff

**Updated:** 2026-10-10  
**Repository:** `ijoolaie/AI-Employee`  
**Status (2026-10-10):** PR #983 is merged into `main`.  
**Pull request:** [#983 — stylized 3D AI office](https://github.com/ijoolaie/AI-Employee/pull/983)  
**Squash merge commit:** `f3f7ad6c169a5e31b1773b4a280af43b49c020c7`  
**Documentation-updated PR head validated before merge:** `a0952cc44444e5c04c4c245653e59227b3a88a82` (all 17 automated workflows succeeded).  
**Latest `main` head inspected after merge/docs reconciliation:** `e8ec6eae8801ce1c8e709262c7d1d070b0d218aa`. Its docs-head workflow runs: Delivery Manifest Bundle `38036176393`, SLO Contract Manual v2 `38036176381`, CodeQL `38036176360` (all succeeded).  
**Remaining release boundary:** manual desktop/mobile visual QA and production release certification are not complete; merge does not imply production readiness.

## Current verification update — 2026-10-10

**Merged code head:** `a0952cc44444e5c04c4c245653e59227b3a88a82`. All 17 automated workflows completed successfully on this exact PR head before squash merge:

- CI: [37980678249](https://github.com/ijoolaie/AI-Employee/actions/runs/37980678249) — frontend lint, contract/unit tests, production build, World Mode Playwright smoke, backend compile, Ruff, migration gates and backend tests passed.
- CodeQL: [37980677995](https://github.com/ijoolaie/AI-Employee/actions/runs/37980677995) — Python and JavaScript/TypeScript analyses passed.
- HA recovery: [37980678205](https://github.com/ijoolaie/AI-Employee/actions/runs/37980678205) — recovery rehearsal and cleanup passed.
- Ephemeral DAST: [37980678086](https://github.com/ijoolaie/AI-Employee/actions/runs/37980678086) — OWASP ZAP baseline scan and cleanup passed.
- Production infrastructure: [37980678035](https://github.com/ijoolaie/AI-Employee/actions/runs/37980678035) — service lifecycle, migration gate, PostgreSQL backup and isolated restore passed.

This evidence supersedes older SHA-specific status statements below for the merged code. The merge commit is `f3f7ad6c169a5e31b1773b4a280af43b49c020c7`; the later documentation-only `main` head inspected is `e8ec6eae8801ce1c8e709262c7d1d070b0d218aa`. Three workflows triggered for that docs-only head (Delivery Manifest Bundle, SLO Contract Manual v2, CodeQL) all succeeded. Other workflows were validated against the exact PR code head before merge.

**Not yet performed:** manual visual QA across desktop and narrow/mobile viewports. CI's Playwright smoke is automated functional coverage, not a substitute for visual inspection. PR #983 is merged. Future changes should use a new branch/PR and must not treat merge as production release approval.

## 1. Goal and product boundary

Deliver an immersive, colorful, isometric-style **AI Employee World** office interface, using *Startup Empire - Idle Tycoon* only as a high-level visual reference. This is not a game remake and must not turn the product into a game. The World view should present the real AI Employee workforce, state, selection and navigation functionality through a more legible office environment.

No proprietary game assets or source code are copied; current visuals are procedural Three.js geometry.

## 2. Current implementation

Primary implementation:
- `frontend/features/world/WorldViewport.tsx`
- Input lifecycle: `frontend/features/world/WorldInput.ts`
- Input regression tests: `frontend/__tests__/world-input.test.ts`
- World mode E2E: `frontend/e2e/world-mode.spec.ts`
- Three.js type declarations: `frontend/features/world/three.d.ts`

### Visual work completed
- Warm wood/checkerboard floor and pastel department zones.
- Rear window wall, raised isometric camera, shadows and warm/cool lighting.
- Procedurally built seated employees with names, state indicators, selection rings and accessible selection controls.
- Character details include necks, ears, nose, hair cap/fringe, eyebrows, collar, tie, sleeves, forearms and hands.
- Workstations include monitors/stands, keyboards/keys, mouse, papers/notes, mugs and chairs; scene also includes plants, reception furniture and a central HQ focal point.
- Employees are positioned closer to desks and hands are raised toward the keyboard plane.
- Working status is conveyed by a subtle indicator pulse, not whole-character bobbing.

### Interaction, accessibility and resource handling
- Existing employee state/data, selection panel and camera controls remain in place.
- Keyboard and pointer input are separated into `WorldInput.ts`.
- Multi-pointer gestures are captured; pinch completion does not emit an accidental tap.
- A cancelled pointer gesture does not select an employee.
- Window blur clears held movement keys and active gesture state.
- Escape/selection E2E checks verify the employee panel and `aria-pressed` state.
- Animation pauses while the tab is hidden and resumes without a large time jump.
- `prefers-reduced-motion` disables the activity pulse.
- Rebuilt employee visuals dispose replaced geometries, materials and label textures.
- Floor tiles are batched into two `THREE.InstancedMesh` objects; decorative floor tiles do not cast/receive shadows.
- A non-WebGL fallback remains available.

## 3. Important commits

| Commit | Change |
|---|---|
| `c46548deb3833e57550d36d7d4875699db228608` | Batch floor tiles into instanced meshes |
| `af19167b5390f009fb3edbcf10339debd062522f` | E2E accessibility contract for selection and Escape |
| `9293314bdfa4570ca2f8b04a1da0fb814e613086` | Add pointer lifecycle regression tests |
| `5efbf2ceb2fd6a7e6684446eb5e6e80119805b91` | Make blur listener compatible with non-browser test environment |
| `ae666379386ae1f2625617e83fa255c7ab75ce11` | Ignore pointer-move events from pointers without an active pointer-down |
| `92951f79751c2c69811e7ed249aa2ee8b25ec3b2` | Add regression coverage for hover moves during a single-pointer tap |
| `7143aff6680938b2d0b11e43c9dc07c0fc12c1d8` | Previous docs head; its workflow results are historical for the current branch |

The validation evidence below was retrieved for exact PR head `1bf75228bac2c37d693a4b21305fe0bd302e0a4a`. All five workflow runs and every job within them completed successfully on this exact SHA. A subsequent documentation update creates a new head and therefore requires a fresh exact-head check.

## 4. Validation evidence — latest inspected PR head

**Exact tested PR head:** `1bf75228bac2c37d693a4b21305fe0bd302e0a4a`  
**Captured:** 2026-10-09. All five required workflow runs and all jobs within them completed with `success` on this exact SHA.

| Check | Observed state | Evidence |
|---|---|---|
| CI — frontend and backend | Success. Frontend Lint, Contract tests, Unit tests, Production build, Playwright Chromium install and World Mode Playwright smoke all succeeded; backend compile, Ruff, migration gates and backend tests succeeded. | [Run 37980135919](https://github.com/ijoolaie/AI-Employee/actions/runs/37973946846) |
| CodeQL — JavaScript/TypeScript and Python | Both analysis jobs succeeded. | [Run 37980135968](https://github.com/ijoolaie/AI-Employee/actions/runs/37969649529) |
| HA Failure Recovery Validation | Recovery rehearsal, Compose validation and image build succeeded. | [Run 37980135924](https://github.com/ijoolaie/AI-Employee/actions/runs/37969649702) |
| Ephemeral DAST Validation | OWASP ZAP baseline scan, ephemeral stack lifecycle and cleanup succeeded. | [Run 37980136044](https://github.com/ijoolaie/AI-Employee/actions/runs/37969649484) |
| Production Infrastructure Validation | Compose contract, production image build, service lifecycle, database migration gate, backup and isolated restore succeeded. | [Run 37980135852](https://github.com/ijoolaie/AI-Employee/actions/runs/37969649788) |

**Interpretation:** all five automated CI/security/infrastructure gates listed above are green on the inspected SHA. This is not a claim of manual cross-device visual QA or production release certification. Any later commit requires checking the new head before treating these results as current.

### Known prior CI failure and correction

An earlier CI run on `4107c4d75cbfc0313c71b6d5165423256197a0c7` failed in the blur regression test with `ReferenceError: KeyboardEvent is not defined`; 37/38 frontend unit tests passed, while lint, contract tests and backend validation passed. The test was revised to dispatch a plain `Event("keydown")` with a defined `key` property. The current test also verifies that pressing `w` yields `moveY = -1` and that window blur resets movement to zero.

The correction is now covered by a successful CI run on `feb07a6f2c8226ca1dba59fbc83b49fec0e93b71`, including the frontend unit-test and World Mode Playwright smoke steps. The earlier failure remains historical context.

### Latest pointer-cancellation regression fix (validated)

A code review identified a gesture edge case: if a second pointer joined a pinch and was then cancelled before the first pointer ended, the first pointer could still qualify as a tap because the single-pointer origin had not been marked as moved. The input handler now marks the gesture as non-tappable when the second pointer joins, and frontend/__tests__/world-input.test.ts adds a regression test for cancelling the second pinch pointer. This correction and its regression test are included in exact PR head `feb07a6f2c8226ca1dba59fbc83b49fec0e93b71`; CI, CodeQL, HA recovery, DAST, and production infrastructure validation all passed on that SHA.

### Stray pointer-hover regression fix (validated)

A second review found that `onPointerMove` was adding any pointer ID to the active-pointer map, including hover movement from a mouse or stylus that had not started a gesture with `pointerdown`. While another pointer was held, this could falsely look like a multi-pointer gesture and suppress a legitimate tap. The handler now ignores moves from pointer IDs that are not active, and a regression test confirms that a stray hover move does not prevent the active single pointer from selecting. This fix and its regression test are included in exact PR head `1bf75228bac2c37d693a4b21305fe0bd302e0a4a`; all five automated gates passed on that SHA.

### Validation policy

- All five checks must be inspected against the same exact commit SHA.
- A successful job on a prior SHA is historical evidence only.
- A partially completed workflow is not a pass.
- These automated checks do not constitute manual cross-device visual QA or production release certification.

## 5. Immediate next actions

1. All five automated gates passed on exact code head `1bf75228bac2c37d693a4b21305fe0bd302e0a4a`, including both pointer-cancellation and stray-hover regressions. This documentation reconciliation creates a new head, so re-check all five gates after the commit.
2. Perform/record manual browser smoke tests for pinch zoom, pointer cancellation, keyboard movement, focus loss, employee selection, and Escape.
3. Review the rendered scene at desktop and narrow viewport sizes for legibility, selection accuracy and visual hierarchy.
4. Keep this handoff, `CHANGELOG.md`, `DOCUMENTATION_INDEX.md`, and the PR body synchronized with the current head and observed evidence.
5. Keep PR #983 open and Draft. Do not merge or mark ready for review without explicit authorization.

## 6. Scope / non-goals

- Do not redesign World Mode as a game or add game mechanics.
- Do not remove or mock existing employee data, states, controls or accessibility contracts to make a test pass.
- Do not copy third-party proprietary art/assets.
- Do not merge the PR, change it out of Draft, or claim release/production certification based on this branch's UI checks.

## 7. Useful links

- [PR #983](https://github.com/ijoolaie/AI-Employee/pull/983)
- [WorldViewport.tsx](https://github.com/ijoolaie/AI-Employee/blob/feat/world-3d-office/frontend/features/world/WorldViewport.tsx)
- [WorldInput.ts](https://github.com/ijoolaie/AI-Employee/blob/feat/world-3d-office/frontend/features/world/WorldInput.ts)
- [World input tests](https://github.com/ijoolaie/AI-Employee/blob/feat/world-3d-office/frontend/__tests__/world-input.test.ts)
- [World Mode E2E](https://github.com/ijoolaie/AI-Employee/blob/feat/world-3d-office/frontend/e2e/world-mode.spec.ts)


## Latest implementation handoff — 2026-10-10

### Current repository target

- Repository: ijoolaie/AI-Employee
- Working branch / PR: feat/world-3d-office / [PR #983](https://github.com/ijoolaie/AI-Employee/pull/983)
- Implementation head at this handoff refresh: 33411a4b95aa3a5ebd2deb265800fd250066b60a
- The user explicitly authorized merging PR #983. Do not interpret the older historical “do not merge without approval” notes above as overriding this newer authorization; still require the documentation-updated exact head's checks to finish successfully before merge.

### Delivered in this implementation slice

- Playable 3D/isometric World presentation and input/accessibility hardening while preserving the read-only boundary over governed workforce/company data.
- World catalogue, orders, append-only commerce events and feature entitlements; split payment approval from feature activation; tenant-scoped access checks.
- Read-only vendor tenant diagnostics with hierarchy restrictions, data minimization and audit logging.
- Vendor/reseller incoming support escalation inboxes and audited, tenant-scoped status transitions (open, in_progress, resolved).
- At the implementation head above, all 17 workflow runs inspected were successful, including CI backend/frontend, CodeQL, HA recovery, ephemeral DAST, production infrastructure and supporting product/security gates. Documentation updates create a new commit; verify the exact new head before merging.

### Remaining limitations / next work

- No live payment gateway/webhook verification, USDT network policy or wallet/ledger.
- No room lease expiry/renewal, furniture/employee placement fulfillment, or persistent customization applied to the live 3D scene.
- No support reply/message threads, attachments, impersonation or temporary support grants.
- Manual desktop/mobile visual QA is still outstanding; automated CI is not production certification.

### Merge and handoff sequence

1. Verify every required workflow against the documentation-updated PR head.
2. Merge PR #983 only if those checks are green; the user's merge authorization is explicit.
3. Verify the PR's merged state and merge commit SHA from GitHub.
4. Report the merge SHA, exact-head CI evidence, documented limitations, and follow-up work. Do not claim live payment or production certification.


## Merge result — 2026-10-10 (verified)

- PR #983: https://github.com/ijoolaie/AI-Employee/pull/983
- State: closed and merged into main; no longer Draft.
- Squash merge commit: f3f7ad6c169a5e31b1773b4a280af43b49c020c7.
- Validated PR head before merge: a0952cc44444e5c04c4c245653e59227b3a88a82.
- All 17 automated workflows passed on that exact PR head: CI, CodeQL, HA recovery, ephemeral DAST, production infrastructure, and the supporting product/security E2E workflows.
- Frontend CI lint, contract tests, unit tests, production build and World Mode Playwright smoke passed. Backend migration checks and backend tests passed, including the support inbox status-transition regression tests.
- Follow-up limitations: no live payment gateway/webhook verification or wallet/ledger; no lease expiry/renewal or fulfillment automation; no persistent customization wired to the live 3D scene; no support reply threads, attachments, impersonation or temporary support grants. Manual desktop/mobile visual QA and production release certification are still outstanding.
- Next session should resolve the current main SHA, read this handoff and the current status/priority documents, then continue from the remaining limitations rather than treating this merge as production release approval.


## 2026-10-10 follow-up checkpoint — validation and next actions

### Repository / release boundary

- PR #983 is merged to `main` at `f3f7ad6c169a5e31b1773b4a280af43b49c020c7`. The PR head `a0952cc44444e5c04c4c245653e59227b3a88a82` passed all 17 workflows before merge.
- Latest published exact-SHA certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. The World merge is not a new production certification.

### Blocking dependency PR #984

- Inspected PR head: `5287581895464c2942dc4ae4b3f21949e51322a7`.
- CodeQL passed; CI, Production Infrastructure Validation, HA Failure Recovery Validation and Ephemeral DAST Validation failed.
- Root cause: the lockfile resolves Tailwind v4 while `frontend/package.json` and `frontend/postcss.config.mjs` still use Tailwind v3 conventions. CI build fails with the Tailwind PostCSS plugin migration error.
- A formal request-changes review and conversation comment have been posted. Retain the `source-map-js@1.2.2` security update, fix the lockfile/configuration mismatch, and require all mandatory checks green on the exact corrected head before merge.

### World acceptance checklist — still open

- [ ] Manual desktop visual QA, including keyboard navigation, movement, room prompts, employee selection and customization panel.
- [ ] Manual mobile QA, including touch movement, joystick, pinch/zoom cancellation edge cases, responsive layout and touch target behavior.
- [ ] Record browsers/devices, steps, results and screenshots/video; automated CI does not close this gate.
- [ ] Implement and test live payment provider/webhook verification and explicit network/provider policy for USDT before any real-payment claim.
- [ ] Implement wallet ledger, transaction idempotency/replay handling and auditable balance changes before enabling World Credit.
- [ ] Connect approved entitlements to actual room inventory, leases/renewals/expiry, employee placement and durable customization-to-3D-scene state.
- [ ] Complete support reply/thread/attachment workflow; do not imply read-only escalation inboxes are a full support workspace.
- [ ] Re-check all CI/security workflows against the exact current branch head; never inherit previous-SHA success.

No real payments or paid feature activation should be claimed from the current prototype/API foundations. Keep release certification and external deployment/acceptance gates separate.


### Dependency PR #984 correction update — 2026-10-10

- Corrected lockfile commit pushed to PR #984: `de9dabe66a0916ab2b2d8644cd0ef27d3eed0890`.
- The lockfile now derives from `main` and changes only `node_modules/source-map-js` to 1.2.2; Tailwind 3.4.19 and `postcss-selector-parser` 6.1.4 remain present. This removes the unintended Tailwind v4 drift without dropping the intended security fix.
- The old failures were observed on superseded head `5287581895464c2942dc4ae4b3f21949e51322a7`. All five workflows have been triggered on the corrected SHA; their final exact-head outcomes are pending. Do not merge until all required checks pass.


### PR #984 latest-head correction — 2026-10-10

- CI on the intermediate lockfile-only commit showed `npm ci` still failed because the PR branch's `frontend/package.json` also requested Tailwind v4. The correction was therefore extended to restore that manifest to `main`'s Tailwind v3 declaration.
- Latest correction commit: `072e0c077ad18b7cb2afea1c50b8b68aa99be857`. Manifest and lockfile now agree on Tailwind v3; lockfile resolves Tailwind 3.4.19, retains `postcss-selector-parser` 6.1.4, and updates `source-map-js` to 1.2.2.
- CI, CodeQL, Production Infrastructure, HA Recovery and Ephemeral DAST are pending on this exact head. Keep the PR open and unmerged until every required check is green.


### PR #984 final disposition — 2026-10-10

- PR #984 is merged: `36817a54475051ac42a7a445b56a3245845dbfe8`.
- The corrected PR head `072e0c077ad18b7cb2afea1c50b8b68aa99be857` passed CI, CodeQL, Production Infrastructure Validation, HA Failure Recovery Validation and Ephemeral DAST before merge.
- Final dependency scope: update `source-map-js` to 1.2.2; preserve Tailwind v3 and `postcss-selector-parser` 6.1.4. No Tailwind v4 migration was included.
- Keep World manual QA and all external production/release acceptance gates open until independently completed and documented.


## 2026-10-10 follow-through — catalogue-backed currency offer (PR #986)

### Verified merge

- PR: [#986](https://github.com/ijoolaie/AI-Employee/pull/986) — `feat(world): show server catalogue prices by currency`.
- Merge commit: `c0a2b063012263114bd195b68612a423610474d3`.
- Tested PR head: `825155d36e4b1d813b248232a309f8c4d6988720`.
- All eight reported checks passed on that exact head: frontend, backend, infrastructure, CodeQL, CodeQL JavaScript/TypeScript, CodeQL Python, DAST and recovery. Frontend lint, contract tests, unit tests, production build and World Mode Playwright smoke passed.

### What changed

- Replaced the hard-coded room offer placeholder with `frontend/features/world/WorldRoomOfferPanel.tsx`.
- Reads active catalogue data from `GET /world-commerce/catalogue` and offers IRR, USD and USDT selection.
- Only shows server-configured price/provider/payment-method values; missing price is stated as missing, not replaced with a fabricated value.
- Error/loading/empty states are handled. The UI explicitly says it is preview-only.

### Boundaries that remain

- The panel does not create an order, submit a payment reference, verify a provider/webhook, or activate a room.
- Catalogue provider/method labels are configuration data, not evidence of live provider connectivity.
- No World Credit until the wallet ledger, atomic balance mutations, idempotency and replay handling are implemented and tested.
- No live gateway/crypto claims until provider-specific verification, webhook signature/replay controls and USDT network policy are delivered.
- Entitlements still need to drive room inventory/leases/renewals/expiry, employee placement and persistent customization-to-3D-scene state.
- Manual desktop/mobile visual QA remains open; this merge is not production certification. Latest certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

### Next recommended implementation slice

Inspect and use the existing order API contract to add an explicit customer order-creation step to the room offer. The server must remain authoritative for price and validate item/currency/provider/payment method; client requests must include a stable idempotency key. Do not create an order for a currency/provider/method absent from the selected catalogue option. Keep provider verification and fulfillment as distinct future slices unless their end-to-end contracts and tests are completed.


### Follow-up contract audit — catalogue setup is a prerequisite

- The current Alembic migration creates `world_catalogue_items` but does not seed a paid room catalogue entry.
- The current `GET /world-commerce/catalogue` API is read-only; no catalogue create/update API was found in the inspected World commerce router.
- Consequence: the new offer panel is structurally connected to the server but may correctly show an empty catalogue until a catalogue item is configured. This is not a frontend price bug and must not be worked around with hard-coded fallback prices.
- Next implementation should provide a tightly authorized platform-admin catalogue configuration path (or use an explicitly approved seed/config process), validating per-currency amount, provider allowlist and payment-method allowlist. Keep real provider readiness distinct from configuration, and do not choose a USDT network or invent price points.
- Once a valid item is configured, proceed to customer order creation through the existing API with an idempotency key; the backend must continue to calculate the final amount from server-owned catalogue data.


### Follow-through — platform-admin catalogue configuration (PR #988 merged)

- PR #988: https://github.com/ijoolaie/AI-Employee/pull/988
- Squash merge: `e8239e563aef2904fc26fe617e3e3f470819c941`; exact PR head `2c7941b14940660285e8d53098abfe4aeba7f7b2` passed all 16 reported checks.
- Added platform-admin-only list/create/replace endpoints under `/admin/world-commerce/catalogue`, strict request validation for item types/codes and IRR/USD/USDT price options, positive decimal amounts, provider/method choices, free-versus-paid consistency, duplicate-code handling and audit-ledger events.
- Provider/method values are configured choices only. No live payment processing, webhook verification, USDT network policy, World Credit ledger or room fulfillment was added.

### Follow-through — customer order intent (PR #989 merged)

- PR #989: https://github.com/ijoolaie/AI-Employee/pull/989
- Squash merge: `74224ef253a1bb3d990347e34e41dbe31827b97d`; exact PR head `8e538976163aae3bffc5ef88067a2e08987ca673` passed all 8 reported checks.
- `WorldRoomOfferPanel` now calls `POST /world-commerce/orders` with the selected server-configured item code, currency, payment provider/method and a stable idempotency key. No client-owned amount is sent.
- Backend `create_order` inspection confirms that the service loads the active catalogue item, validates currency/provider/method against its server-owned price option, calculates the amount from that option, rejects disabled World Credit, and scopes idempotency by tenant. A reused key with mismatched inputs returns conflict; concurrent retries are handled through the unique-constraint recovery path.
- The UI labels the action as order creation without payment, and shows the order ID/status without claiming that money moved or the room activated.
- Post-merge CI was triggered on merge SHA `74224ef253a1bb3d990347e34e41dbe31827b97d`; inspect its final outcomes before relying on that post-merge run as additional evidence.

### Remaining hard gates

- Provider-specific payment verification, signed webhooks and replay controls; explicit USDT network policy.
- Durable wallet ledger and replay-safe atomic balance accounting before enabling World Credit.
- Entitlement-backed room inventory, lease expiry/renewal, employee placement, fulfillment and durable customization-to-3D-scene state.
- Support reply/thread/attachment workflow.
- Manual desktop/mobile QA and independent production release certification remain outstanding.
- Latest published certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`; the merge does not inherit that certification.
