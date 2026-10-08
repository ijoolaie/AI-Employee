# Frontend Transformation Audit — Management Mode + AI Company World

Date: 2026-10-08
Baseline audited: main at f45f8220c329813f9d642162e30fc7e6689adf1b
Scope: frontend code, W12/W13 documentation, product roadmap and AI Company World specification
Execution boundary: local-first

## Executive finding

The existing frontend is a solid enterprise SaaS shell with a read-only Virtual Office, but it is not yet the dual-mode AI Company product described by the new gameplay specification.

The correct strategy is incremental replacement of the presentation layer, not a rewrite of the platform.

Strengths:
- Next.js 16 + React 19 foundation is appropriate.
- React Query and the existing authenticated API client are reusable.
- /office already proves the correct architectural direction: tenant-scoped backend data → presentation state.
- W13 derives HQ tier/capacity from authoritative subscription data.
- Sidebar already exposes AI Company HQ.
- Existing Employee, WorkItem, Run, Approval, Customer, Sales, Order, Analytics and Billing routes provide reusable Management Mode surfaces.

Gaps:
- /office is a dashboard/card grid, not an explorable world.
- No World Engine, camera controller, movement adapter, collision/navigation layer or world interaction system exists.
- No World/Management mode switch exists.
- No department/world projection exists.
- No PixiJS or equivalent world renderer dependency exists.
- No mobile-first world HUD exists.

## What must remain unchanged

Do not replace:
- Next.js/React application shell.
- Customer authentication/layout.
- Axios/API client.
- React Query.
- existing domain API contracts.
- Employee/Run/WorkItem/Approval governance.
- tenant isolation.
- billing/entitlement authority.
- Management Mode routes.
- current W12 read-only semantics until the new World implementation has equivalent evidence.

Do not introduce a second backend execution engine.

## Current architecture assessment

The customer layout owns authentication and renders the Sidebar plus scrollable main content. It should become the Application Shell with a Management/World mode switch inside the customer workspace.

The Sidebar is already grouped into Business, People & AI, Customer Operations, Finance & Platform, Developer and Settings. Retain this as Management Mode navigation. World Mode should have a much lighter HUD.

The existing /office route consumes GET /api/v1/customer-dashboard/office and already renders authoritative HQ tier, subscription/capacity, employee states, current WorkItem and pending approvals. This should become the data-contract foundation for World Mode rather than being discarded.

## Target architecture

Customer Application Shell
- Management Mode
  - Dashboard
  - Customers
  - Sales
  - Orders
  - Employees
  - Work
  - Finance
  - Analytics
  - Workflows
  - Governance/Developer
- World Mode
  - WorldViewport
  - WorldCamera
  - WorldInput
    - DesktopInputAdapter
    - MobileInputAdapter
  - WorldMap
  - Buildings
  - Departments
  - Employees
  - Interactions
  - Navigation/Collision
  - WorldHUD
  - WorldOverlays

The World renderer must be isolated from business logic.

## Renderer decision

Recommended first implementation: PixiJS 2D/2.5D.

Reason:
- current product is a Next.js web application;
- the reference is visually isometric rather than requiring true 3D;
- PixiJS fits an interactive 2D canvas while React retains control of forms, panels and SaaS UI;
- it minimizes architectural disruption;
- mobile performance is easier to control than a premature full 3D engine.

Do not add Three.js merely because the reference looks like a game.

## Proposed frontend module boundary

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

Do not move existing management features into the world feature.

## World state boundary

World state should initially be derived from existing APIs.

Minimum read model:
- hqTier
- subscription/capacity
- departments
- employees: id, name, avatar, presentationState, currentWorkItem, latestRun
- approvals
- workItems
- customer/activity summaries
- generation timestamp

The first implementation must not invent revenue, customer activity, employee productivity or department state where the backend does not provide it.

## Department model

Initial world layout should be deliberately small:
1. CEO / Command
2. Sales
3. Customer Support
4. Operations
5. Engineering

Later:
6. Marketing
7. Finance

Each department must have real data, an interaction point and a Management Mode destination. It must not be decorative only.

## Employee world model

Keep the existing authoritative presentation-state mapping.

Initial visual states:
- IDLE
- WORKING
- WAITING_APPROVAL
- BLOCKED
- ESCALATED
- COMPLETED

Do not add MEETING animation until a real backend/session source exists.

## Controls

Desktop:
- WASD movement
- mouse camera pan
- mouse-wheel zoom
- E interaction
- Esc close
- Tab quick management
- M map

Mobile:
- virtual joystick
- touch camera gesture
- pinch zoom
- contextual interaction button
- tap employee/building to focus/select

Desktop and mobile share one World Engine; only input/presentation adapters differ.

## World ↔ Management bridge

World → Management:
- employee → employee management
- department → department dashboard
- WorkItem → WorkItem
- approval → approval
- customer → customer
- order → order
- revenue/outcome → analytics

Management → World:
- Locate in HQ on supported entities.

This is essential. Otherwise World Mode is only decoration.

## Visual transformation

Management Mode keeps the current professional SaaS language.

World Mode becomes:
- full viewport
- isometric 2.5D map
- stylized buildings
- recognizable departments
- animated employee avatars
- contextual interaction markers
- compact HUD
- panels only when needed

The product should feel like a business simulation, not a children's game.

## Reference-game mechanics translated to AI Company

Build room → unlock/configure department.
Furniture → capability/tool/knowledge/workstation resource.
Tenant company → customer/business account.
Rent → measurable revenue/savings/business outcome.
Employee happiness → operational health/workload/quality.
Repairman → operations/reliability capability.
Energy → real usage/plan capacity only where commercially justified.
Diamonds → optional real premium credits, never a core-operation gate.
Tasks → activation/business missions.
Player XP → company progression.
Idle income → real background business activity.

Do not reproduce an independent arcade economy.

## First vertical

The first commercially meaningful World loop should support:

Conversation → Lead → Qualification → Offer → Order → Revenue.

Sales and Customer Support therefore have priority over cosmetic systems.

## Do not build yet

Do not start with:
- wardrobe
- cosmetic marketplace
- premium diamonds
- decorative furniture catalog
- large city
- large NPC populations
- complex traffic simulation
- voice avatars
- 3D/VR
- multiplayer
- fake rent economy

These do not validate the product as effectively as the first real business loop.

## Implementation phases

F0 — Shell and mode architecture
- mode switch
- World route
- full-screen viewport
- management preservation
- responsive/mobile shell

F1 — World renderer
- PixiJS
- isometric coordinate system
- map
- camera
- zoom/pan
- desktop input
- mobile input

F2 — Real HQ
- departments
- employees
- real presentation states
- current WorkItem
- approvals
- interactions

F3 — Management bridge
- entity overlays
- Locate in HQ
- deep links
- notifications
- quick management panel

F4 — Business outcome layer
- conversations
- leads
- orders
- outcome metrics
- AI cost
- ROI where evidence exists

F5 — Progression
- company milestones
- department unlocks
- capability progression
- activation missions

F6 — Living world
- day/night
- ambient employees
- visitors
- controlled environmental animation

F7 — Polish
- animation
- sound
- VFX
- accessibility
- performance

## F1 Definition of Done

F1 is complete only when:
- World route loads for an authenticated customer;
- existing Management Mode remains unchanged;
- isometric map renders;
- camera pans/zooms;
- desktop movement works;
- mobile movement works;
- viewport is responsive;
- no backend business state is duplicated;
- no fake business metrics are shown;
- World/Management switch works;
- existing frontend contract tests pass;
- existing frontend unit tests pass;
- Playwright covers the World shell;
- local real-stack smoke evidence exists.

## Recommended first vertical slice

Login → Customer Shell → World Mode → HQ map → real employee appears → employee visual state follows backend → E opens employee overlay → open Employee Management → return to World.

Only after this is stable should departments, customers, orders and progression be added.

## Release boundary

This audit is design/code-reconciliation work. It does not certify World Mode.

Any implementation PR must preserve tenant isolation, governance, approvals, tool authorization and auditability; pass frontend contract/unit/browser tests; run local real-stack checks; document exact SHA; and receive fresh certification before promotion into a certified release.

## Final decision

The frontend should evolve from:

SaaS Dashboard + Read-only Virtual Office

to:

AI Company Platform = Management Mode + Explorable World Mode

The backend remains the product source of truth. The World is the visual and interactive representation of that real AI Company.
