## User-approved World visual direction — 2026-10-12

- The user supplied a current desktop AI Company HQ screenshot and a target mobile office-tycoon screenshot. The target direction is now documented in the canonical [AI Company World & Gameplay Specification, §30](../blueprint/AI_COMPANY_WORLD_GAMEPLAY_SPEC.md#30-approved-visual-reference--office-management-tycoon-presentation-2026-10-12).
- Visual target: polished 3/4 isometric office; warm cream walls and coral/terracotta floors; teal/blue partitions; windows/blinds, doors, wall decor, detailed workstations; varied original/licensed stylized employees; soft shadows; compact, readable responsive HUD.
- This is a visual direction, not permission to copy proprietary art, exact UI, maps, characters or source. Preserve AI-Employee's department model and enterprise semantics.
- Priority order: scene composition/legibility → authored/licensed employee and workstation art → obstacle-aware navigation → mobile HUD/accessibility → actual desktop/mobile screenshot review.
- No fictional coins/gems/energy/income, fabricated activity or ungrounded employee placement. Backend state, tenant isolation, room access and approval semantics remain authoritative.
- PR #1050 remains Draft/unmerged until the user-approved art direction is implemented and visually accepted. Existing green workflows do not constitute visual acceptance or release certification.

---
## Current engineering status — 2026-10-12, World V2 visual-review checkpoint

- PR [#1050](https://github.com/ijoolaie/AI-Employee/pull/1050) is open, Draft and unmerged on current `main`, exact head `8a7de75a8d49b4e1489b00353615f7a1f3808f87`. All five exact-head workflows passed: [CI](https://github.com/ijoolaie/AI-Employee/actions/runs/38213177840), [CodeQL](https://github.com/ijoolaie/AI-Employee/actions/runs/38213177820), [Production Infrastructure Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38213177945), [HA Failure Recovery Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38213177822), and [Ephemeral DAST Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38213177856).
- CI artifact `world-visual-review-1e43f2d0cd75d04671bf8b71d9e7f54f848f15ef` contains real Playwright desktop (1440×900) and mobile (390×844) viewport screenshots. Camera framing and mobile overlay collisions were corrected on this exact head.
- Visual acceptance remains open: character/furniture art is mostly procedural, mobile labels are small, and collision checks are static rather than full pathfinding. Keep #1050 Draft and unmerged until the visual direction and remaining gaps are addressed.
- PR #1046 is closed unmerged as superseded; #1045 is closed unmerged after user rejection. PRs #1040, #1041, #1042, #1047, #1048, #1049 and #1051 are merged as recorded below.
- Latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`; engineering checks do not certify a new production release.

## Current engineering status — 2026-10-11, after PR #1041 and #1042 merges

- PR #1041 merged to main at `e1633e9bf000af045e2571d930b4eeefec30883f`. The exact PR head `528750ce9fbac51690d3da6a660394ed6896cbb8` passed CI, CodeQL, Production Infrastructure Validation, HA Failure Recovery Validation, and Ephemeral DAST. Expired room access remains server-authoritative and fail-closed; renewal creates an order and does not activate access by itself.
- PR #1042 merged to main at `cd1f218469d913e4e586e8a0c29b00dbb9d246ad`. Exact head `4bebbdcdce78dc5e43276cbaa7aac9136c5fdf4e` passed all 11 workflows; backend suite 1452 passed, 1 deselected; Docker build succeeded; 13 support-message tests and the real PostgreSQL + HTTP API race regression (1 passed) succeeded. The attachment uniqueness race now returns a stable conflict and rolls back the message/attachment transaction together.
- PR #1040 merged at `467e6266540cd429b6e4156ac1a3f9ca00d96759`; CodeQL passed on its final PR head before merge.
- PR #1045 was closed unmerged as user-rejected/superseded. PR #1046 remains Draft and unmerged: all five exact-head automated workflows passed on `7f456bda345053e3ff2caf7697a1bc2a36199b19`, but actual desktop/mobile screenshots and user visual acceptance are still missing. Most characters/furniture remain primitive-built; obstacle-aware pathfinding is not implemented.
- Remaining acceptance: manually test support create → reload → reply/thread → authorized attachment download and tenant-denial cases; run actual World desktop/mobile visual QA and inspect movement, layout, console and accessibility. Issue #1043 tracks the missing customer-tenant support entry point; issue #1044 tracks the visual redesign.
- Do not treat engineering merges or green CI as production release certification. Latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
