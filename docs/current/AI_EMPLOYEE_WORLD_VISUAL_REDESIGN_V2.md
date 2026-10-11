# AI Employee World — Visual Redesign V2

**Status:** Design/implementation contract; not evidence of completed visual work.  
**Date:** 2026-10-11  
**Parent work:** PR #1045 / issue #1044  
**Current decision:** Keep #1045 Draft and do not merge based on CI alone. The user ran the build locally and rejected the visual result: the office still looks primitive, employee faces do not match the approved reference direction, movement looks unnatural, and props are placed incoherently.

## Outcome we are building toward

A polished, stylized isometric 3D office-management game presentation: readable silhouettes, expressive friendly employees, intentional room composition, coherent furniture scale, soft contact shadows, warm/cool lighting, and smooth purposeful animation. Idle Company Tycoon / Agent Office are art-direction references only; do not copy their proprietary models, textures, code, UI, or exact layouts.

## Diagnosis from the current implementation

The current `frontend/features/world/WorldViewport.tsx` builds most objects from primitive `BoxGeometry`, `SphereGeometry`, and `CylinderGeometry`. Adding more primitives and color accents did not produce the requested character art or environmental detail.

- `addWorker` builds the face/hair/outfit from separate primitive meshes. Variation is largely deterministic palette/shape variation, not a designed character model with a coherent silhouette.
- `addCEOAvatar` is a capsule/body plus a few simple shapes and has no walk-cycle rig.
- The input loop translates the CEO avatar by changing its position and rotation. It does not animate coordinated legs/arms, foot planting, body weight, acceleration, deceleration, or collision-aware navigation; visually this can read as sliding.
- Employee workstation positions are generated from a fixed list and overflow rows. This does not validate chair/desk occupancy, aisle clearance, collisions, or whether a worker's pose aligns with the keyboard.
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
