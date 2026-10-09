# AI Employee Platform — Productization & Delivery Roadmap

## Roadmap truth — 2026-10-09

Three axes remain independent:

- **Release:** `v1.4.17` at exact certified SHA `b403c0dcdea579e017738a6fdea138c2b1a2999c`, published after exact-SHA Production Certification Run `37625345534`.
- **Architecture:** `V1.5 Agentic Operating Model`.
- **Engineering:** external production execution, governed Agent workforce hardening and operational/customer acceptance.

`v1.4.17` is the latest published exact-SHA certified release. The release identity is immutable; later `main` documentation/engineering commits are not automatically certified.

## Current position

Phase 11 Unified Execution is complete. Phase 12 Test Center is operationally hardened. Phase 13 Agent Teams & Marketplace is engineering complete. Phase 14.1–14.16 tracked engineering is complete/reconciled.

The project is now in **Post-release Reconciliation → External Production & Customer Acceptance**, with repository governance hardening tracked separately in Issue #975. The audited product-completeness gate is closed for the current scope and remains under regression watch.

## Current engineering checkpoint — 2026-10-09

- AI Company World F8 is merged in PR #977. Employee visual slots are stable by immutable employee ID; `departmentId` remains `null` until an authoritative tenant-scoped assignment contract exists. Do not infer organizational placement from names, roles, runs, work items, or API ordering.
- PR #978 reconciled the master implementation hand-off; PR #979 reconciled current status/priority documents after F8; PR #980 reconciled this roadmap's release truth. These are engineering/documentation changes, not new production certification.
- Last verified live `main` checkpoint after PR #980: `4492ad2c3d3d0f6c2b91189e37a7614fa5ca1259`; re-resolve Git metadata before future work.
- `main` branch protection/rulesets remain unconfigured in the evidence available here. Owner/admin configuration and a test-PR verification are tracked by [Issue #975](https://github.com/ijoolaie/AI-Employee/issues/975).
- The immutable latest published/certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Engineering commits after that SHA do not inherit certification.

## 2026-10-07 v1.4.17 publication closure

The PR #955 application-code boundary `b403c0dcdea579e017738a6fdea138c2b1a2999c` passed exact-SHA Production Certification and has now been published as `v1.4.17`.

- Certification Run: **37625345534**
- Certification Job: **112805570856**
- Result: **PASS**
- Product Gate failures: **0**
- Evidence digest: **sha256:c05d9ba79e135dfb64ffd7aed89e2fd36b1ebcb53f6ef2ddfb865e516b870e3d**
- Git tag `v1.4.17`: **VERIFIED**
- GitHub Release `v1.4.17`: **PUBLISHED**
- External production deployment: **NOT VERIFIED / NOT CLAIMED**
- Customer acceptance/revenue: **NOT VERIFIED**

No application-code change is required merely to reconcile this publication. The next work is external evidence, not another feature expansion.

## W0–W23 final evidence boundary — 2026-10-07

- **W0:** implemented / baseline infrastructure.
- **W1:** real-stack verified.
- **W9:** real-stack verified; not a new implementation target.
- **W10:** governed sales/payment mechanics verified; real customer qualification, acceptance and realized external revenue remain not verified.
- **W16:** marketplace lifecycle/governed execution mechanics verified; external payout/revenue/tax settlement remain not verified.
- **W17:** implemented / real-stack verified.
- **W18:** implemented / real-stack verified first vertical slice.
- **W19:** design foundation active; provider execution not implemented/configured.
- **W20:** implemented / real-stack verified first governed vertical slice; external payout/revenue/tax/customer outcome not verified.
- **W21:** implemented / real-stack verified; autonomous external company-network execution and financial/customer outcomes not verified.
- **W22:** implemented / real-stack verified; live search/SEO traffic impact not verified.
- **W23:** implemented / real-stack verified; live provider/customer outcome not verified.

## Product Completeness Gate — added 2026-09-21

The product-completeness gate was completed for the audited scope before v1.4.11 certification. External production gates remain independent and open pending an external target.

### Product-completeness requirements — CLOSED FOR CURRENT AUDITED SCOPE

1. **Persian/English localization:** **DONE for the audited customer operational scope**; EN/FA browser acceptance, locale-aware formatting and true RTL direction coverage are in place.
2. **Customer Employee Templates:** **DONE for the audited scope**; the customer-facing curated catalog contains seven tenant-safe bilingual starter templates with lifecycle/installation metadata. These seven templates are the current **operational/customer starter catalog**, not the complete AI-company workforce role catalog.
3. **Operational lists and lifecycle:** **DONE for the audited scope**; Product, Customer, Order/Invoice and Schedule lifecycle parity uses resource-specific non-destructive semantics where retention/auditability requires them.
4. **Backend/frontend parity:** **DONE for the audited scope**; customer-visible lifecycle actions map to supported and authorized operations.
5. **Shared UX states:** **DONE for the audited scope**; customer Analytics/Reporting retry and empty states plus permission/lifecycle state handling are covered.
6. **Browser acceptance:** **DONE for the audited scope**; principal customer operational routes are accepted in both `en` and `fa`, including `lang`/`dir` assertions.
7. **Edition-aware Test Center — DONE:** Vendor, Reseller and Customer definition visibility and execution boundaries are edition-aware; shared isolation/RBAC/execution controls remain covered at the shared boundary, without requiring every service in every edition.

Canonical record: docs/current/PRODUCT_COMPLETENESS_GATE_2026-09-21.md.

This gate was the source-change gate completed before v1.4.11 certification. It does not modify or weaken immutable historical release certifications.

## Commercial Readiness Gate

### Objective

Prove that the certified product can be operated safely, observably and recoverably in a real production environment and can pass the required partner/customer acceptance gates.

### Required gate sequence

1. **Readiness audit** — inspect application, security, database, deployment, secrets, monitoring, DR, providers, billing, Agent governance, tenant isolation and customer UX/support readiness.
2. **Blocker register** — classify every finding as blocker, required-before-launch, follow-up, or ready/evidenced.
3. **Production target** — provision and harden the actual target; record infrastructure identity and configuration evidence.
4. **Exact release deployment** — deploy the currently approved immutable release identity (`v1.4.17`, SHA `b403c0dcdea579e017738a6fdea138c2b1a2999c`) only after the real external target is provisioned; preserve deployment evidence.
5. **Security/network validation** — verify TLS, ingress/egress, firewall, secret lifecycle, credential rotation and relevant attack surfaces.
6. **Data protection** — validate backup integrity, restore procedure and migration/recovery behavior.
7. **DR measurement** — perform real recovery drills and record measured RPO/RTO.
8. **Observability** — measure SLI/SLO and error-budget behavior under representative production conditions.
9. **Provider validation** — validate intentionally configured live providers using production-safe credentials and record target-specific evidence.
10. **Tenant/RBAC acceptance** — validate Vendor → Reseller → Client isolation and authorization on the deployed target.
11. **Security testing** — authenticated DAST and independent security/pentest review; disposition findings.
12. **HA/failure recovery** — rehearse dependency/service failures and document recovery behavior.
13. **Operations** — verify alerting, escalation, staffed on-call and incident response.
14. **External acceptance** — complete Vendor, Reseller and Customer acceptance where applicable.
15. **Go-live decision** — reconcile all exceptions and explicitly authorize commercial publication.

### Commercial gate rule

`Engineering Ready ≠ Release Certified ≠ Production Deployed ≠ Commercially Accepted`

A passing repository certification is necessary but does not prove real deployment, live-provider behavior, measured SLO/DR, independent security review or customer acceptance.

## Stage 7 — External Production Certification & Customer Acceptance

**Issues:** #210 / #269 / #19 — **ACTIVE / EXTERNAL-PENDING**

| Priority | Work package | Status |
|---|---|---|
| P0 | Immutable release identity | `v1.4.17` published and exact-SHA certified at `b403c0dcdea579e017738a6fdea138c2b1a2999c` |
| P0 | External production deployment | Pending real infrastructure |
| P0 | Backup/restore & DR | Pending target evidence and measured RPO/RTO |
| P0 | Production SLO/SLI | Engineering contract exists; target measurement pending |
| P0 | Live provider validation | Pending |
| P0 | Vendor → Reseller → Client isolation/RBAC | External evidence pending |
| P0 | DAST / independent security review | External evidence pending |
| P0 | Networking / TLS / secret lifecycle | Target evidence pending |
| P0 | HA/failure recovery | Target rehearsal pending |
| P0 | Incident response / on-call | Live drill pending |
| P0 | Final external certification / customer acceptance | Pending #210/#269 |

### Recommended production infrastructure

Canonical baseline: `docs/current/PRODUCTION_SERVER_BASELINE.md`.

- **Staging:** 4 vCPU / 8 GB RAM / 100 GB SSD.
- **Initial production:** 8 vCPU / 16 GB RAM / 150–200 GB NVMe/SSD.
- **Growth:** 12–16 vCPU / 32 GB RAM / 250 GB+ NVMe/SSD.
- Ubuntu 24.04 LTS, fixed/public IP, TLS ingress, hardened firewall, encrypted off-host backups and centralized observability.
- Kubernetes is not required for the first external target; a hardened Docker-based deployment is sufficient when recovery and security controls are verified.
- GPU is optional for remote-provider inference and mainly relevant to local model inference/GPU OCR.

These sizing values are recommendations, not evidence that infrastructure has been provisioned.

## Workforce role taxonomy — clarification

The product now distinguishes two related but different catalogs:

1. **Customer operational starter templates** — the current seven templates exposed by the Customer Employee Templates surface: Sales Assistant, Customer Support Agent, Order Assistant, Catalog Assistant, Report Analyst, Document Analyst and Finance Assistant.
2. **AI Company workforce role catalog** — the broader organizational workforce model defined in `docs/blueprint/AI_COMPANY_FOUNDING_WORKFORCE.md`. This includes executive/governance roles such as AI Chief of Staff and **AI Internal Manager**, plus domain managers and specialist roles.

The AI Internal Manager is a managerial workforce role. It supervises specialized AI employees and prepares governed proposals for CEO decisions covering hiring/provisioning, retirement/removal, transfer/reassignment, replacement, urgent operational budgets and financial estimates. Its authority is **CEO approval by default**, with explicit delegation available for routine, non-financial, non-critical and reversible operations. Delegation is scoped, auditable and revocable; financial, material-resource, security-sensitive, legal, production-critical and irreversible actions remain approval-gated.

The role model remains:

`Human CEO → AI Board → AI Chief of Staff → AI Internal Manager → Specialized AI Workforce`

The existing governed workforce substrate, proposal flow and CEO approval boundary remain the authoritative implementation path. Adding or activating these managerial roles is a separate workforce/product slice and must not be represented as already implemented merely because the architecture documents define them.

### Next requested workforce roles

The next workforce implementation slice is explicitly defined as:

1. **AI Marketing & Advertising Manager**
2. **AI Graphic Designer**
3. **AI Software Developer**
4. **AI Trader**

All four roles operate under Internal Manager supervision and approval. The Internal Manager may execute or authorize their routine non-financial, non-critical and reversible work when the CEO has explicitly delegated that authority to the Internal Manager. The AI Trader remains financial/high-impact and actual capital allocation or financial execution still requires CEO/authorized-human approval.

These roles are planned candidates, not a claim that active instances already exist in the current certified release.

## Post-v1.4.11 workforce implementation checkpoint — 2026-09-23

The following post-release engineering slices are now merged on mainline and remain outside the v1.4.11 certification identity:

- Internal Manager workforce role catalog foundation.
- Durable CEO delegation with scoped, time-bounded, auditable authority.
- Runtime-bound Manager proposal provenance using governed Agent identity and durable Run identity.
- Manager proposals may target any existing catalog role or propose a new role definition; four specialized roles have first-party workforce role templates.
- Manager workforce dashboard reporting for capacity, queue status, terminal success rate and informational queue age; SLA compliance remains explicitly unconfigured until a tenant SLA target exists.
- Runtime enforcement of explicit workforce operations, with fail-closed role validation and human-approval gates.

No slice above provisions or activates an AgentInstance by itself, and none changes the immutable v1.4.11 release.

### Historical next engineering order (superseded by the 2026-09-29 checkpoint below)

1. Define explicit role-specific capability/tool bindings where concrete tools exist; do not infer role authority from tool names.
2. Add tenant-owned SLA target configuration and make dashboard compliance conditional on an explicit target.
3. Add runtime/e2e evidence for governed role operations and approval execution. **CURRENT NEXT ENGINEERING SLICE:** the canonical Run-path enforcement is implemented, but a semantic Workforce real-stack E2E matrix is not yet evidenced; the existing Compose stack has no market-data provider stub and the deterministic E2E AI provider does not emit `tool_calls`.
4. Reconcile exact-SHA certification only when a new release candidate is intentionally cut.

## Workforce semantic runtime evidence checkpoint — 2026-09-29

Repository audit conclusion:

- The governed role → operation → tool enforcement is implemented on the canonical Agent Run path after PR #827.
- Generic real-stack Agent WorkItem execution is validated through Celery and audit correlation.
- PR #832 closes the identified semantic Workforce runtime evidence gap for the currently implemented read-only market-research binding.
- The E2E-only deterministic provider and market-data provider are isolated to the certification/Compose path; production provider defaults and market-provider behavior remain unchanged.

### Completed evidence slice

1. Minimum E2E-only deterministic tool-call/provider infrastructure was added by PR #832.
2. The real WorkItem → Run → Celery → ToolRegistry → semantic handler path was executed successfully.
3. Persisted `tool.call` audit evidence and runtime binding correlation were verified.
4. Negative controls covered wrong-role denial, stale capability denial, approval-required operation denial and cross-tenant assignment denial.
5. The evidence index and current-priority records were reconciled after the PR #832 merge.

### Next engineering order

1. Keep the implemented semantic bindings under regression watch; do not add generic wrappers or reclassify unrelated tools.
2. Add new semantic workforce tools only when a concrete operation has a real tenant-safe domain/service and an explicit role-operation binding.
3. If the post-certification Workforce evidence is intentionally selected for release, create a new release candidate and run fresh exact-SHA certification; the v1.4.11 certification remains unchanged.
4. Continue the independent external-production sequence separately; repository engineering evidence does not close external deployment, live-provider, SLO/DR, security-review or customer-acceptance gates.
## Stage 9 — Autonomous Workforce Optimization

**Class:** PRODUCT / ENGINEERING — **CURRENT PLANNED SLICES IMPLEMENTED; INCLUDED IN THE v1.4.17 RELEASE LINE**

The planned Stage 9 slices were implemented and exact-SHA certified in v1.4.2; they remain part of the current v1.4.17 release line:

1. capability-aware workload routing;
2. task/risk/cost-aware model selection;
3. queue-aware workload balancing;
4. persisted workload-balancing evidence;
5. telemetry-backed Agent fitness;
6. Agent version fitness;
7. promotion evidence;
8. governed promotion;
9. governed rollback planning;
10. workforce capacity forecasting;
11. governed workforce scaling.

The control architecture is deliberately bounded:

`Forecast / Evidence → Governed Proposal → Existing Governance → Provision / Access Review / Activation`

Optimization cannot directly bypass identity, policy, approval, budget, lifecycle, concurrency, audit or execution controls.

## Stage 10 — AI Company Operating System

Long-term product vision: organization-wide command, policy-governed autonomy, agent/version registry, workforce analytics, orchestration and tenant-safe operations. This is not a current implementation claim.

## Cross-cutting Definition of Done

Every stage must preserve tenant isolation, RBAC, equivalent Human/Agent authorization, policy-driven approvals, scoped credentials, auditable identity, safe test execution, secret exclusion, one authoritative Alembic graph, reproducible CI/release artifacts, explicit evidence boundaries and documentation reconciliation.

## Evidence boundary

Repository tests, PR CI, CodeQL, local Docker, production-like validation, synthetic load and simulated providers are engineering/release evidence only. They do not substitute for live production deployment, measured production SLO/DR, independent security review or customer acceptance.

Certification never transfers automatically across SHAs.

## Canonical companion records

- `docs/00_START_HERE/VERSIONING_TRUTH.md`
- `docs/00_START_HERE/CURRENT_STATUS.md`
- `docs/00_START_HERE/CURRENT_PRIORITIES.md`
- `docs/current/PRODUCTION_SERVER_BASELINE.md`
- `docs/current/PRODUCTION_EVIDENCE_INDEX.md`
- `docs/current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md`
- `docs/current/STAGE_8_IMPLEMENTATION_STATUS.md`
- `docs/current/STAGE_9_IMPLEMENTATION_STATUS.md`
- `docs/engineering/STAGE_8_GOVERNANCE_AUDIT_CHECKLIST.md`
- `docs/blueprint/STAGE_8_ENGINEERING_EXECUTION_PLAN.md`
- `docs/releases/RELEASE_TRUTH_LEDGER.md`


## Product Experience Track — AI Company World & Dual-Mode Frontend — 2026-10-08

**Decision:** The product direction is now explicitly **Management Mode + World Mode** over one authoritative platform state. The reference gameplay is an interaction/visual benchmark, not a source-code or formula specification.

### Product objective

Build a real AI Company that customers can manage conventionally and explore as a living company headquarters. World Mode must make the existing governed Employee/Agent, WorkItem, Run, Workflow, Customer, Commerce, Usage and Billing capabilities visible and interactive without creating a second business state.

### Canonical specification

See `docs/blueprint/AI_COMPANY_WORLD_GAMEPLAY_SPEC.md`.

### Product mapping

- Building → AI Company HQ
- Office → Department/workspace
- Furniture → Capability/tool/knowledge/workstation resource
- Tenant → Customer/business account
- Rent → measurable revenue/savings/business outcome
- Employee → governed AI Employee/Agent Instance
- Happiness → operational health/workload/quality
- Repair → real operational maintenance
- Construction → department/capability unlock
- Tasks → business missions/activation objectives
- Player level → company progression
- Idle income → real background business activity

### Frontend target

Keep Next.js/React as the management shell. Add an explorable 2D/2.5D isometric World Mode using a dedicated renderer (initial recommendation: PixiJS). Desktop and mobile share one World Engine; input adapters differ for keyboard/mouse versus touch/virtual joystick.

The world is backend-driven. Employee animations and building states must derive from authoritative tenant-scoped data. No fake revenue, fake employee activity, permission bypass or game-only economy is allowed.

### Implementation order

1. World Foundation — renderer, isometric map, camera, movement, collision, buildings and Management↔World navigation.
2. Real Company — department and AI Employee projections, movement, backend-driven states and interaction.
3. Business Loop — WorkItems, customers/conversations, leads, orders, revenue/outcome and AI cost.
4. Progression — company progression, department unlocks, capability upgrades and missions.
5. Living World — day/night, visitors, ambient activity, events and return summary.
6. Polish — animation, VFX, audio, accessibility and performance.

### Mobile requirement

Mobile is first-class, not a reduced desktop port. It must use the same backend truth and World Engine with touch-specific input and presentation adapters.

### Current boundary

This is a new product/design track, not a claim that interactive World Mode is already implemented. The current W12 Virtual Office foundation remains a read-only presentation surface. Any application-code implementation must be validated on mainline and receives fresh exact-SHA certification before entering a certified release.

### External-production boundary

External production remains independent. Product World work is allowed to proceed locally while the project remains local-first; no external production deployment or customer-revenue claim is implied by this track.
