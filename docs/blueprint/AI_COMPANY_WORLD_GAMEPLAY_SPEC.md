# AI Company World & Gameplay Specification

Status: CANONICAL PRODUCT / UX / GAMEPLAY SPECIFICATION — DESIGN BASELINE
Reconciled: 2026-10-12 — user-approved visual reference refinement

## 1. Purpose

This document converts the observed mobile isometric office/tycoon gameplay reference into an AI-Employee-specific product specification. The reference supplies interaction patterns, visual language, progression, spatial presentation and engagement loops. It is not a specification of the original game's source code, formulas or backend.

AI-Employee remains an enterprise-grade AI Company platform. World Mode is a presentation and interaction layer over the governed platform runtime.

## 2. Product thesis

Build a real AI Company that the user can run, manage and walk through.

One authoritative backend state feeds two presentation modes:

Management Mode: SaaS operations, tables, forms, analytics, workflows, billing, governance.
World Mode: explorable HQ, departments, AI employees, interactions, movement, camera and ambient presentation.

These are two views of one product, not two separate products.

## 3. Non-negotiable architecture

Backend state remains authoritative. The frontend must not create a second business/economy state.

Authoritative domains include Employee/Agent, WorkItem, Run, Workflow, Approval, Customer, Conversation, Product, Order, Usage and Billing.

World projection may cache rendering data, but it must never become the source of truth for business state, authorization, permissions, approvals or financial outcomes.

## 4. Reference-to-product mapping

| Reference | AI-Employee |
|---|---|
| Building | AI Company HQ |
| Floor | Department |
| Office | Department / workspace |
| Furniture | Capability / tool / knowledge / workstation resource |
| Tenant company | Customer / business account |
| Rent | Revenue / savings / measurable business outcome |
| Employee | Governed AI Employee / Agent Instance |
| Happiness | Operational health, workload and quality |
| Facility requirement | Required knowledge, tool, integration, data or policy |
| Repairman | Operations / Reliability capability |
| Construction | Department/capability unlock |
| Energy | Plan/usage/capacity limits only where commercially justified |
| Diamonds | Optional premium credits only if a real premium mechanic exists |
| Tasks | Business missions / activation objectives |
| Player level | Company progression |
| Idle income | Background business activity and accumulated outcomes |
| Day/night | World time and ambient presentation |
| NPCs/traffic | Employees, customers, visitors, partners and ambient activity |

## 5. Core gameplay loop

Build Company → Unlock Department → Provision AI Employee → Give Knowledge + Tools + Permissions → Assign Work → AI executes real WorkItems → Business outcome → Revenue/saving/time saved/customer outcome → Review health → Improve capability/add employee/expand department → Repeat.

For the first commercial vertical the preferred outcome loop is Conversation → Lead → Qualification → Offer → Order → Revenue.

This keeps the game loop tied to the existing Sales, Customer, Conversation, Commerce, Run and Billing foundations.

## 6. AI Company HQ

Initial meaningful departments:
- CEO / Command
- Sales
- Customer Support / Success
- Marketing
- Operations
- Finance
- Engineering

Each department is a functional projection, not decoration.

Sales may show conversations, qualified leads, follow-ups, orders, revenue influenced, AI cost, pending approvals and blocked work.
Support may show open conversations, escalations, human handoffs, resolution and SLA/queue signals where configured.
Marketing may show campaigns, content work, attributable leads and approvals where evidence exists.
Finance may show invoices, payments, billing, usage, AI cost and financial approvals.
Engineering may show WorkItems, tests, builds, deployments, incidents, approvals and blocked work.

Never fabricate metrics merely to make the world appear active.

## 7. AI Employee representation

An AI Employee is a real governed execution identity, not a decorative NPC.

Visual state derives from role, department, WorkItem, Run status, approval status, workload, tool state, errors and configured avatar.

Suggested states: Idle, Working, Walking, Waiting Approval, Meeting, Blocked, Needs Attention, Completed.

The renderer must never show Working when authoritative state says Blocked or Idle.

## 8. Interaction model

Desktop: WASD movement, mouse camera control/pan, contextual interaction, configurable sprint, Esc menu, Tab quick panel, M map and E/context interaction.

Example: approach employee → [E] Interact → employee card → current task/history/management view.

Mobile: virtual joystick, touch camera gestures, contextual interaction button, tap-to-focus and mobile-first HUD/panels.

Desktop and mobile share the same World Engine and backend state. Only the Input Adapter differs.

## 9. World technology boundary

Keep Next.js/React as the management shell.

Recommended initial renderer: PixiJS for 2D/2.5D isometric world; React/Next for management UI, HUD, forms and panels.

Conceptual structure:

Next.js/React → Management UI + HUD + Company World → World Renderer → Camera / Map / Buildings / Employees / Collision / Animation / Interaction / Input.

Input adapters: Desktop Keyboard+Mouse and Mobile Touch.

Three.js or a full 3D engine is not required for the first implementation. Introduce true 3D only if validated visual requirements justify it.

## 10. Visual direction

Target: stylized isometric 2.5D business world with polished tycoon readability.

Use a 3/4 top-down camera, readable rooms, professional stylized characters, soft shadows, clear silhouettes, mobile-friendly HUD, visible construction/unlock states, subtle environmental animation, day/night presentation and optional seasonal themes.

The product should feel like a business simulation, not a children's game.

Do not copy proprietary assets, names, characters or source implementation from the reference.

## 11. Building and capability progression

Department lifecycle: Locked → Available → Unlocking/Configuring → Active → Degraded/Needs Attention → Active.

An apparent construction sequence must correspond to a real capability, configuration or entitlement.

Reference furniture upgrades become capability upgrades. Example:

Sales Capability Lv.1: answer customers.
Lv.2: answer + qualify leads.
Lv.3: answer + follow-up.
Lv.4: answer + qualify + follow-up + create orders.
Lv.5: governed autonomous sales workflow.

An upgrade must correspond to a real capability, integration, tool, workflow or measurable capacity. Do not create arbitrary stat inflation.

## 12. Customer loop

Customer → Onboarding → Connect channel → Connect business data → Deploy AI Employee → Conversation/Work → Human handoff when needed → Business outcome → ROI/subscription/expansion.

Human handoff remains a first-class product path and must preserve context and auditability.

## 13. Economy

Do not copy the reference game's arcade currency system.

Primary business metrics are Revenue, Revenue Influenced, AI Cost, Orders, Leads, Conversations, Human Hours Saved and evidence-backed ROI.

Commercial limits may use subscription entitlements, usage capacity, employee capacity, workflow capacity and optional premium credits.

Any limit must map to an actual commercial/product rule.

## 14. Background / idle progression

World Mode should continue to reflect real background work while the user is away.

On return, show an evidence-backed summary such as conversations handled, leads qualified, follow-ups, orders, revenue influenced, tasks completed and AI cost.

Every displayed number must come from persisted platform data. Unknown values must not be invented.

## 15. Operational health instead of arcade happiness

Use measurable dimensions: workload, queue depth, success rate, error rate, latency, blocked state, knowledge freshness, integration health and SLA compliance where a target exists.

Show individual metrics before introducing a composite health score. Any composite score must have a documented formula and evidence.

## 16. Maintenance / reliability loop

Reference repair mechanics become real operational maintenance: expired credentials, failed connector, stale knowledge, excessive queue, failed workflow, blocked approval, provider issue or deployment failure.

Operations/Manager surfaces the issue and governed actions such as reconnect, reconfigure, reassign or add capacity.

All actions remain subject to existing authorization, approval, audit and tenant-isolation rules.

## 17. Missions / tasks

Business missions should drive activation and measurable outcomes.

Examples: deploy first AI Employee; connect first channel; add product knowledge; handle first 10 conversations; qualify first lead; generate first AI-assisted order; configure human handoff; activate Support; review first ROI report.

Progress must be driven by real domain events such as EmployeeActivated, ChannelConnected, KnowledgeIndexed, ConversationHandled, LeadQualified, OrderCreated and HumanHandoffCompleted.

Do not use client-side fake counters.

## 18. Company progression

Replace player XP with Company Progression. Progression is driven by meaningful milestones, for example CEO/Command → Sales → Customer Support → Marketing → Operations → Finance → Engineering.

The exact unlock order remains a product decision and must follow capability dependencies and the first-vertical strategy.

## 19. Living world

Day/night, employees walking, visitors, customers, traffic, construction animation and seasonal themes may be used as presentation systems.

Ambient effects must never imply fake business activity.

## 20. Management ↔ World navigation

World objects must link to real SaaS surfaces: Employee → Open Employee; Department → Open Department; Customer → Open Customer; Order → Open Order; Alert → Open WorkItem; Approval → Open Approval; Revenue → Open Analytics.

Management pages may expose Locate in HQ to focus the World camera on the relevant object.

This creates one product rather than disconnected dashboard and game frontends.

## 21. Mobile requirements

Mobile is first-class: touch movement, touch camera, contextual interaction, responsive HUD, readable panels, low-memory rendering mode, asset/animation budget and network-interruption handling.

Mobile must use the same backend truth, permissions and World Engine; only input/presentation adapters differ.

## 22. Event-driven design

World Mode should consume authoritative domain events/state. It should not invent business events.

Example: OrderCreated → TaskService + CompanyProgression + Analytics + Notification + WorldProjection.

Example: IntegrationDegraded → Operations + Notification + Manager + WorldProjection.

This also aligns with the existing event-driven task and governed WorkItem architecture.

## 23. Data model boundary

Do not create a game-only economy schema.

World projection may contain building state, employee visual state, interaction targets, camera/map state and ambient presentation state, while tenant business state remains in existing domain services.

Any new persistent world model must have a clear ownership boundary and must not duplicate Employee, Agent, WorkItem, Run, Customer, Order, Billing or Usage truth.

## 24. Implementation order

Phase A — World Foundation: renderer, isometric map, camera, player/avatar, desktop movement, mobile input adapter, collision, buildings/rooms and Management↔World navigation.

Phase B — Real Company: department projection, AI Employee projection, employee movement, backend-driven states, interactions and management handoff.

Phase C — Business Loop: WorkItems/tasks, customers/conversations, leads, orders, revenue/outcome metrics, AI usage/cost and ROI/evidence views.

Phase D — Progression: Company progression, department unlocks, capability upgrades, missions, notifications and rewards.

Phase E — Living World: day/night, visitors/NPCs, ambient movement, events and return/offline summary.

Phase F — Polish: animation, VFX, audio, seasonal themes, accessibility and performance optimization.

## 25. Explicit non-goals

Do not create an independent game economy unrelated to SaaS economics; use fake revenue; create fake employee activity; grant permissions through game mechanics; hide governance controls behind the game; require an energy bar for normal business operations; replace Management Mode; introduce a second backend execution engine; or claim mobile parity before mobile acceptance exists.

## 26. Evidence boundary

This is a product/design baseline. It does not claim that the proposed World Mode is implemented in the current release.

Current W12 Virtual Office remains the read-only presentation foundation derived from governed Employee/Run/WorkflowApproval state. The interactive World Mode described here is a future implementation slice unless separately evidenced.

Any application-code implementation promoted into a release requires fresh exact-SHA certification.

## 27. Acceptance criteria

A World Mode release candidate is complete only when Management Mode remains functional; World Mode renders from authoritative state; desktop and mobile movement work; camera/collision work; employee visual state matches backend state; interactions open real domain views/actions; no game-only business source of truth exists; tenant isolation/RBAC/approval/tool governance remain intact; metrics are evidence-backed; World state is tenant-scoped; performance is acceptable on supported targets; frontend contract/unit/browser tests pass; relevant real-stack E2E evidence passes; and the promoted SHA receives fresh exact-SHA certification.

## 28. Product success metrics

Primary: Time to First Value, first AI Employee activation, first connected channel, first conversation, first qualified lead, first order, retention and expansion.

Experience: World Mode usage, Management↔World transitions, employee/department interactions, mission completion and return sessions.

Economics: revenue/customer, gross margin, AI cost/customer, support cost/customer, CAC, ARPU, churn, LTV/CAC and payback period.

World Mode succeeds only if it improves activation, understanding, engagement or retention without materially degrading operational usability.

## 29. Relationship to existing architecture

This specification extends rather than replaces V1.4 platform architecture, V1.5 Agentic Operating Model, governed Agent/Employee identity, WorkItem execution, Workflow/Approval, Tool Registry, Knowledge/Memory, Customer/Conversation/Commerce, Billing/Usage, Test Center and tenant isolation/RBAC/audit.

Strategic model: Human CEO → AI Company → Departments → AI Employees/Agents → WorkItems → Tools + Knowledge + Policies → Execution → Business Outcomes → Revenue/Savings/Growth → Company Progression.

World Mode is the visual and interactive representation of that system.
## 30. Approved visual reference — office-management tycoon presentation (2026-10-12)

### Reference intent

The user supplied two visual references for the AI Company World redesign:

- **Current product screenshot:** a wide desktop, 3/4 isometric office HQ with department zones (Command, Sales, Operations, Customer Care, Engineering), a large tiled floor, simple desks/chairs/monitors, floating department labels, a central HQ label, a small player/worker avatar, and minimal top/bottom controls. This is the baseline to improve, not the desired final art quality.
- **Target gameplay screenshot:** a portrait mobile office-management/tycoon scene with warm cream walls, salmon/red room flooring, teal/blue partitions, large windows with blinds, doors, framed wall decor, detailed desks/computers and storage, several visibly different human-like employees in varied outfits/hairstyles, clear isometric depth and soft shadows, and a compact high-contrast HUD for resources/time/status plus contextual action buttons.

Treat the second screenshot as the **visual direction**, not as a pixel-perfect layout to copy. It is a reference for readability, art quality, material/color contrast, room detail, character variety and mobile game composition. Do not copy proprietary game assets, branding, UI artwork, characters, maps, or source code.

### Target art direction

- **Camera and composition:** consistent 3/4 top-down isometric view with stable perspective, clear room boundaries and an immediately readable floor plan. Desktop may show the full HQ; mobile should frame a useful playable area without shrinking labels into illegibility.
- **Architecture:** replace the empty warehouse-like impression with warm, designed office interiors: distinct floor materials/colors per room, cream/light neutral walls, window bays with frames/blinds, doors, wall art/signage and tasteful trim. Keep the existing named AI-Employee departments and make them easy to identify.
- **Workstations and props:** create coherent desk sets with monitor, keyboard, chair and small office objects; add cabinets, plants, dividers, meeting furniture and department-specific props. Props must not obstruct paths, employee selection, labels or controls.
- **Palette and materials:** warm coral/terracotta floor accents, cream walls, teal/blue partitions and furniture accents, restrained department color identity, consistent material response and soft contact shadows. Maintain sufficient contrast for text and interactive targets.
- **Employees:** use varied, friendly, stylized low-poly/cartoon characters with readable silhouettes, differing hair, clothing colors and body/accessory details. Avoid repeated capsule/box figures as the final presentation. Use original or properly licensed assets and record source/license/provenance; no unlicensed extracted sprites or copied characters.
- **Animation and life:** idle/work/walk/approval states may use subtle, reduced-motion-aware animation only when supported by actual employee/run/approval state. Ambient motion must not imply fake business activity.
- **HUD:** preserve a restrained enterprise product identity while borrowing the reference's compact, high-contrast hierarchy: company/status summary, authoritative resource/usage information, current time only if it is a real world clock, and contextual actions. Do not add fictional coins, gems, energy, income or arcade progression. Do not reproduce the reference's exact HUD, icons or text.
- **Lighting and depth:** coherent light direction, soft shadows, layered walls/furniture and subtle highlights; avoid excessive bloom, noisy decoration or low-contrast UI.

### AI-Employee semantic mapping

| Visual reference element | AI-Employee representation |
|---|---|
| Room / office | Existing tenant-scoped department/workspace projection |
| Desk / computer | Workstation presentation; not a new permission or capability source |
| Character | Real governed Employee/Agent identity and configured avatar where available |
| Working/waiting character pose | Authoritative supported employee/run/approval state only |
| Room label | Existing AI-Employee department identity; no fabricated department metrics |
| HUD resources | Existing plan, usage, capacity and recorded outcome fields only |
| Lock/door/access affordance | Existing server-authoritative entitlement and tenant-scoped room access |
| Upgrade/unlock affordance | Real capability, entitlement or configuration workflow; never cosmetic authority |

The currently available office read model may not expose authoritative employee department/location ownership. Until that contract exists, department zones are presentation-only and must not falsely imply employee assignment or access rights.

### Implementation priorities

1. **P0 — Scene composition and legibility:** establish a deliberate isometric room plan, improve floor/wall/window/door composition, retain clear department identities, fix clipping/overlap, and ensure desktop/mobile camera framing.
2. **P1 — Character and workstation quality:** replace the most visible primitive-built workers and furniture with authored original/licensed assets or deliberately modeled, cohesive procedural art; vary employee silhouettes and desk details.
3. **P2 — Interaction and navigation:** keep movement, camera, employee selection, contextual interaction, room lock/expiry and keyboard/touch controls functional. Implement and test obstacle-aware navigation rather than relying only on static collision guards.
4. **P3 — HUD and accessibility:** improve mobile label sizing/contrast, safe-area placement, focus/keyboard behavior, touch target size and reduced-motion handling.
5. **P4 — Finish and evidence:** add restrained shadows/material polish and optional ambient details; capture actual route screenshots at desktop 1440×900 and mobile 390×844, inspect console/layout/input behavior, and record the results in the implementation handoff.

### Acceptance gates

- The actual /world route is materially and visibly improved relative to the current procedural box-built scene; an isolated mockup or generated concept image is not implementation evidence.
- Desktop and mobile screenshots are captured from the running application after the change and reviewed against this section.
- Department labels, employees, workstations, doors, HUD and controls remain readable and do not overlap or clip at supported viewport sizes.
- Employee states, metrics, entitlements, room access and approvals remain grounded in authorized backend read models. No fake economy or activity is introduced.
- Mouse/keyboard and touch controls, employee selection, room lock/expiry, tenant isolation, accessibility and reduced-motion behavior continue to work.
- Authored asset licenses/provenance are recorded. No proprietary reference assets or source code are copied.
- Frontend lint, unit/contracts, build and relevant Playwright tests pass; relevant real-stack smoke checks are recorded.
- Keep the redesign PR Draft/unmerged until visual acceptance is explicit. Green CI is necessary but not sufficient and does not certify a production release.

### Current evidence boundary — 2026-10-13

- PR #1050 is closed unmerged; its historical comments must not be treated as current implementation evidence. PR #1057 merged as `de053b24d045d17d0e447e29140cfd4728ade4c8` for the warm floor/window polish, but the current `main` tree has no `employee-base.glb`, `GLTFLoader`, or World asset-credit/license files. Player/CEO and employee models remain procedural.
- PR #1071 accepted viewport framing for its bounded criterion.
- PR #1072 merged as `c097eedbc5674d788d72b5b3a2d334adba1737e6`; exact-head workflows passed and desktop/portrait screenshots were manually reviewed. Acceptance is limited to glass partitions, colored rails and mullions.
- PR #1075 exact head `f316ef147b43eccf5b82a2776dfc4bf124f4b6cf` passed CI, Documentation Truth Consistency, CodeQL, HA Failure Recovery, Production Infrastructure Validation and Ephemeral DAST. The fresh [desktop/portrait screenshot artifact](https://github.com/ijoolaie/AI-Employee/actions/runs/38358857827/artifacts/11793314632) was reviewed; the office floor fits the 390×844 portrait canvas after a small camera-fit adjustment, and the room entrances/tiled zones are visible. This is accepted for the bounded room/floor/portrait-fit slice on the exact code head; use the GitHub PR state for merge lifecycle. Full obstacle-aware pathfinding, authored employee assets and overall World completion remain incomplete.
- Authored employee assets, a validated scene-layout model, full obstacle-aware pathfinding, character animation quality and overall visual acceptance remain incomplete.

The redesign is **not considered complete** until the acceptance gates above are met. CI success and screenshots from a candidate are evidence only for that exact source head; neither certifies a production release.