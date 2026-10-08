# AI Company World — F0–F7 Implementation Record

**Status:** IMPLEMENTED IN ENGINEERING BRANCH — local-first validation required before merge  
**Branch:** `feat/f2-world-authoritative-state`  
**Base:** `main` at `f45f8220c329813f9d642162e30fc7e6689adf1b`  
**Release boundary:** This work is post-`v1.4.17` engineering work and does not inherit the certified release claim.

## Purpose

This record is the implementation authority for the World Mode product track:

`Customer Shell → World Mode → HQ → real workforce → management bridge → recorded outcomes → authoritative progression → live state → responsive/polished UX`

The World is a presentation and navigation surface over existing governed backend truth. It is **not** a second workflow engine, employee database, metrics store, entitlement system, or AI runtime.

## Architecture

```
Customer Application Shell
├── Management Mode
└── World Mode
    ├── WorldShell                 # orchestration only
    ├── WorldState                 # pure read-model projection
    ├── WorldViewport              # rendering + camera/input adapter
    ├── WorldInput                 # desktop/mobile input normalization
    ├── WorldEmployeePanel         # employee interaction surface
    ├── WorldProgressionPanel      # authoritative capacity presentation
    ├── WorldOutcomePanel          # recorded ROI evidence
    ├── WorldStatusBar             # live state visibility
    └── WorldMiniMap               # presentation-only navigation aid
```

### Authority rules

1. Backend remains the source of business truth.
2. `getCustomerOffice()` remains the authoritative World workforce read model.
3. `getROIAnalytics()` remains the authoritative outcome read model.
4. No World component may create or mutate business state directly.
5. World projection must be pure and deterministic.
6. Presentation-only metadata must never become authorization or quota logic.
7. If authoritative data is unavailable, the UI fails closed rather than inventing values.
8. Department locations are visual zones only because the current office contract does not expose authoritative employee department/location ownership.
9. Employee presentation states are restricted to the states supported by the existing office contract.
10. No proprietary game assets, maps, branding, or copied code are used.

## Phase record

### F0 — Dual-mode shell
**Implemented:** PR #960.

- Added `/world`.
- Added Management ↔ World mode switching.
- Preserved existing authentication and Management sidebar.
- World shell contains no fabricated business data.

### F1 — Renderer / camera / input
**Implemented foundation:** PR #961 and continued in this branch.

- Deterministic isometric HQ map.
- Camera pan and bounded zoom.
- WASD / Arrow movement.
- Mouse/touch drag camera movement.
- Mobile joystick.
- Touch pinch zoom.
- Accessible zoom/reset controls.
- `M` toggles the presentation-only mini map.
- Camera and input behavior are isolated from business state.

**Renderer decision:** The original architecture selected PixiJS as the long-term renderer. The current implementation deliberately keeps the rendering boundary isolated so the renderer can be swapped without changing the read-model, interaction, or business layers. The current branch uses the browser Canvas renderer while dependency/lockfile installation is validated in the local environment. F1 must not be called production-complete until the local dependency/build validation confirms the chosen renderer path.

### F2 — Real HQ projection
**Implemented in PR #962 branch.**

- Existing tenant-scoped `/customer-dashboard/office` data is projected into World.
- Real employees appear in the world.
- Real presentation state follows the backend.
- Current work item and latest run are visible.
- Unknown presentation states fail closed to `IDLE`.
- No second operational state store exists.

### F3 — World ↔ Management bridge
**Implemented.**

- Selecting an employee opens an authoritative employee panel.
- Employee panel links to existing `/employees/{id}` management view.
- `Esc` closes the interaction.
- World never duplicates employee management functionality.

### F4 — Business outcome loop
**Implemented.**

- World consumes existing `/analytics/roi`.
- Displays recorded conversations, AI resolutions, orders and influenced revenue when available.
- Empty/unavailable outcome data is explicitly shown as unavailable.
- No revenue, productivity or ROI is estimated inside World.

### F5 — Company progression
**Implemented as authoritative capacity presentation.**

Progression is derived only from existing HQ subscription/usage fields:

- HQ tier;
- active employees / employee limit;
- active workflows / workflow limit;
- monthly runs / monthly run limit;
- deterministic capacity utilization index.

There is no invented XP, coins, idle income, happiness score, or gameplay economy.

### F6 — Living World
**Implemented.**

- Office state refreshes every 5 seconds.
- ROI state refreshes every 15 seconds.
- Employee state changes therefore originate from real backend changes.
- Live status bar reports the states actually present in the read model.
- Generated timestamp is displayed as the source freshness marker.
- No timer fabricates activity transitions.

### F7 — Product polish
**Implemented foundation.**

- Responsive desktop/mobile shell.
- Keyboard and pointer navigation.
- Mobile joystick and pinch zoom.
- Accessible camera controls.
- Keyboard mini-map toggle.
- Explicit loading/error states.
- Reduced-motion-safe approach: no decorative animation is required for business state.
- WorldShell is kept as orchestration; rendering, state projection, input, panels and progression are separate modules.

## Anti-spaghetti rules

### Dependency direction

```
WorldShell
  ↓
World UI components
  ↓
WorldState / WorldInput / WorldCamera
  ↓
existing frontend API facade
  ↓
existing backend read models
```

World components must not import backend service code, database code, Celery tasks, provider SDKs, or direct execution paths.

### State ownership

- Server/business state: backend.
- Query cache: TanStack Query.
- World presentation state: local React state only.
- Camera state: `WorldCamera`.
- Input state: `WorldInput`.
- Derived world read model: pure `projectWorldReadModel()`.

Do not introduce a global Zustand store for World business state unless a demonstrated cross-route requirement exists.

### Forbidden shortcuts

- duplicated employee records;
- fake revenue;
- fake task timers;
- fake employee activity;
- World-specific execution endpoints;
- direct provider calls from World;
- authorization based on visual HQ tier;
- hard-coded tenant-specific employees;
- unbounded component files that mix rendering, data fetching and business rules.

## Validation contract

Before merge, run the existing frontend validation sequence on the exact branch SHA:

1. frontend contract tests;
2. governance contract tests;
3. World unit tests;
4. lint/typecheck/build;
5. Playwright World shell checks (the CI frontend job now runs the dedicated `e2e/world-mode.spec.ts` smoke);
6. local real-stack smoke with the existing LM Studio setup;
7. verify Management Mode remains unchanged;
8. verify World employee state changes follow the existing office API;
9. verify no second AI execution path exists.

**Certification boundary:** these are engineering/local evidence only. They do not modify or extend the immutable `v1.4.17` Production Certification.

## Known deliberate limitation

The current backend office contract does not expose authoritative employee department/location coordinates. Therefore the World uses deterministic presentation zones and slots without claiming that those are real employee locations. A future backend contract may add department/location metadata; the World projection layer is intentionally isolated so that enhancement can be made without rewriting rendering or interaction code.
