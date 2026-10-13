## PR #1083 merged — responsive World camera-control anchors (2026-10-13)

- PR [#1083](https://github.com/ijoolaie/AI-Employee/pull/1083) merged by squash as `7ffd7720cbd7c931724a281c875152170d188afe`, from exact PR head `19bc76052955f2b22ceafe43aab2f2983f77fe65`.
- Change: removed the inline `right: 12px` positioning that overrode responsive classes; controls now use `right-3 bottom-4` by default and `sm:left-4 sm:right-auto` on desktop.
- All five observed exact-head workflow groups passed: [CI / frontend+backend+Playwright 38381090279](https://github.com/ijoolaie/AI-Employee/actions/runs/38381090279), [CodeQL 38381090284](https://github.com/ijoolaie/AI-Employee/actions/runs/38381090284), [Production Infrastructure 38381090299](https://github.com/ijoolaie/AI-Employee/actions/runs/38381090299), [HA Failure Recovery 38381090566](https://github.com/ijoolaie/AI-Employee/actions/runs/38381090566), and [Ephemeral DAST 38381090384](https://github.com/ijoolaie/AI-Employee/actions/runs/38381090384).
- Fresh [desktop/mobile artifact 11803596084](https://github.com/ijoolaie/AI-Employee/actions/runs/38381090279/artifacts/11803596084) was manually inspected at 1440×900 and 390×844. Desktop controls are bottom-left; mobile controls are bottom-right and visibly separate from the bottom-left joystick.
- This is a bounded layout fix. It does not complete Issue [#1044](https://github.com/ijoolaie/AI-Employee/issues/1044), skeletal animation, role-specific character art, obstacle-aware pathfinding, release certification, or production deployment. The available workflow wrapper did not return post-merge runs for the merge SHA; post-merge state must not be inferred from pre-merge checks.

## PR #1082 merged — reduced-motion-aware working employee sway (2026-10-13)

- PR: [#1082](https://github.com/ijoolaie/AI-Employee/pull/1082), squash-merged after exact-head CI/security/infra checks and fresh desktop/mobile screenshot review passed.
- Exact PR head: `9a8cb2179cb7675a773b7dd51e99251a9e2838fb`; merge commit: `f1b4f782d8753da6c5f960b50942e9a5a6f16b06`.
- Implementation: `getWorkerBodySway` adds a small deterministic body rotation only for `WORKING` employees; it returns zero for other states and when `prefers-reduced-motion: reduce` is active. Four Vitest cases cover state gating, reduced motion, amplitude/determinism and phase variation.
- Exact-head workflows passed: [CI 38378436816](https://github.com/ijoolaie/AI-Employee/actions/runs/38378436816) (backend and frontend; lint, contracts, unit tests, production build and Playwright), [CodeQL 38378436770](https://github.com/ijoolaie/AI-Employee/actions/runs/38378436770), [Ephemeral DAST 38378436804](https://github.com/ijoolaie/AI-Employee/actions/runs/38378436804), [Production Infrastructure Validation 38378436717](https://github.com/ijoolaie/AI-Employee/actions/runs/38378436717), and [HA Failure Recovery Validation 38378436814](https://github.com/ijoolaie/AI-Employee/actions/runs/38378436814).
- Desktop/mobile artifact [11802346424](https://github.com/ijoolaie/AI-Employee/actions/runs/38378436816/artifacts/11802346424) was inspected. Desktop layout is intact; on the 390×844 mobile screenshot the joystick stays bottom-left and camera controls bottom-right with no visible overlap. Static screenshots confirm layout only, not the animation over time.
- Post-merge workflows on the merge SHA: [SLO Contract Manual v2 38378936646](https://github.com/ijoolaie/AI-Employee/actions/runs/38378936646) and [Delivery Manifest Bundle 38378937055](https://github.com/ijoolaie/AI-Employee/actions/runs/38378937055) passed. At this documentation checkpoint, post-merge [CI 38378936957](https://github.com/ijoolaie/AI-Employee/actions/runs/38378936957), [Production Compose Validation 38378937006](https://github.com/ijoolaie/AI-Employee/actions/runs/38378937006), [Production Infrastructure Validation 38378937068](https://github.com/ijoolaie/AI-Employee/actions/runs/38378937068), [CodeQL 38378937201](https://github.com/ijoolaie/AI-Employee/actions/runs/38378937201), and [Ephemeral DAST 38378937394](https://github.com/ijoolaie/AI-Employee/actions/runs/38378937394) were still running; update this status after their final results.
- Scope boundary: this is an ambient presentation cue, not skeletal rigging or a walk cycle. Issue [#1044](https://github.com/ijoolaie/AI-Employee/issues/1044) remains open for the broader World redesign. No release certification, deployment, or customer-acceptance claim is implied; certified release remains `v1.4.17`.

# AI Employee World — Master Handoff
**Updated:** 2026-10-13  
**Status:** PR #1081 is merged to `main` as `71755e07660f380116f3c157f3e78e9e1c7f79d6` from exact PR head `7a6b410c5bbf1b27b72a024a2b823bf19711de82`; pre-merge CI/security/infra gates passed and desktop/portrait visual review confirmed no HUD/joystick/camera-control overlap. All seven observed post-merge workflow groups passed on the merge SHA. PR #1076 is merged to `main` as `fc669d9aa6ee32c099a605873cc8ffca8b95b988` from exact PR head `46a7f13ce9c4b8e9f94352f3862539efa14c404e`; all seven exact-head groups passed, visual artifacts were reviewed, and all nine observed post-merge groups passed. The accepted change adds a project-original static employee GLB with deterministic material variation and procedural fallback. It does not complete rigging/animation, role-specific art or full pathfinding. PR #1071 viewport framing is accepted for its bounded criterion. PR #1072 is merged at `c097eedbc5674d788d72b5b3a2d334adba1737e6` from exact head `98e740fbc95d6597440fee2216977762e008fa0a`; all five workflow groups passed, and the fresh 1440×900 desktop / 390×844 portrait screenshots were manually reviewed. The glass-partition pass is accepted; broader redesign and gameplay work remain incomplete.

## PR #1081 merged — mobile World camera controls (2026-10-13)

- PR: [#1081](https://github.com/ijoolaie/AI-Employee/pull/1081), merged by squash after the exact PR-head checks and visual review passed.
- Validated PR head: `7a6b410c5bbf1b27b72a024a2b823bf19711de82`; merge commit on `main`: `71755e07660f380116f3c157f3e78e9e1c7f79d6`.
- Change: mobile camera controls are anchored to the bottom-right (`right: 12px; bottom: 16px; top: auto`) to keep them apart from the top-left HUD and bottom-left joystick. Reset/fullscreen controls have accessible labels/titles and 40px mobile targets; the Playwright overlap assertion now includes measured HUD/control boxes in failure diagnostics.
- Pre-merge exact-head evidence: CI run [38376582057](https://github.com/ijoolaie/AI-Employee/actions/runs/38376582057) passed frontend and backend jobs; CodeQL [38376581915](https://github.com/ijoolaie/AI-Employee/actions/runs/38376581915), Ephemeral DAST [38376581913](https://github.com/ijoolaie/AI-Employee/actions/runs/38376581913), Production Infrastructure Validation [38376581909](https://github.com/ijoolaie/AI-Employee/actions/runs/38376581909), and HA Failure Recovery [38376581932](https://github.com/ijoolaie/AI-Employee/actions/runs/38376581932) passed. Desktop/mobile visual-review artifact [11801004004](https://github.com/ijoolaie/AI-Employee/actions/runs/38376582057/artifacts/11801004004) was reviewed; the HUD, joystick, and camera controls do not overlap.
- Post-merge checks on `71755e07660f380116f3c157f3e78e9e1c7f79d6` all passed: [CI 38377667568](https://github.com/ijoolaie/AI-Employee/actions/runs/38377667568), [CodeQL 38377667634](https://github.com/ijoolaie/AI-Employee/actions/runs/38377667634), [Ephemeral DAST 38377667574](https://github.com/ijoolaie/AI-Employee/actions/runs/38377667574), [Production Infrastructure Validation 38377667722](https://github.com/ijoolaie/AI-Employee/actions/runs/38377667722), [Production Compose Validation 38377667804](https://github.com/ijoolaie/AI-Employee/actions/runs/38377667804), [SLO Contract Manual v2 38377667569](https://github.com/ijoolaie/AI-Employee/actions/runs/38377667569), and [Delivery Manifest Bundle 38377667751](https://github.com/ijoolaie/AI-Employee/actions/runs/38377667751).
- Release boundary: this is an engineering UI fix, not a new release certification, production deployment, or customer-acceptance claim. Latest certified release remains `v1.4.17` unless the release ledger is updated by a separate certification.

## Latest exact-main CI checkpoint — 2026-10-13

The manual-dispatch trigger fix is merged and both workflows have now been run on `main` at exact SHA `8cd10f175df4a4f532f3e2d1ea0ac2b6486f2c3d`:

- [CI run 38371564101](https://github.com/ijoolaie/AI-Employee/actions/runs/38371564101) — PASS. Frontend: 143 contract checks, 76 Vitest tests, 10 Playwright tests passed; production build completed. Backend: 1,452 passed, 1 deselected, 22 warnings. [World visual-review artifact 11800165354](https://github.com/ijoolaie/AI-Employee/actions/runs/38371564101/artifacts/11800165354) is available but is not marked visually accepted in this handoff.
- [Architecture Guard run 38371581649](https://github.com/ijoolaie/AI-Employee/actions/runs/38371581649) — PASS. 20 architecture tests passed; final architecture audit and production-completeness baseline PASS.
- Follow-up: triage React hook and Next.js navigation lint warnings; confirm duplicate-key database log entries are expected test output; plan the Node.js 24-compatible action runtime update; investigate the transient first localhost refusal if it recurs.
- These runs validate the exact SHA and tested scope only. They do not certify a new release, prove external deployment or live provider execution, or establish customer acceptance/revenue.

## Current source of truth
- `main` contains PR [#1062](https://github.com/ijoolaie/AI-Employee/pull/1062), merged as `d6e4f9297dbf7122aab22bdf8bbea467a6f8f038`.
- Code head validated before merge: `7dd0a54709a6b8660dc7fb3d32051160ac50fbb2`.
- Exact-head visual artifact: [`world-visual-review-10d00b30be9cfc784398ed8a3c4380328684ee3f`](https://github.com/ijoolaie/AI-Employee/actions/runs/38292198575). The 1440×900 desktop and 390×844 mobile screenshots were inspected.
- All five required workflows passed on that exact source head:
  - [CI / Playwright](https://github.com/ijoolaie/AI-Employee/actions/runs/38292198575)
  - [CodeQL](https://github.com/ijoolaie/AI-Employee/actions/runs/38292198505)
  - [Ephemeral DAST](https://github.com/ijoolaie/AI-Employee/actions/runs/38292198517)
  - [HA Failure Recovery](https://github.com/ijoolaie/AI-Employee/actions/runs/38292198352)
  - [Production Infrastructure Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38292198497)
- PRs #1059 and #1060 were closed as superseded by #1062. Dependency PRs #1063, #1066, #1065 and #1064 were also merged after their exact-head checks passed.
- PR #1072 adds low translucent department glass panels, colored cap rails and repeated mullions; the exact-head screenshot artifact is [CI run 38356980574 / artifact 11793500701](https://github.com/ijoolaie/AI-Employee/actions/runs/38356980574/artifacts/11793500701). The glass partitions do not obscure workstations/employee silhouettes, but the portrait artifact crops the outer right room edge; full mobile framing is not accepted.
- PR #1075 exact head `f316ef147b43eccf5b82a2776dfc4bf124f4b6cf` passed CI, Documentation Truth Consistency, CodeQL, HA Failure Recovery, Production Infrastructure Validation and Ephemeral DAST. The fresh [desktop/portrait artifact](https://github.com/ijoolaie/AI-Employee/actions/runs/38358857827/artifacts/11793314632) was reviewed; the floor now fits in portrait view, and room entrances/tiled zones are visible. The bounded room/floor/portrait-fit slice is visually accepted on the exact code head; the GitHub PR page is authoritative for lifecycle. Role-specific employee art, rigging/animation and full pathfinding remain open.
- Asset reality check: at pre-PR #1076 baseline commit `4805a2eb8358fd64e6784fe07b1337c9553c0059`, the World asset path had no `employee-base.glb` or `GLTFLoader`. PR [#1076](https://github.com/ijoolaie/AI-Employee/pull/1076) is merged as `fc669d9aa6ee32c099a605873cc8ffca8b95b988` from exact PR head `46a7f13ce9c4b8e9f94352f3862539efa14c404e`. All seven exact-head workflow groups passed; the exact-head visual artifact is [11796728540](https://github.com/ijoolaie/AI-Employee/actions/runs/38366530490/artifacts/11796728540), reviewed on desktop and portrait. All nine observed post-merge workflow groups on merge SHA `fc669d9aa6ee32c099a605873cc8ffca8b95b988` passed: [CI](https://github.com/ijoolaie/AI-Employee/actions/runs/38367142780), [CodeQL](https://github.com/ijoolaie/AI-Employee/actions/runs/38367142858), [Architecture Guard](https://github.com/ijoolaie/AI-Employee/actions/runs/38367142938), [Production Infrastructure](https://github.com/ijoolaie/AI-Employee/actions/runs/38367142771), [Production Compose](https://github.com/ijoolaie/AI-Employee/actions/runs/38367143130), [Ephemeral DAST](https://github.com/ijoolaie/AI-Employee/actions/runs/38367142908), [Documentation Truth](https://github.com/ijoolaie/AI-Employee/actions/runs/38367142950), [SLO Contract](https://github.com/ijoolaie/AI-Employee/actions/runs/38367142842), and [Delivery Manifest Bundle](https://github.com/ijoolaie/AI-Employee/actions/runs/38367142859). The GLB is static/unrigged; rigging, animation, role-specific art and full pathfinding remain open. This merge does not certify a production release.
- Release certification is unchanged: latest certified tag remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. The World merge is not a new production release.

## What changed
- Fixed Tailwind scanning to include `frontend/features/**`, which had omitted responsive utility styles from feature components.
- Consolidated the procedural executive avatar, procedural surface materials, camera pan helper and tests, consistent reset/default camera distance, continuous side-wall backing and floor palette correction.
- Reviewed exact-head artifact `world-visual-review-79cf5b031bc4bc4bd12cd60d38dd29753af85a71` from CI run [38298932308](https://github.com/ijoolaie/AI-Employee/actions/runs/38298932308), head `712a687a119aca0f82d3cce9df5aab5d0d53f2e0`: desktop and portrait both show the full office floor inside the viewport. All five required workflows passed for this exact head. Desktop multiplier is 1.85; portrait multiplier is 2.05.
- Mobile camera controls use compact Reset/Full labels in the upper-right; the HUD stays upper-left and joystick stays bottom-left. Pointer cancellation resets movement.
- Extracted ground collision footprints into `frontend/features/world/WorldNavigation.ts`.

## Verification actually present
- Playwright checks mobile HUD/camera/joystick bounds, console/page errors and unexpected HTTP 5xx responses.
- The original canvas-screenshot comparison for pointer drag timed out on software-rendered CI. Follow-up PR #1069 replaces that brittle screenshot comparison with a real pointer-gesture event assertion; `WorldPan` unit tests cover the projection math. This does not by itself certify visual camera movement.
- Existing World E2E coverage checks keyboard movement to locked-room proximity, room offer/renewal flows and server-authorized room access.
- Unit tests cover coffee-table/workstation footprints, walkable aisle space and office bounds.
- Historical note: CI run [38292598819](https://github.com/ijoolaie/AI-Employee/actions/runs/38292598819) failed on an earlier post-merge head. PR #1069 and PR #1071 followed; the final #1071 head `712a687a119aca0f82d3cce9df5aab5d0d53f2e0` subsequently passed all five required workflow groups and its screenshot artifact was reviewed. That validation applies to the merged viewport change, not every future `main` commit.

## Explicit limitations — do not overstate completion
- The base employee body now loads from the local GLB with procedural fallback. The player/CEO avatar remains procedural; the base employee mesh is static and does not provide skeletal animation or role-specific art.
- Collision geometry is a conservative footprint guard with axis-separated sliding; it is not full obstacle-aware pathfinding or arbitrary-route navigation.
- Walk-cycle foot planting and richer authored employee/workstation assets remain follow-up work.
- World remains a read-only projection of authorized business data. Do not invent employees, revenue, orders, approvals, entitlements or room access client-side.

## Next actions
1. PR #1069 is merged; PR #1068 was closed as superseded. The pan smoke now checks pointer-event wiring rather than relying on WebGL canvas screenshots; unit tests cover pan projection math.
2. PR #1071 is merged at `ff3a138a4164c793c06678f9ca9d790ab2c14cd8`; its five exact-head workflow groups passed and viewport screenshots were reviewed. Continue remaining World redesign tasks separately.
3. PR #1073 reconciled release/current-state docs and PR #1074 added the consistency gate and static role audit; both are merged. PR #1075's bounded room/floor/portrait-fit implementation passed exact-head checks and visual review. The GitHub PR page is authoritative for lifecycle; continue with rigging/animation, role-specific art and full obstacle-aware pathfinding.
4. Prioritize authored/licensed character assets with provenance and verified runtime loading, if approved.
5. Design and test obstacle-aware navigation and more comprehensive collision integration tests.
6. Keep release certification separate from World code merges.


## Post-merge verification follow-up — PR #1082 (2026-10-13)

The five post-merge workflows previously listed as running have now completed successfully on merge commit `f1b4f782d8753da6c5f960b50942e9a5a6f16b06`:

- [CI / frontend + backend](https://github.com/ijoolaie/AI-Employee/actions/runs/38378936957) — both jobs passed.
- [Production Compose Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38378937006) — passed.
- [Production Infrastructure Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38378937068) — passed.
- [CodeQL](https://github.com/ijoolaie/AI-Employee/actions/runs/38378937201) — Python and JavaScript/TypeScript analysis passed.
- [Ephemeral DAST](https://github.com/ijoolaie/AI-Employee/actions/runs/38378937394) — passed.

Together with the already-recorded passing post-merge SLO Contract Manual v2 and Delivery Manifest Bundle workflows, these close the post-merge verification checkpoint for #1082. This is workflow evidence for the merge commit only; it does not establish production deployment or a new release certification.

## Next World work — acceptance remains open

Continue Issue [#1044](https://github.com/ijoolaie/AI-Employee/issues/1044) as a separate, reviewable slice. Do not close the issue based on #1082. Next priority is to verify the current employee GLB loader/fallback and animation boundary against the live World route, then address authored asset provenance and obstacle-aware navigation with exact-head desktop/mobile screenshots, console/performance review, and regression checks for selection, touch/keyboard controls, room lock/expiry, tenant-scoped scene access, and reduced motion. Visual acceptance requires review of the actual rendered result; static screenshots alone cannot prove motion behavior.

## Execution-phase progress tracker — 2026-10-13

Percentages below are coarse stage-completion estimates based on the exit criteria in sections A0–A4 and section 8—not code-volume estimates. Overall progress is the unweighted mean of the five stage percentages, rounded to the nearest whole percent. Update these values only when new repository/runtime evidence changes the corresponding acceptance checklist.

| Stage | Progress | Evidence and remaining exit criteria |
|---|---:|---|
| A0 — Reconcile source-of-truth documents and add consistency validation | 100% | PRs #1073/#1074 and the documentation consistency check are recorded as complete. Required-check enforcement on `main` remains a governance follow-up, not a hidden completion claim. |
| A1 — Map every canonical employee role to real execution | 30% | Static source map covers the 12-role workforce catalog. Per-role runtime traces, configured-provider evidence, negative/failure tests, persisted audit review, and acceptance evidence remain incomplete. |
| A2 — Execute priority end-to-end workflows | 15% | Existing local/component E2E evidence covers parts of the product. The defined content, design, marketing, sales, customer-delivery, finance, and developer/operations workflows are not yet all verified end-to-end against their intended real targets. |
| A3 — Satisfy commercial launch gates | 0% | No verified live-provider customer pilot, independent delivery acceptance, and reconciled actual receipts/costs have been evidenced here. |
| A4 — Establish autonomy/reliability acceptance baselines | 0% | Representative supervised-pilot metrics and agreed targets are not established. |
| **Overall execution phase** | **29%** | Equal-weight average: (100 + 30 + 15 + 0 + 0) / 5 = 29%. This is not a claim that 29% of code or product features exist. |

**Current next stage:** continue A1/A2 with the smallest reproducible real-stack acceptance test, beginning by verifying the current-main W8/W23 Customer Success and W9 QA/DevOps workflow results. Do not claim configured provider execution where the test fixtures explicitly say `provider_execution=not_configured`. Commercial readiness and production certification remain separate gates.



## PR #1085 merged — workforce E2E trigger coverage (2026-10-13)

- PR [#1085](https://github.com/ijoolaie/AI-Employee/pull/1085) was squash-merged as `0a6025e6dae1ed473fafdee8f3ca1833f2c27068` from exact PR head `e262faa29fe2a4b05f5109652781c7939434ed4f`.
- Exact-head W9 QA & DevOps real-stack E2E [run 38382195260](https://github.com/ijoolaie/AI-Employee/actions/runs/38382195260) passed, including stack build/start, DB preparation, health check, source compilation and certification step.
- Exact-head W23 Customer Success real-stack E2E [run 38382195369](https://github.com/ijoolaie/AI-Employee/actions/runs/38382195369) passed, including stack build/start, DB preparation, health check, source compilation and verification step.
- Exact-head CodeQL [run 38382195585](https://github.com/ijoolaie/AI-Employee/actions/runs/38382195585) passed.
- Change aligns `pull_request` and `push` path filters for both workforce E2E workflows and includes relevant governance/freshness/license/storage/edition services, models, DB core, dependency lock, backend Dockerfile and Compose dependencies. Manual dispatch remains supported.
- The workflow-run connector returned no post-merge runs for merge SHA at this checkpoint; do not infer post-merge workflow success from exact-head pre-merge checks.
- Important boundary: these are real-stack certification-fixture tests, not proof of live third-party provider execution, customer delivery, revenue, production deployment or release certification. Unconfigured providers must continue to be reported as not configured.
- Execution tracker unchanged: A0 100%, A1 30%, A2 15%, A3 0%, A4 0%, overall 29%. This PR improves test-trigger reliability but does not yet add missing per-role runtime traces or end-to-end business acceptance evidence.


## Progress denominator correction — agent-actionable scope (2026-10-13)

The persistent agent rules in [`AGENTS.md`](../../AGENTS.md) now require separate actionable and full-scope progress figures. A3 (real commercial pilot, actual receipts/costs, independent customer acceptance) and A4 (operational autonomy/reliability baselines dependent on real supervised-pilot data) are excluded from the current actionable denominator only; they remain open and are not treated as complete.

| Stage | Progress | Counting treatment |
|---|---:|---|
| A0 — source-of-truth reconciliation | 100% | Included in actionable denominator |
| A1 — role-to-execution audit | 30% | Included in actionable denominator |
| A2 — end-to-end workflow proof | 15% | Included only for repository/local/available-CI-verifiable criteria; split out any unavailable external-only criterion |
| A3 — commercial pilot | 0% | Excluded from actionable denominator; externally dependent and still open |
| A4 — autonomy/reliability baseline | 0% | Excluded from actionable denominator where it requires real operational/pilot data; still open |
| **Agent-actionable progress** | **48%** | (100 + 30 + 15) / 3 = 48.3%, rounded |
| **Full-scope context** | **29%** | (100 + 30 + 15 + 0 + 0) / 5 = 29% |

Next repo-actionable work: inspect W8/W9/W23 certification scripts and their current-main evidence; distinguish fixture/real-stack verification from live-provider execution; add the smallest missing positive/negative role acceptance tests; record exact SHA/run evidence. External-only queue remains live provider credentials, production deployment, actual customer pilot/acceptance, receipts and costs. GitHub-hosted CI is a server-run engineering check but does not substitute for a customer-controlled server or live third-party integration.
