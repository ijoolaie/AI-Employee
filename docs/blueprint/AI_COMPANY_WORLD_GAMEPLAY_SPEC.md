# AI Company World & Gameplay Specification

Status: CANONICAL PRODUCT / UX / GAMEPLAY SPECIFICATION — DESIGN BASELINE
Reconciled: 2026-10-08

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