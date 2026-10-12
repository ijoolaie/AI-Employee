# AI Employee World — Visual Redesign V2

**Status:** Design/implementation contract; not evidence of completed visual work.  
**Date:** 2026-10-11  
**Tracking:** Issue #1044; corrective PR #1046 is now based on `main` and contains the combined diff from the earlier #1045 branch plus V2 corrections, so repository pull-request workflows can validate it.  
**Current decision:** PR #1045 remains Draft and must not be merged as visual approval. The user ran the earlier build locally and rejected the result: the office still looks primitive, employee faces do not match the approved reference direction, movement looks unnatural, and props are placed incoherently. PR #1046 also remains Draft and unmerged.

## Outcome we are building toward

A polished, stylized isometric 3D office-management game presentation: readable silhouettes, expressive friendly employees, intentional room composition, coherent furniture scale, soft contact shadows, warm/cool lighting, and smooth purposeful animation. Idle Company Tycoon / Agent Office are art-direction references only; do not copy their proprietary models, textures, code, UI, or exact layouts.

## Diagnosis from the current implementation

The current `frontend/features/world/WorldViewport.tsx` builds most objects from primitive `BoxGeometry`, `SphereGeometry`, and `CylinderGeometry`. Adding more primitives and color accents did not produce the requested character art or environmental detail.

- `addWorker` builds the face/hair/outfit from separate primitive meshes. Variation is largely deterministic palette/shape variation, not a designed character model with a coherent silhouette.
- Initial diagnosis before the V2 corrective commits: `addCEOAvatar` used a capsule/body plus simple shapes and had no coordinated walk-cycle rig. V2 now adds articulated pivots and a basic time-based walk cycle, but this has not been visually validated and does not establish foot planting or natural weight transfer.
- V2 adds movement easing and smoother facing/camera follow. Collision-aware navigation/pathfinding is still absent, so the avatar can still approach or cross obstacles unnaturally.
- V2 arranges 20 desk/chair assemblies in a 2×2 grid per department and maps the first 20 worker anchors to those stations. The layout is still hard-coded and has no automated validation for bounds, overlap, aisle clearance, or duplicate occupancy. Employees beyond 20 are placed in an unlabelled staging row; that is not an accepted final capacity design.
- The scene is composed from hard-coded coordinates and independent decorative additions, so props can overlap circulation areas or be visually unrelated to the room function.

## Implementation sequence

### V2-A — Establish a repeatable visual baseline

- Capture actual browser screenshots from the running PR build at desktop and mobile sizes before further art changes.
- Record camera framing, visible scene bounds, employee count, console errors, frame-time/performance baseline, and a list of visible overlap/clipping defects.
- Use the same camera, viewport sizes, and employee fixtures for each comparison. Automated CI is not visual approval.

### V2-B — Replace ad-hoc placement with a scene layout model

- Define explicit room/department bounds, desk anchors, chair anchors, employee work anchors, wall/door/window zones, decoration zones, and walkable navigation cells.
- Place each workstation as a coordinated desk + chair + monitor + accessories assembly. A worker's seated anchor and facing direction must be derived from its workstation, not from array index arithmetic.
- Add placement validation for bounds, overlap, walkways, door access, and duplicate occupancy. Invalid placements must be omitted or surfaced in development diagnostics rather than silently rendered.
- Ensure extra employees do not spawn inside desks, walls, plants, or other workers. Overflow must use an intentional additional workspace or a clearly represented capacity state.

### V2-C — Establish a coherent art asset pipeline

- Prefer authored, reusable low-poly/stylized GLTF assets for character bodies, hair, faces, chairs, desks, plants, and room props where the repository's asset/licensing/performance constraints permit.
- Keep procedural geometry only for small status indicators, simple accents, and placeholders. Do not claim primitive-built heads are equivalent to the approved reference characters.
- Use a consistent art bible: proportions, bevel language, material roughness, palette, face scale/eye placement, texture resolution, shadow softness, and camera angle.
- Keep original or properly licensed assets only; document provenance and license. No extracted assets from commercial games.
- If external asset downloads or model authoring tools are unavailable, explicitly report the limitation and deliver a clearly labelled prototype—not a claim of reference-level fidelity.

### V2-D — Character model and animation

- Create a reusable character hierarchy with torso, head, upper/lower arms, hands, thighs, lower legs, and feet as separate articulated parts or a skinned GLTF rig.
- Use a proper idle and walk cycle. Walking requires alternating leg/arm swing, body bob/weight shift, foot placement, and facing direction consistent with movement. Smooth start/stop and prevent large frame deltas from causing teleport-like steps.
- Use a navigation/pathfinding layer around obstacles; no walking through desks, chairs, walls, or other employees. When no valid path exists, stop and expose a blocked/idle state.
- Respect `prefers-reduced-motion`, pause cleanly when the tab is hidden, and keep animation work within the project's laptop/mobile performance budget.
- The CEO avatar and employee characters must share the same visual language and rig conventions.

### V2-E — Compose, light, and polish the office

- Design a deliberate focal hierarchy: reception/entry, department work areas, collaboration zone, circulation, and perimeter architecture.
- Every object must have a functional or compositional reason to be there. Keep walkways and doorways clear; group accessories with their desks; align chairs to desks; keep plants/decor out of work and movement zones.
- Use layered materials, restrained bevels, contact shadows, ambient occlusion only if affordable, and intentional warm key/cool fill lighting. Avoid relying on emissive rectangles and extra trim as a substitute for asset quality.
- Test the scene at the actual intended camera distance and at mobile scale; faces, labels, and interaction targets must remain legible without clutter.

## Acceptance gates (all required before #1045 or successor can be marked ready)

1. **Visual evidence:** before/after screenshots from the actual running browser build at desktop (1440×900) and mobile (390×844), same camera and fixture data; no concept renders presented as runtime screenshots.
2. **Character quality:** at least 4 visibly distinct, coherent character appearances; recognizable facial features at normal game zoom; no floating facial features, intersecting hair, or disconnected accessories.
3. **Motion:** visible walk cycle with alternating limbs and planted-looking steps; smooth direction changes and start/stop; no sliding-only translation; reduced-motion behavior verified.
4. **Layout:** no furniture/character intersections, no blocked main aisles/doorways, workers align with their assigned desks, no arbitrary overflow rows.
5. **Interaction regressions:** employee selection, keyboard/touch movement, camera controls, room access and lease expiry remain functional.
6. **Runtime quality:** no new console errors; check renderer/resource cleanup and performance on the project's target laptop and a narrow viewport.
7. **Automated validation:** lint, unit/contracts, build, and relevant World interaction tests pass on the exact final commit.
8. **Honest scope:** if only one gate is incomplete, PR remains Draft and lists the missing evidence. CI success alone never means art direction was accepted.

## Work order

1. Capture and inspect the real current runtime.
2. Implement layout anchors/validation and remove invalid placement patterns.
3. Introduce one approved character asset/rig and validate it in-scene before scaling to a cast.
4. Implement walk/idle animation and obstacle-aware movement.
5. Replace the most visible primitive props and refine lighting/materials.
6. Capture comparison screenshots, run regressions, update the master handoff, and request user review.

Do not merge or certify this work without explicit user approval after the visual evidence is reviewed.

## 2026-10-11 implementation follow-up

- Corrected two visible layout collisions in the current procedural scene: department planters were placed beside the second desk/chair approach, and the left lobby planter nearly touched the sofa. Planters now use the rear-right corner of each department and the lobby planters sit outside the reception/sofa footprint.
- Made the locked-room Playwright regression wait for the actual proximity affordance while movement is held, rather than stopping after a fixed 900 ms. The movement change uses acceleration/easing, so a fixed short hold was brittle.
- Exact-head CI is running for the follow-up commit. These changes are source-level corrections only; they do **not** establish that the scene has been visually approved. No real-browser screenshot/video has been captured from this session, and the cast/furniture still uses procedural primitives rather than authored GLTF assets. Keep both visual PRs Draft pending visual evidence and the remaining redesign work.

## 2026-10-11 additional source corrections

- Reworked the department workstations into a compact 2×2 grid (four actual desk/chair assemblies per department, 20 authored stations total). Each seated worker anchor now corresponds to a station coordinate instead of the previous arrangement where the second desk could sit in front of the first desk's chair.
- Employees beyond the 20 authored stations are placed in a separate staging row rather than being silently stacked into the desk grid. This fallback is not visually designed or labelled yet and still needs a capacity indicator.
- Improved procedural face readability with iris color variation, eye catchlights, and a curved smile. This is a small source-level refinement, **not** a replacement for authored character assets or proof that the approved reference has been matched.
- Workflow lookup did not return runs for the latest branch head after these follow-up commits. The exact latest head remains unverified by CI, and no real-browser screenshot/video is available in this session. Keep the PR Draft and do not merge.


## 2026-10-11 PR validation routing correction

- PR #1046 was retargeted from `feat/world-visual-polish-1044` to `main` because `.github/workflows/ci.yml` and `.github/workflows/codeql.yml` restrict pull-request base branches. The prior base was excluded, so no workflow run for the latest head was not a passing result.
- PR #1046 now compares 18 commits against `main` and includes four changed files: `docs/00_START_HERE/CURRENT_PRIORITIES.md`, this contract, `frontend/e2e/world-mode.spec.ts`, and `frontend/features/world/WorldViewport.tsx`. This is a combined successor diff; inspect it as a whole.
- The exact head `6185fcdb8c62f223f3391fb52474a90fb1929145` subsequently completed all five reported PR workflows successfully: CI, CodeQL, Production Infrastructure Validation, HA Failure Recovery Validation, and Ephemeral DAST Validation. This certifies those automated checks for that exact source head only; it does not establish visual quality or manual-browser correctness. Any subsequent code change requires fresh checks.
- This session has no access to the user's local Windows browser/runtime, so it has not captured or verified actual desktop/mobile screenshots. Keep the PR Draft until exact-head checks and real visual evidence are available.


## 2026-10-12 reconciliation after PR #1057 merged

- Current `main` is at merge commit `de053b24d045d17d0e447e29140cfd4728ade4c8` for PR #1057. The warmer palette, window blinds, responsive viewport changes, and an employee GLB asset plus attribution/license information are present in that merged history.
- PR #1055 is the remaining open follow-up found by repository search. Its head `004530abe6628d477a925cc1026f3b043f4c4280` is diverged from current main (14 commits ahead, 2 behind) and screenshots described by the PR show top-left overlay overlap and clipped room labels. Do not merge it without reconciling its unique changes and refreshing evidence.
- Runtime asset caveat: current `frontend/features/world/WorldViewport.tsx` still creates ordinary employees in `addWorker` from primitive meshes and has no GLTF/GLB loader reference. Verify if another route/component uses the GLB; if not, asset presence alone does not meet the authored-character acceptance gate.
- Revised work order: (1) port the unique pan projection utility/tests and executive avatar/movement changes onto current main; (2) fix label/HUD clipping; (3) verify or wire GLB runtime loading with loading/error fallback and resource disposal; (4) implement obstacle-aware navigation and validated workstation/overflow placement; (5) exact-head CI plus actual desktop/mobile screenshots and human review.
- Keep visual acceptance open until the acceptance gates above are met. Green CI and the presence of an asset file are not visual approval.

---


## Latest execution update — 2026-10-12, PR #1059 opened from current main

- PR [#1059](https://github.com/ijoolaie/AI-Employee/pull/1059) was created from current main (`de053b24d045d17d0e447e29140cfd4728ade4c8`) to port the unique camera-pan and executive-motion changes from the diverged #1055 without carrying its stale branch history.
- #1059 includes the tailored articulated executive avatar, camera-projected ground-plane pan utility with unit tests, more responsive time-based movement while preserving current-main axis-separated furniture collision checks, smoother camera follow, walk-cycle cadence adjustment, and cached-texture cleanup protection.
- Latest exact head checked in this pass: `05e6bee5534a242bb567f00e6c7ab7e24cb2d660`. At check time, HA recovery was in progress, CodeQL queued, and CI / infrastructure / DAST pending. No test result is claimed until these runs finish.
- #1055 remains stale/diverged until #1059's unique scope and checks are reviewed. Its earlier green checks are not transferable to #1059. Once the new branch's complete diff is verified, close #1055 as superseded to prevent competing branches.
- Current-main `WorldViewport.tsx` still has no GLTF/GLB loader reference for regular employee characters. Confirm actual runtime usage of the GLB asset before calling employee asset integration complete.
- Remaining gates: fix and review actual desktop/mobile overlay and label clipping; verify employee asset runtime loading/fallback/disposal; implement obstacle-aware navigation and intentional overflow handling; review walk quality/reduced motion; pass exact-head checks and inspect the screenshot artifact.

---
