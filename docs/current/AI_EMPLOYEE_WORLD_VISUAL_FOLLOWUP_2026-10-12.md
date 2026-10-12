# AI Employee World — Visual Follow-up

**Date:** 2026-10-12  
**Status:** Draft implementation; not visually accepted  
**Branch:** `feat/world-visual-followup-main`

## Delivered in this slice

- Pointer panning converts screen-space drag through the camera's projected ground-plane axes, with sensitivity scaled to camera distance and viewport height.
- CEO movement uses time-based target velocity at 6.2 world units/second, eased acceleration/deceleration, smooth facing and camera follow, plus an articulated low-poly walk cycle.
- The CEO procedural model now has a more coherent executive silhouette: jacket/shirt/tie layers, lapels, pocket accent, styled hair, facial details, trouser legs and shoes.
- Cached deterministic canvas textures add restrained grain to wood, fabric and plaster surfaces without downloading external assets.
- Unit tests cover pointer projection. Playwright captures runtime screenshots at desktop (1440×900) and mobile (390×844); CI uploads the PNGs as an artifact.

## Explicit limitations

- These are source-level procedural improvements. They do not constitute an authored/licensed GLTF/GLB pipeline and do not meet the final art target by themselves.
- Procedural surfaces are interim maps, not calibrated PBR texture sets.
- Movement still has no route-finding or foot-planting solution; collision and natural gait need further work.
- Automated screenshots are review evidence, not an automated visual quality verdict.

## Acceptance gates

1. Exact-head CI passes, including lint, unit tests, production build and World Playwright regressions.
2. Downloadable desktop/mobile screenshot artifacts exist for this exact head and are reviewed for framing, clipping, character readability and material quality.
3. Pointer drag direction and sensitivity, CEO movement speed, start/stop and reduced-motion behavior are checked in a real browser.
4. Only then decide whether to merge. Keep Draft if any gate is incomplete.

## CI findings and fixes — 2026-10-12

- First CI run exposed a strict unit-test mismatch: stationary pointer deltas produced JavaScript negative zero (`-0`). Normalized zero values in `WorldPan.ts`.
- The production build also exposed that this repository's current Three.js declarations do not export the type names used by the new annotations. Replaced those annotations with compatible structural/loose types while preserving runtime constructors.
- That CI run therefore **failed** and produced no screenshot artifacts; do not treat it as accepted evidence. The fixes are now committed on the same branch. A fresh CI run for the latest head must pass before review continues.
