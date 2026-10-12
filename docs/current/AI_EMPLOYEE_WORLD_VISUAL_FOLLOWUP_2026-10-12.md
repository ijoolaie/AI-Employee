# AI Employee World — Visual Follow-up

**Date:** 2026-10-12  
**Status:** Implementation in progress; visual acceptance remains open  
**Code PR:** [#1059](https://github.com/ijoolaie/AI-Employee/pull/1059)  
**Documentation PR:** [#1058](https://github.com/ijoolaie/AI-Employee/pull/1058)

## Implemented on the current-main follow-up branch

- Replaced the simple player token with a stylized executive character with layered workwear, facial detail, shoes and articulated limbs.
- Added camera-projected ground-plane pan conversion and unit tests for horizontal drag, vertical drag and stationary input.
- Restored the CEO spawn to z=4.4 after tracing two room-proximity Playwright failures to the previous z=3.5 spawn overlapping the lobby coffee-table collision footprint.
- Added deterministic cached procedural wood, fabric and plaster maps to the desk, chair, floor and rear wall. Shared cached maps are preserved across viewport unmounts.
- Preserved current-main movement speed and easing, axis-separated collision checks and camera follow rather than retaining an unverified speed increase.

## Validation evidence

- Commit `c943f86b2f831dfcd47fda9ada6b4a8f88093a85` passed CI including Playwright, CodeQL, production infrastructure validation, HA recovery validation and DAST.
- CI generated desktop (1440×900) and mobile (390×844) runtime screenshots for that commit. These images were inspected manually.
- The latest material-texture commit is `bb5d777b7b07d212ed65578cdabb3a210afcada2`; its exact-head checks and new screenshots must be reviewed before this follow-up can be accepted.

## Visual review findings

- **Desktop:** The HQ layout is coherent and the department platforms, desks and entrance remain readable. The executive is still small relative to the full office view.
- **Mobile:** The scene is usable as a pannable crop, but the rightmost department is clipped at the viewport edge and department labels are too small for confident reading. Treat these as open responsive-framing issues, not visual acceptance.
- **Assets:** Employee models are still procedural. The #1055 PR description says a GLB and provenance manifest were delivered by #1057, but the inspected #1057 diff contains no corresponding asset/manifest changes and current `WorldViewport.tsx` has no GLTF/GLB loader reference. Do not claim authored-model integration until both the asset and runtime loading path are verified.
- **Motion:** The spawn/collision issue is fixed in the source and the next exact-head checks must continue to confirm the room proximity, offer and renewal flows. Full pathfinding and foot planting are not implemented.

## Acceptance gates

1. Latest exact-head CI, Playwright, CodeQL, DAST, HA recovery and infrastructure workflows pass.
2. Inspect the new desktop/mobile screenshot artifacts for the texture change; confirm there is no new visual regression.
3. Improve portrait framing/label readability without hiding the ability to pan the world.
4. Verify an authored/licensed employee asset and runtime loader, or explicitly defer that work.
5. Verify movement start/stop, collision, room proximity, authorized access and expired-access renewal in browser tests.
6. Keep PR #1059 Draft until all required checks pass and the visual gates are reviewed.

## Scope boundary

The World viewport remains a read-only presentation of governed business data. Visual changes must not create employees, revenue, orders, approvals, entitlements or room access client-side. Server authorization remains the only source of truth for the locked room.
