# AI Employee World — Master Handoff

**Updated:** 2026-10-09  
**Repository:** `ijoolaie/AI-Employee`  
**Working branch:** `feat/world-3d-office`  
**Pull request:** [#983 — stylized 3D AI office](https://github.com/ijoolaie/AI-Employee/pull/983)  
**Base:** `main`  
**Workflow rule:** keep the PR open and Draft; do not merge or mark ready without explicit approval.

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
| `4107c4d75cbfc0313c71b6d5165423256197a0c7` | Model document window in input lifecycle test |

The branch has also accumulated visual refinements to character proportions, desk alignment, hands/keyboard alignment, reduced motion and background rendering. See the PR commit history for the complete audit trail.

## 4. Latest CI evidence and current gate

For commit `4107c4d75cbfc0313c71b6d5165423256197a0c7`, the observed workflow results are:

| Check | Result | Evidence |
|---|---|---|
| CI | **Failed** | [Run 37951309925](https://github.com/ijoolaie/AI-Employee/actions/runs/37951309925) |
| CodeQL | Passed | [Run 37951309858](https://github.com/ijoolaie/AI-Employee/actions/runs/37951309858) |
| HA Failure Recovery Validation | Passed | [Run 37951310035](https://github.com/ijoolaie/AI-Employee/actions/runs/37951310035) |
| Ephemeral DAST Validation | Passed | [Run 37951309993](https://github.com/ijoolaie/AI-Employee/actions/runs/37951309993) |
| Production Infrastructure Validation | Passed | [Run 37951309920](https://github.com/ijoolaie/AI-Employee/actions/runs/37951309920) |

### CI failure diagnosis

The frontend lint and contract tests passed; backend validation and backend tests passed. Frontend unit tests reported 37 passed and 1 failed out of 38. The failing test was the focus-loss regression in `world-input.test.ts`; the runner reported `ReferenceError: KeyboardEvent is not defined`. The production build and Playwright smoke stages were skipped after the unit-test failure.

The current branch file content has since been observed using a plain `Event("keydown")` with a defined `key` property, rather than relying on a global `KeyboardEvent`. However, **that content is not yet certified by a successful CI run**. The next step is to ensure the exact branch head includes this test-environment-safe implementation, push a new commit if needed, and verify the entire CI workflow on that exact SHA.

## 5. Immediate next actions

1. Reconcile the exact branch head and the contents used by the failed CI run.
2. Ensure the focus-loss test constructs keyboard input without relying on browser globals, while still verifying that `w` sets `moveY = -1` and blur resets movement to zero.
3. Run frontend unit tests, lint, production build and World Mode Playwright smoke through CI.
4. Inspect all five workflow results for the same exact head SHA; do not infer a pass from an earlier commit.
5. Update this handoff and the PR description with the verified SHA and links to the final results.
6. Keep PR #983 open and Draft. Do not merge or mark ready for review without explicit authorization.

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
