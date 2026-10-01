# AI Workforce Implementation Roadmap

## Status

**Post-v1.4.11 engineering roadmap — code-reconciled 2026-09-30**

This document is the implementation roadmap for turning the governed AI Workforce foundation into an actually executable internal AI company.

It is based on the repository code audit performed on 2026-09-30. It intentionally separates role/catalog definitions, governance/runtime infrastructure, concrete executable tools and handlers, real-stack evidence, and production/customer evidence.

A role listed in a blueprint is not considered implemented until the role has a real governed execution path.

## Current code-reconciled baseline

The repository now contains nine governed first-party workforce roles in the role catalog:
1. ai_internal_manager
2. ai_marketing_advertising_manager
3. ai_graphic_designer
4. ai_software_developer
5. ai_trader
6. ai_content_producer
7. ai_social_media
8. ai_sales_lead_generation
9. ai_website_employee

The role catalog defines explicit capability contracts and fail-closed binding rules.

The current code audit found:
- Internal Manager has concrete workforce coordination/reporting/budget/cost tools.
- Marketing Manager has concrete campaign-plan, content-coordination and growth-report tools.
- Trader has concrete read-only market-research, risk-analysis and trading-plan tools.
- Graphic Designer now has explicit governed semantic bindings for visual-asset operations; provider-backed image generation remains unconfigured.
- Software Developer now has a tenant-scoped Engineering Workspace semantic domain for artifact changes, change sets, test/lint/build staging, CI/repository proposals, health and rollback proposals.
- Content Producer now has governed text-content artifact operations.
- Social/Instagram now has governed channel/publication/comment/DM/analytics operation contracts; live Instagram provider credentials/API execution remain unconfigured.
- Dedicated image/video generation providers remain unconfigured; the creative domain records governed asset requests rather than faking provider execution.
- Sales/CRM now has a governed Sales & Lead Generation role with research/qualification/proposal/reporting operations; autonomous external outreach remains approval-gated and provider-dependent.
- Customer Success, SEO, QA and DevOps remain future dedicated workforce roles outside W0–W6.
- Website Employee now has governed requirements/implementation/test/build/preview/health/deploy/rollback operations; actual deployment remains dependent on the W2 repository/deployment provider chain.

### Evidence rule

A capability moves from planned to implemented only when all applicable layers exist:

Role → Operation → Capability Contract → Registered Tool → Tenant-safe Handler → Runtime Governance → Tests → Real-stack Evidence

Missing any required execution layer means the operation remains unavailable or partially implemented.

# Phased implementation plan

## Phase W0 — Evidence and contract reconciliation

**Goal:** make the repository documentation exactly match executable code before adding new workforce functionality.

### Deliverables
- Reconcile STATUS.md with the current Role/Tool Registry code.
- Maintain one authoritative binding inventory.
- Record role/operation/tool/handler/test/evidence status.
- Keep unsupported operations explicitly fail-closed.
- Add/update tests whenever a binding is added or removed.
- Separate certified v1.4.11 evidence from mutable post-release mainline evidence.

### Exit criteria
- No documentation claims an operation is executable unless the code path exists.
- Binding counts and role counts are generated/verified from code or checked against code in CI.
- Unsupported operations are visibly marked as unavailable.

**Priority: P0**

## Phase W1 — Internal Company Control Plane

**Goal:** make the AI Internal Manager capable of operating the company as a governed coordinator.

### Scope
- Workforce roster and active-instance state.
- Task assignment and reprioritization.
- Handoffs.
- Workload balancing.
- Capacity requests.
- CEO report.
- Budget/cost estimates.
- Proposal generation.
- Approval queue integration.
- KPI/SLA state.
- Cross-employee run correlation.
- Daily CEO operating brief.

### Important boundary
The Internal Manager coordinates existing capabilities. It must not invent execution authority merely because another tool has a similar name.

### Exit criteria
A deterministic real-stack scenario passes:
CEO goal → Internal Manager → assign work → specialized employee → result → verification → CEO report
with tenant identity, audit provenance and approval controls verified.

**Priority: P0**

## Phase W2 — Engineering Employee

**Goal:** make ai_software_developer a real governed execution employee.

### Build a dedicated Engineering Workspace domain
Required first-party tools should be explicit and independently governed:
1. workspace read/list
2. file create
3. file edit
4. file delete
5. patch/change-set creation
6. test execution
7. lint/type-check
8. build
9. Git branch/change-set preparation
10. commit proposal
11. pull-request proposal
12. CI/status inspection
13. deployment proposal
14. health check
15. rollback proposal

### Safety
- Workspace and repository scope must be tenant-bound.
- Production-critical/security-sensitive changes remain approval-gated.
- No arbitrary shell capability should be silently substituted for these semantic operations.
- Every change must have provenance and a reversible path where possible.

### Exit criteria
Developer task → workspace change → tests → review/proposal → approval when required → deploy → health check → audit
works end-to-end on a controlled test repository.

**Priority: P0**

## Phase W3 — Content & Creative Workforce

**Goal:** turn content planning into actual content production.

### Content Production Employee
Capabilities:
- long-form article
- social caption
- short-form variant
- CTA
- content calendar
- brand/voice policy
- SEO-aware content brief
- repurposing
- content QA

### Graphic Designer
Introduce a real Creative/Media domain:
- create visual asset
- revise asset
- brand variant
- campaign creative
- asset metadata/versioning
- approval state
- provider selection

### Generation provider architecture
Use a provider abstraction:
Local → Free/low-cost API → Paid API
Paid generation must remain approval-gated.

### Exit criteria
A content request can produce a governed text + creative package with stored artifacts, provenance and approval state.

**Priority: P1**

## Phase W4 — Social / Instagram Employee

**Goal:** convert content packages into governed distribution.

### Capabilities
- account/channel connection
- publish post
- publish reel
- publish story
- schedule publication
- read comments
- classify/triage comments
- read/respond to DMs where permitted
- analytics retrieval
- publication status
- failure/retry handling

### Governance
Publishing and external messaging are Tier 2 external-impact actions. Account credentials and provider scopes must be tenant-owned and never exposed to model context.

### Exit criteria
Content Employee → Social Employee → approval → Instagram provider → publish → verify → analytics
passes against a test/sandbox-capable integration or explicitly documented provider test environment.

**Priority: P1**

## Phase W5 — Sales & Lead Generation Workforce

**Goal:** make the Internal Company capable of generating and managing its own pipeline.

### Capabilities
- lead research
- lead qualification
- CRM enrichment
- outreach draft
- follow-up queue
- proposal preparation
- meeting-request preparation
- pipeline reporting
- conversion attribution

### Human boundary
External outreach, contractual commitments and material commercial actions require explicit policy/approval.

### Exit criteria
research → qualify → CRM → draft outreach → human approval → send → response → follow-up → pipeline
is auditable end-to-end.

**Priority: P1**

## Phase W6 — Website Employee

**Goal:** allow the AI Company to create and operate its own website.

### Capabilities
- requirements/specification
- UX/content plan
- implementation
- asset integration
- automated tests
- accessibility checks
- build
- preview
- deployment
- health check
- rollback
- post-release issue detection

This phase depends on W2 Engineering Workspace and W3 Content/Creative capabilities.

### Exit criteria
The Internal Manager can assign a website change and the governed engineering chain can implement, test, deploy, verify and report the result.

**Priority: P1**

## Phase W7 — SEO & Growth Employee

**Goal:** create a measurable organic-growth loop.

### Capabilities
- keyword/topic research
- content opportunity analysis
- on-page recommendations
- technical SEO checks
- internal-link recommendations
- content briefs
- search-performance ingestion
- growth reporting
- experiment proposals

No claim of actual search-engine impact is made without external measurement.

### Exit criteria
research → opportunity → content/technical task → implementation → measurement → report
is operational.

**Priority: P2**

## Phase W8 — Customer Success / Support Employee

**Goal:** operate the customer lifecycle after acquisition.

### Capabilities
- inbox triage
- customer profile/context retrieval
- support drafting
- escalation
- churn-risk evidence
- onboarding follow-up
- satisfaction reporting
- knowledge-base maintenance proposals

Customer-facing responses remain governed external-impact actions.

**Priority: P2**

## Phase W9 — QA & DevOps Employees

**Goal:** close the autonomous software delivery loop.

### QA
- test-plan generation
- regression execution
- Playwright/API checks
- defect creation
- release evidence

### DevOps/SRE
- CI status
- deployment orchestration
- health checks
- logs/metrics
- incident detection
- rollback
- backup/restore verification

Production-critical actions remain approval-gated.

**Priority: P2**

## Phase W10 — Internal AI Company Dogfood

**Goal:** make AI-Employee its own first customer.

### Target operating loop
CEO → Internal Manager → Research → Marketing → Content → Creative → Sales → Customer Success → Developer → QA → DevOps → Website → Analytics → Internal Manager

### First business objective
**First Revenue Generated by AI Workforce**

The first measurable objective is not number of employees. It is a real qualified lead, customer conversation, pilot, and eventually paid customer generated and processed through the governed workforce.

### Cost principle
Use the local machine and local models where practical. Add paid APIs, external infrastructure and heavier compute only when a real workload requires them and the economics are covered by customer revenue.

### Exit criteria
At least one real business workflow is completed repeatedly with measurable outcome, human approval at consequential boundaries, audit trail, cost measurement, failure/recovery handling, and repeatability.

**Priority: P0 after W1–W6 foundations**

# Implementation order

The recommended engineering order is:

W0 → W1 → W2 → W3 → W4 → W5 → W6 → W7 → W8 → W9 → W10

W10 is the business validation loop, not a final finish-everything-first milestone.

The project should begin dogfooding as soon as W1 plus the minimum tools for one complete revenue workflow exist.

## Build rule
Do not implement a workforce role because it appears in the catalog.
Implement a role when there is a real workflow that needs it.
Do not add a generic wrapper merely to make a capability appear executable.

For every new capability:
1. define the semantic operation;
2. define its side effects and risk;
3. define tenant/security boundaries;
4. implement a dedicated domain/service where necessary;
5. register a canonical Tool;
6. bind Role → Operation → Tool explicitly;
7. add negative/authorization tests;
8. add real-stack evidence;
9. update the authoritative status;
10. only then call the capability implemented.

## Definition of Done
A workforce role is Executable only when role, template where required, capability contract, Tool Registry binding, handler, permissions, approvals, tenant scope, runtime provenance, automated tests and relevant real-stack evidence all exist.

A role with only catalog/contract/template definitions is Planned/Partial, not Executable.

## Release boundary
All post-v1.4.11 workforce implementation is mainline engineering until a new release candidate is created and exact-SHA certification is rerun.
The immutable v1.4.11 certification remains unchanged.
## Implementation checkpoint — 2026-09-30

The W0–W6 engineering pass has started on mainline after the v1.4.11 certified boundary.

### W0 — implemented
- Added `backend/scripts/workforce_binding_inventory.py` as the code-derived Role → Operation → Tool inventory.
- Added focused W0 tests.
- The registry dispatch boundary now treats every `workforce_*` tool through the same governed context path instead of maintaining a growing hand-written allowlist.
- Unsupported operations remain fail-closed.

### W1 — existing foundation reconciled
- Internal Manager coordination, handoff, balancing, capacity, CEO reporting, budget and cost tools remain governed by the existing runtime/delegation controls.
- Existing real-stack workforce semantic certification remains the evidence path for runtime identity, role binding, stale-contract denial, approval denial and tenant isolation.
- W1 is not declared fully closed until the complete CEO → assignment → specialist → verification → CEO-report scenario is recorded as dedicated real-stack evidence.

### W2 — semantic Engineering Workspace foundation implemented
Added governed engineering operations for tenant-scoped workspace artifacts, change-set creation, test/lint/build staging, Git/CI proposals, deployment proposal, health check and rollback proposal.
- Workspace artifacts are tenant-namespaced through the existing storage boundary.
- External repository/deployment operations remain provider-backed proposals; no arbitrary shell execution was introduced.
- Production/deployment/rollback boundaries are approval-gated.

### W3 — Content & Creative foundation implemented
- Added executable Content Producer role/template and governed text-content artifact operations.
- Added concrete bindings for Graphic Designer visual-asset operations.
- Creative provider execution remains explicitly unconfigured rather than being faked by a generic tool.

### W4 — Social/Instagram governance foundation implemented
- Added Social Media role/template and semantic channel/publication/comment/DM/analytics operations.
- External publication and messaging are approval-gated.
- No Instagram credential/provider adapter is claimed as live until a tenant-owned provider integration is configured and real-stack evidence exists.

### W5 — Sales & Lead Generation governance foundation implemented
- Added Sales/Lead Generation role/template and research/qualification/CRM/draft/follow-up/proposal/reporting operations.
- External outreach and material commercial actions remain approval-gated.
- Existing CRM infrastructure is not silently treated as an autonomous outreach provider.

### W6 — Website Employee foundation implemented
- Added Website Employee role/template and requirements → implementation → tests → build → preview → health → deploy/rollback semantic operations.
- Deploy and rollback are approval-gated.
- W6 depends on the W2 engineering provider chain for actual repository deployment; no production deployment is claimed by these semantic foundations alone.

### Verification rule
These phases are **mainline implementation**, not a new certified release. v1.4.11 SHA `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f` remains immutable. A future release candidate must rerun exact-SHA certification after the W0–W6 changes are validated.



## W1 implementation checkpoint — 2026-10-01

A dedicated real-stack certification harness now exists at `backend/scripts/e2e_workforce_w1_control_plane_verify.py`.

It exercises:
- CEO-owned bounded delegation to the Internal Manager;
- governed Manager `assign_task`;
- specialist Agent WorkItem dispatch and successful Run;
- persisted execution/audit verification;
- governed Manager `prepare_ceo_report` against the resulting tenant workload.

This W1 exit criterion is now **VERIFIED**. GitHub Actions run `36830129984` / job `110264598687` completed successfully against the Docker/Celery stack. The run verified database readiness, application health, CEO delegation, governed Manager `assign_task`, specialist Agent WorkItem → Run execution, persisted audit/provenance, and Manager CEO report generation. Certification output included `WORKFORCE W1 CONTROL-PLANE REAL-STACK E2E PASS`; specialist Run evidence was `cd46f769-0823-4141-b012-72c0f7e6b0f2`.

### W1 evidence corrections discovered during certification
- Manager delegation lookup was corrected to identify the Manager by the governed `workforce_role_code=ai_internal_manager` capability contract rather than the obsolete fixed template slug.
- The W1 real-stack workflow was corrected to start the transactional-outbox dispatcher and Celery beat services, so persisted `agent.run.execute` handoffs are actually delivered to the execution worker.
- The W1 fixture license was corrected to include the Manager tools it actually executes.

W1 is now evidenced on mainline. This evidence remains post-v1.4.11 engineering evidence and does not modify the immutable certified release.

