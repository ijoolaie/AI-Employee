# Master Hand-off — AI Employee / AI Company Platform

Date: 2026-10-08
Status: ACTIVE LOCAL-FIRST HAND-OFF
Repository: ijoolaie/AI-Employee
Current implementation branch: docs/frontend-world-audit

## 1. Purpose

This document is the single hand-off point for the next implementation phase.

It consolidates the current product direction, architecture decisions, verified runtime boundaries, frontend transformation plan, workforce roadmap, local execution rules, acceptance gates, and explicit non-goals.

A future engineer/agent should be able to start from this document without reconstructing the strategy from scattered conversations or historical documents.

This hand-off is intentionally implementation-oriented. It is not a production certification.

---

## 2. Non-negotiable execution boundary

The immediate target is a real, usable product running locally on the developer machine.

Do not start external production deployment, live payment execution, live provider integrations, DAST/HA/DR production exercises, commercial go-live, or external on-call work as part of this phase.

Local-first means:

- run the real application stack locally;
- use PostgreSQL and Redis;
- use the real frontend/API/worker path;
- use LM Studio as the local AI provider;
- preserve the governed backend as the source of truth;
- prove behavior with local real-stack evidence;
- do not call local evidence external production certification.

Do not alter the certified v1.4.17 baseline merely to make the new World UI fit.

Any application-code change must be justified by a concrete local requirement or observed failure.

---

## 3. Certified baseline and current truth

### Certified release

- Release: v1.4.17
- Certified SHA: b403c0dcdea579e017738a6fdea138c2b1a2999c
- Certification Run: 37625345534
- Job: 112805570856
- Product Gate failures: 0
- Evidence artifact: production-certification-evidence-v1.4.17-b403c0dcdea579e017738a6fdea138c2b1a2999c
- Evidence SHA-256: c05d9ba79e135dfb64ffd7aed89e2fd36b1ebcb53f6ef2ddfb865e516b870e3d
- Tag v1.4.17 points to the certified SHA.

The certified release remains immutable. Post-release mainline work is not automatically certified.

### Current frontend documentation work

- PR #958: canonical AI Company World gameplay/design specification.
- PR #959: frontend audit and Workforce roadmap reconciliation.
- Current branch for this hand-off: `docs/frontend-world-audit`.

These documentation changes do not themselves certify the World implementation.

---

## 4. Product north star

The product is not merely an AI-agent dashboard.

The target product is:

> AI Company Platform = Management Mode + Explorable AI Company World

The customer should be able to operate a real AI workforce through a conventional SaaS interface and also enter a visual company HQ where the same real employees, work, approvals and business activity are represented.

North-star outcome:

> Build an AI Company that measurably creates time and money for a small business.

The visual World is a representation and interaction layer over the governed platform. It is not a second backend, a separate simulation engine, or an arcade economy.

---

## 5. Two-mode product model

### Management Mode

Keep the existing professional SaaS experience:

- Dashboard
- Customers
- Sales
- Orders
- Employees
- Work
- Finance
- Analytics
- Workflows
- Governance
- Developer
- Settings

Existing authenticated customer layout, API client, React Query, domain routes and governance remain reusable.

### World Mode

Add an explorable AI Company HQ:

- World viewport
- isometric 2.5D map
- camera
- desktop/mobile input
- buildings/departments
- real employee avatars
- interaction targets
- compact HUD
- contextual overlays
- navigation/collision foundation

The user switches modes without changing tenant, session or backend authority.

---

## 6. Current frontend foundation

The existing `/office` route is valuable and must not be thrown away.

It already consumes authoritative customer-dashboard data and exposes:

- HQ tier;
- subscription/capacity;
- employee/workload counts;
- employee presentation states;
- current WorkItem;
- latest Run;
- approvals.

Therefore:

`/office` is the read-model foundation for World Mode, not the final World UI.

The transformation is incremental:

SaaS Dashboard + Virtual Office
→ Management Mode + Explorable World Mode.

Do not rewrite the customer application shell merely to introduce the World.

---

## 7. Target frontend architecture

```
Customer Application Shell
├── Management Mode
│   ├── Dashboard
│   ├── Customers
│   ├── Sales
│   ├── Orders
│   ├── Employees
│   ├── Work
│   ├── Finance
│   ├── Analytics
│   ├── Workflows
│   └── Governance / Developer
└── World Mode
    ├── WorldShell
    ├── WorldViewport
    ├── WorldCamera
    ├── WorldInput
    │   ├── DesktopInputAdapter
    │   └── MobileInputAdapter
    ├── WorldMap
    ├── Buildings
    ├── Departments
    ├── Employees
    ├── Interactions
    ├── Navigation / Collision
    ├── WorldHUD
    └── WorldOverlays
```

Suggested boundary:

```
frontend/
  app/
    (customer)/
      world/
        page.tsx
  features/
    world/
      WorldShell.tsx
      WorldViewport.tsx
      WorldHud.tsx
      WorldCamera.ts
      WorldInput.ts
      DesktopInputAdapter.ts
      MobileInputAdapter.ts
      WorldInteraction.ts
      WorldState.ts
      worldTypes.ts
      map/
      buildings/
      employees/
      departments/
      overlays/
  components/
    mode-switch/
```

Do not move existing Management Mode features into `features/world`.

---

## 8. Renderer decision

Use PixiJS for the first World implementation.

Reason:

- the reference experience is isometric/2.5D rather than dependent on true 3D;
- Next.js/React remains the application shell;
- PixiJS provides an appropriate interactive canvas;
- React remains responsible for forms, panels and business UI;
- mobile performance is easier to control;
- architectural disruption stays low.

Do not introduce Three.js, full 3D, VR or a separate game engine unless a later evidence-backed requirement makes it necessary.

---

## 9. Backend truth and World read model

The World must never invent business truth.

Initial World read model:

- hqTier
- subscription/capacity
- departments
- employees:
  - id
  - name
  - avatar
  - presentationState
  - currentWorkItem
  - latestRun
- approvals
- workItems
- customer/activity summaries where authoritative
- generation timestamp

Initial employee presentation states:

- IDLE
- WORKING
- WAITING_APPROVAL
- BLOCKED
- ESCALATED
- COMPLETED

Do not create MEETING or similar animations without an authoritative backend/session source.

No fake revenue, productivity, customer activity, workload or ROI numbers.

---

## 10. Department model

Start small.

1. CEO / Command
2. Sales
3. Customer Support
4. Operations
5. Engineering

Later:

6. Marketing
7. Finance

Every department must eventually have:

- a real data source;
- a meaningful interaction point;
- a Management Mode destination.

A building that is purely decorative is not considered a completed department.

---

## 11. Controls

### Desktop

- WASD: movement
- mouse drag: camera pan
- mouse wheel: zoom
- E: interact
- Esc: close overlay
- Tab: quick management
- M: map

### Mobile

- virtual joystick: movement
- touch gesture: camera
- pinch: zoom
- contextual action button: interaction
- tap employee/building: focus/select

There is one World Engine.

Only input/presentation adapters differ between desktop and mobile.

---

## 12. World ↔ Management bridge

World Mode must be useful, not decorative.

World → Management:

- employee → Employee Management
- department → department dashboard
- WorkItem → WorkItem
- approval → Approval
- customer → Customer
- order → Order
- revenue/outcome → Analytics

Management → World:

- supported entities provide `Locate in HQ`.

The first vertical slice must prove this bridge for at least an employee.

---

## 13. First implementation vertical slice

The first real slice is deliberately narrow:

`Login → Customer Shell → World Mode → HQ map → real employee appears → employee state follows backend → E opens employee overlay → Employee Management → return to World`

Definition of done:

- authenticated customer can enter World Mode;
- Management Mode still works;
- World route loads;
- isometric scene renders;
- camera works;
- desktop movement works;
- mobile input works;
- a real employee is projected;
- employee visual state follows backend;
- interaction opens real employee information;
- user can jump to Employee Management;
- user can return to World;
- no duplicated business state;
- no fake metrics;
- frontend contract tests pass;
- frontend unit tests pass;
- Playwright covers the World shell;
- local real-stack smoke passes.

---

## 14. Frontend implementation phases

### F0 — Shell and mode architecture

- Management/World mode switch.
- World route.
- Full-screen responsive viewport.
- Preserve existing Management Mode.
- Mobile shell.

### F1 — World renderer and movement

- PixiJS.
- Isometric coordinate system.
- Map.
- Camera.
- Zoom/pan.
- Desktop input.
- Mobile input.
- Collision/navigation foundation.

### F2 — Real HQ

- departments;
- buildings;
- employees;
- authoritative presentation states;
- WorkItems;
- approvals;
- interactions.

### F3 — Management bridge

- contextual overlays;
- deep links;
- Locate in HQ;
- quick management;
- notifications where backed by real events.

### F4 — Business outcome loop

Prioritize:

Conversation → Lead → Qualification → Offer → Order → Revenue.

Only evidence-backed outcome metrics may be shown.

### F5 — Company progression

- company milestones;
- department/capability unlocks;
- activation/business missions;
- no independent arcade economy.

### F6 — Living World

- day/night;
- controlled ambient movement;
- visitors/events where real;
- background-work return summaries from platform state.

### F7 — Polish

- animation;
- VFX/audio;
- accessibility;
- mobile performance;
- visual consistency.

---

## 15. Reference-game mechanics: translation rules

Use the reference game's interaction language, not its independent economy.

- Build room → unlock/configure department.
- Furniture → capability/tool/knowledge/workstation.
- Tenant company → customer/business account.
- Rent → measurable revenue/savings/business outcome.
- Happiness → operational health/workload/quality.
- Repairman → operations/reliability capability.
- Energy → real usage/plan capacity only where justified.
- Diamonds → optional real premium credits, never a core-operation gate.
- Tasks → activation/business missions.
- XP → company progression.
- Idle income → real background business activity.

Do not copy proprietary assets, branding, maps or code.

Do not build a fake economy merely because a reference game has one.

---

## 16. Workforce roadmap alignment

The frontend World must consume the same governed workforce platform already described by the Workforce roadmap.

Important workforce rule:

Role → Operation → Capability Contract → Registered Tool → Tenant-safe Handler → Runtime Governance → Tests → Real-stack Evidence

A role is not considered implemented merely because it exists in a catalog.

The World must not introduce a parallel execution authority.

The existing Workforce roadmap remains the backend/domain execution roadmap. F0–F7 is the frontend product-experience track that makes those capabilities visible and usable.

---

## 17. Priority order

The implementation order is now:

### P0 — Product foundation

1. Preserve v1.4.17 certified baseline.
2. Keep current Management Mode stable.
3. Reconcile documentation/current truth.
4. Build F0.
5. Build F1.
6. Prove the first World vertical slice locally.

### P1 — Real company interaction

7. F2 real HQ projection.
8. F3 World ↔ Management bridge.
9. Sales + Customer Support priority.
10. Employee → WorkItem → Approval interaction.

### P1 — Business outcome

11. Conversation → Lead → Qualification → Offer → Order → Revenue.
12. Evidence-backed outcome dashboard.
13. Human handoff.

### P2 — Progression and living world

14. F5 progression.
15. F6 living world.
16. F7 polish.

Do not prioritize cosmetic/game-economy work above the real business loop.

---

## 18. Local runtime reference

Current local stack:

- API: 127.0.0.1:18000
- Frontend: 127.0.0.1:13000
- PostgreSQL: 127.0.0.1:15432
- Redis: 127.0.0.1:16379
- LM Studio host: http://127.0.0.1:1234/v1

Docker containers reach LM Studio through:

`http://host.docker.internal:1234/v1`

Use all three compose files for local real-AI tests:

```powershell
docker compose `
  -f .\docker-compose.yml `
  -f .\docker-compose.local-production.yml `
  -f .\docker-compose.local-lmstudio.yml ...
```

The LM Studio override is intentionally untracked unless explicitly promoted.

---

## 19. Existing local real-AI evidence

The local runtime has already proven:

Browser UI → API → Celery run.execute → LM Studio → HTTP 200 → AI provider call → successful Employee Run.

A real Workflow E2E has also proven:

Workflow input mapping → Employee Run → AI Gateway/provider → LM Studio → result → successful Workflow completion.

Therefore the World implementation should consume this existing runtime rather than create a new AI execution path.

---

## 20. Existing certification/evidence boundary

The repository has already passed the major local real-stack product gates covering:

- Auth;
- Tenant isolation and RBAC;
- Conversation tenant isolation;
- Employee → Run → AI → Result;
- Files → Knowledge → Memory;
- Admin/Developer;
- Workflow → Approval → Schedule;
- Orders → Sales → Invoice → Billing;
- Reports/Analytics isolation;
- Unified WorkItem human path;
- Unified WorkItem agent path;
- frontend Playwright E2E.

The certified v1.4.17 release remains the historical certification baseline.

Any new application code for World Mode requires fresh tests and fresh exact-SHA evidence.

---

## 21. Architecture rules for implementation

1. Backend remains authoritative.
2. World renderer is presentation/interaction, not business execution.
3. No second AI execution engine.
4. No second tenant/auth system.
5. No fake business metrics.
6. No direct provider calls from visual components.
7. No generic shell/HTTP execution as a hidden substitute for governed semantic operations.
8. External-impact actions remain approval-gated.
9. World interactions must preserve tenant boundaries.
10. Every new business read model must have a clear authoritative source.
11. Every state animation must have a real source or be explicitly ambient/non-business.
12. Management Mode must remain usable without World Mode.
13. Mobile is first-class, not a later CSS pass.
14. Prefer small vertical slices over broad unfinished infrastructure.

---

## 22. What not to build now

Do not start with:

- wardrobe/cosmetics;
- premium diamonds;
- decorative furniture catalog;
- giant city;
- large NPC populations;
- traffic simulation;
- voice avatars;
- full 3D;
- VR;
- multiplayer;
- fake rent/income economy;
- speculative revenue dashboards;
- autonomous external outreach;
- live payment execution;
- external production deployment.

These can be revisited only after the first real business loop proves product value.

---

## 23. Validation protocol for every World implementation PR

Before merging any application-code World change:

1. Backend compile where applicable.
2. Ruff/backend tests where backend changes exist.
3. Frontend contract tests.
4. Frontend unit tests.
5. Frontend production build.
6. Playwright World coverage.
7. Local Docker real-stack smoke.
8. Tenant/auth/governance regression for affected paths.
9. Verify no fake metrics or duplicated backend state.
10. Record exact commit SHA and evidence.
11. Update this hand-off only when the implementation truth changes.
12. Do not claim release certification unless the official certification workflow passes on the exact SHA.

---

## 24. Documentation hierarchy

Use this hierarchy:

- `docs/current/` — current operational truth.
- `docs/architecture/` — architecture truth.
- `docs/blueprint/` — approved design/blueprint.
- `docs/historical/` — immutable historical evidence.

If an old document conflicts with current evidence, do not silently treat it as current.

Current canonical documents for this initiative:

- `docs/current/MASTER_HANDOFF.md`
- `docs/current/FRONTEND_WORLD_TRANSFORMATION_AUDIT.md`
- `docs/blueprint/AI_COMPANY_WORLD_GAMEPLAY_SPEC.md`
- `docs/blueprint/AI_WORKFORCE_IMPLEMENTATION_ROADMAP.md`

---

## 25. Immediate next action

The next implementation task is F0, not another backend feature.

F0 should introduce:

- a customer-shell mode switch;
- a dedicated World route;
- a responsive World shell;
- no fake world business state;
- no replacement of existing Management Mode;
- test coverage for mode switching and World route access.

F0 should be followed immediately by the smallest F1 slice needed to render a real isometric HQ and prove desktop/mobile input.

The first success criterion is not visual richness.

It is:

> A real customer enters World Mode, sees their real AI employee in the HQ, interacts with that employee, and can jump to the existing Management Mode without leaving the authoritative product runtime.

---

## 26. Handoff decision

The project is ready to move from strategy/documentation into the first controlled frontend implementation slice.

The correct next move is not a rewrite.

It is a controlled vertical transformation:

`Existing Customer Shell → F0 Mode Switch → F1 World Shell → Real Employee Projection → Management Bridge → Business Outcome Loop`

Keep the backend governed and authoritative.

Keep the current certified release untouched.

Keep local execution as the boundary.

Build the World around the real AI Company, not around a fictional game economy.
