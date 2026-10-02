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

### W2 verification checkpoint — 2026-10-01

W2 semantic foundation is now **VERIFIED on the real stack** for its governed artifact and approval/provider-boundary behavior. GitHub Actions run `36832544726` / job `110272236014` passed. Evidence covers tenant-scoped workspace create/list/edit, cross-tenant isolation, durable unique change sets, fail-closed test/lint/build provider boundaries, and approval-gated deployment proposals.

This does **not** close the live engineering-provider gap: Git hosting, CI execution, deployment, and health providers remain explicitly `not_configured` until a provider adapter is implemented and separately evidenced.

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



## W3 real-stack certification checkpoint — 2026-10-01

W3 Content & Creative now has dedicated real-stack evidence through `backend/scripts/e2e_workforce_w3_content_creative_verify.py` and `.github/workflows/workforce-w3-e2e.yml`.

GitHub Actions run `36882689747` / job `110438160948` completed successfully. Evidence verified:
- Content Producer governed Run → durable versioned content artifact.
- Graphic Designer governed Run → durable creative request.
- artifact provenance and tenant scoping.
- cross-tenant artifact read denial.
- persisted artifact approval state.
- `external_content_commitment` remains explicitly human-approval-required in the authoritative role contract.
- creative provider execution remains explicitly `not_configured`; no provider execution was faked.

Certification output included `WORKFORCE W3 CONTENT-CREATIVE REAL-STACK E2E PASS`.

W3 is therefore **VERIFIED on the real stack** for its current governed Content & Creative scope. This is post-v1.4.11 mainline evidence and does not modify the immutable certified release.


## W4 real-stack governance checkpoint — 2026-10-01

W4 Social/Instagram now has dedicated real-stack governance evidence through `backend/scripts/e2e_workforce_w4_social_governance_verify.py` and `.github/workflows/workforce-w4-e2e.yml`.

GitHub Actions run `36883693486` / job `110441538977` completed successfully. Evidence verified:
- Social Employee governed Run for a non-external read operation.
- Durable tenant-scoped social operation artifacts with provenance.
- Approved publish proposal remains an auditable proposal rather than a provider execution.
- Cross-tenant social artifact read denial.
- External publication remains approval-gated.
- Instagram provider execution remains explicitly `not_configured`; no publication was attempted or faked.

Certification output included `WORKFORCE W4 SOCIAL GOVERNANCE REAL-STACK E2E PASS`.

This closes the **W4 governance/provider-boundary checkpoint**, but does **not** close the full W4 exit criterion. Actual Instagram connect/publish/schedule/DM execution still requires a tenant-owned provider integration and a sandbox/test-capable provider certification. W4 full provider execution is therefore **NOT VERIFIED**.


## W5 real-stack governance checkpoint — 2026-10-01

W5 Sales & Lead Generation now has dedicated real-stack governance evidence through `backend/scripts/e2e_workforce_w5_sales_governance_verify.py` and `.github/workflows/workforce-w5-e2e.yml`.

GitHub Actions run `36884126600` / job `110442982171` completed successfully. Evidence verified:
- Sales Employee governed research Run.
- Durable tenant-scoped sales artifacts with provenance.
- Approved external-outreach proposal remains a proposal and does not execute externally.
- Cross-tenant sales artifact read denial.
- External outreach remains approval-gated.
- CRM/outreach provider execution remains explicitly `not_configured`.

Certification output included `WORKFORCE W5 SALES GOVERNANCE REAL-STACK E2E PASS`.

This closes the **W5 governance/provider-boundary checkpoint**, but does **not** close the full W5 exit criterion. Actual CRM integration, outreach delivery, response ingestion, and follow-up execution require tenant-owned providers and separate real-stack evidence. Full W5 external execution is therefore **NOT VERIFIED**.


## W6 real-stack governance checkpoint — 2026-10-01

W6 Website Employee now has dedicated real-stack governance evidence through `backend/scripts/e2e_workforce_w6_website_governance_verify.py` and `.github/workflows/workforce-w6-e2e.yml`.

GitHub Actions run `36884770848` / job `110445143994` completed successfully. Evidence verified:
- Website Employee governed Run.
- Durable unique tenant-scoped website change artifact.
- Approved deployment remains an auditable proposal.
- Cross-tenant website artifact read denial.
- Deployment remains approval-gated.
- Website deployment provider execution remains explicitly `not_configured`.

Certification output included `WORKFORCE W6 WEBSITE GOVERNANCE REAL-STACK E2E PASS`.

This closes the **W6 governance/provider-boundary checkpoint**, but does **not** close the full W6 exit criterion. Actual repository implementation/deployment/health/rollback execution requires the W2 provider chain to be configured and separately evidenced. Full W6 external execution is therefore **NOT VERIFIED**.


## W4 real-stack certification checkpoint — 2026-10-01

W4 Social/Instagram governance now has dedicated real-stack evidence through `backend/scripts/e2e_workforce_w4_social_governance_verify.py` and `.github/workflows/workforce-w4-e2e.yml`.

GitHub Actions run `36885609693` / job `110448029552` completed successfully. Evidence verified:
- Social Employee governed read/analytics Run.
- tenant-scoped durable social artifact and provenance.
- approved publication proposal remains an internal proposal rather than an external publication.
- publication approval state is pending and governed by the Social role contract.
- cross-tenant artifact access is denied.
- Instagram provider execution remains explicitly `not_configured`.
- no Instagram external side effect is claimed or executed.

Certification output included `WORKFORCE W4 SOCIAL GOVERNANCE REAL-STACK E2E PASS`.

W4 is therefore **VERIFIED on the real stack** for its current governed Social/Instagram scope. This is post-v1.4.11 mainline evidence and does not modify the immutable certified release.


## W5 real-stack certification checkpoint — 2026-10-01

W5 Sales & Lead Generation governance now has dedicated real-stack evidence through `backend/scripts/e2e_workforce_w5_sales_governance_verify.py` and `.github/workflows/workforce-w5-e2e.yml`.

GitHub Actions run `36886034231` / job `110449446757` completed successfully. Evidence verified:
- Sales Employee governed research Run.
- tenant-scoped durable sales artifact and provenance.
- approved external-outreach proposal remains an internal proposal.
- outreach approval state is pending and governed.
- cross-tenant artifact access is denied.
- CRM/outreach provider execution remains explicitly `not_configured`.
- no external outreach side effect is claimed or executed.

Certification output included `WORKFORCE W5 SALES GOVERNANCE REAL-STACK E2E PASS`.

W5 is therefore **VERIFIED on the real stack** for its current governed Sales & Lead Generation scope. This is post-v1.4.11 mainline evidence and does not modify the immutable certified release.


## W7 real-stack certification checkpoint — 2026-10-01

W7 SEO & Growth now has a dedicated governed semantic domain, first-party role contract, canonical SEO/growth tools, and real-stack certification through `backend/scripts/e2e_workforce_w7_seo_growth_verify.py` and `.github/workflows/workforce-w7-e2e.yml`.

GitHub Actions run `36887142892` / job `110453250609` completed successfully. Evidence verified:
- SEO & Growth Employee governed research Run.
- durable tenant-scoped SEO/growth artifact with provenance.
- SEO experiment proposal is approval-gated and requires an exact matching approved tool request.
- cross-tenant artifact access is denied.
- search/growth provider execution remains explicitly `not_configured`; no search-engine impact is claimed.

Certification output included `WORKFORCE W7 SEO GROWTH REAL-STACK E2E PASS`.

W7 is therefore **VERIFIED on the real stack** for its current governed SEO & Growth scope. This is post-v1.4.11 mainline evidence and does not modify the immutable certified release.

## W8 real-stack certification checkpoint — 2026-10-01

W8 Customer Success & Support now has dedicated real-stack evidence through `backend/scripts/e2e_workforce_w8_customer_success_verify.py` and `.github/workflows/workforce-w8-e2e.yml`.

GitHub Actions run `36889736209` / job `110462022257` completed successfully at commit `6705607b06d29a70f5e30785eef6d154fdea6178`. Evidence verified:
- Customer Success governed research Run.
- approval-gated customer action with an exact matching approved tool request.
- durable tenant-scoped artifact and provenance.
- cross-tenant isolation.
- provider execution remains explicitly `not_configured`; no external customer action was faked.

Certification output included `WORKFORCE W8 CUSTOMER SUCCESS REAL-STACK E2E PASS`.

W8 is therefore **VERIFIED on the real stack** for its current governed Customer Success & Support scope. This is post-v1.4.11 mainline evidence and does not modify the immutable certified release.

## W9 real-stack certification checkpoint — 2026-10-01

W9 QA & DevOps now has dedicated real-stack evidence through `backend/scripts/e2e_workforce_w9_qa_devops_verify.py` and `.github/workflows/workforce-w9-e2e.yml`.

The first W9 certification attempt exposed a real registry collision: `workforce_rollback_proposal` was already owned by the Engineering domain. W9 was corrected to use the dedicated `workforce_qa_rollback_proposal` tool, preserving the existing Engineering binding rather than overwriting or duplicating it.

Final GitHub Actions run `36891616509` / job `110468909696` completed successfully at commit `5887c26c727fd2681cc1dd71fc17f0a475c9e80a`. Evidence verified:
- QA & DevOps governed research Run.
- approval-gated deployment proposal with exact approval governance.
- durable tenant-scoped artifact and provenance.
- cross-tenant isolation.
- provider execution remains explicitly `not_configured`; no deployment or rollback side effect was faked.
- Docker stack shutdown completed cleanly without the prior CI-hang pattern.

Certification output included `WORKFORCE W9 QA DEVOPS REAL-STACK E2E PASS`.

W9 is therefore **VERIFIED on the real stack** for its current governed QA & DevOps scope. This is post-v1.4.11 mainline evidence and does not modify the immutable certified release.

## W10 entry checkpoint — 2026-10-01

W0–W9 are now evidenced on mainline at their applicable scope. W10 is the next implementation phase: internal AI Company dogfooding and the first measurable revenue workflow.

W10 must not be treated as a nominal role-count exercise. The first target is one repeatable, governed business workflow that can produce a qualified lead and customer conversation, with human approval at consequential boundaries, complete provenance/audit evidence, cost measurement, and failure/recovery handling.

The immutable v1.4.11 release boundary remains unchanged. All W10 work is post-v1.4.11 mainline engineering until a future release candidate is created and separately certified.

## W10 real-stack dogfood foundation checkpoint — 2026-10-01

The first Internal AI Company dogfood pipeline is now implemented and evidenced through `backend/scripts/e2e_workforce_w10_dogfood_verify.py` and `.github/workflows/workforce-w10-dogfood-e2e.yml`.

GitHub Actions run `36892642090` / job `110472293257` completed successfully. The governed pipeline exercised:
1. lead research;
2. lead qualification;
3. content brief;
4. article production;
5. content QA;
6. outreach drafting;
7. approval-gated external outreach proposal.

Certification evidence included:
- lead research and qualification PASS;
- content brief → article → QA PASS;
- outreach draft PASS;
- exact approval governance PASS;
- external provider fail-closed PASS with `provider_execution=not_configured`;
- `W10 REVENUE WORKFLOW FOUNDATION REAL-STACK E2E PASS`.

Example certification artifacts:
- sales research ID `e910cd61-5df1-4600-9f9b-13fe3a100635`;
- qualification ID `042b7cdc-a63c-47ea-a7f7-9c9a97b009b5`;
- content article ID `e34d6671-caf0-4eac-b53b-129daa40fd24`;
- outreach proposal ID `fe6e3366-719b-42b9-a60f-d4d20e4fb1ac`.

### W10 status boundary

The **revenue workflow foundation is VERIFIED on the real stack**.

The **full revenue outcome is NOT VERIFIED**. No real external outreach, customer conversation, or revenue is claimed because the CRM/outreach provider is still `not_configured`. The next W10 work item is therefore provider-backed business execution plus measurement, not another nominal employee/tool layer.

This remains post-v1.4.11 mainline engineering evidence.


## W10 internal CRM dogfood checkpoint — 2026-10-02

The W10 dogfood foundation was extended with a governed internal CRM mutation and read-only pipeline/forecast loop. The certification harness now exercises:
1. an approval-gated internal CRM deal creation;
2. tenant-scoped pipeline summary;
3. probability-weighted 30-day forecast;
4. the existing approval-gated external-outreach proposal with the provider still fail-closed.

Final GitHub Actions run `36968628359` / job `110717725998` completed successfully at commit `183d46f79fdc723ad70f4c64529ec095fec0d8ea`.

Certification evidence:
- `W10 INTERNAL CRM DEAL + PIPELINE + FORECAST PASS`;
- deal ID `6d37195f-f20d-4b2a-aa9d-5cb27ef42389`;
- weighted pipeline `62,500,000 IRR`;
- 30-day forecast `62,500,000 IRR`;
- `W10 APPROVAL GOVERNANCE PASS`;
- `W10 EXTERNAL PROVIDER FAIL-CLOSED PASS provider_execution=not_configured`;
- `W10 REVENUE WORKFLOW FOUNDATION REAL-STACK E2E PASS`.

A contract correction was made in the Sales semantic domain: `external_side_effect` now represents the governed operation class, while provider execution and `execution.executed` separately represent whether an external effect actually occurred. This preserves fail-closed behavior while keeping the audit classification accurate.

The **W10 internal revenue-workflow foundation is VERIFIED on the real stack**. The **full revenue outcome remains NOT VERIFIED**: no external outreach, customer conversation, or revenue is claimed while the CRM/outreach provider remains `not_configured`.

This remains post-v1.4.11 mainline engineering evidence and does not modify the immutable v1.4.11 certification boundary.


## W10 governed SMTP provider checkpoint — 2026-10-02

W10 now exercises the configured Sales outreach provider path through the existing transactional outbox and dedicated email worker. The E2E environment uses an isolated deterministic SMTP sink; this is provider-path evidence only and is not a real customer delivery.

A real integration gap discovered during certification was fixed: the Sales semantic domain carries tenant IDs as storage-safe strings, while the transactional outbox governance context is UUID-bound. The provider now normalizes the tenant ID to UUID before enqueueing, preserving the deferred Agent governance binding instead of failing with a tenant-context mismatch.

The W10 workflow was also corrected to start the dedicated `worker-email` service. Previously the outbox could be queued without the email delivery worker being present in this certification stack.

Final GitHub Actions run `36969414362` / job `110720048581` completed successfully at commit `69aa536be417046c688950de0cc1e3512c7fbbcc`.

Evidence:
- `W10 SMTP OUTREACH PROVIDER QUEUE PASS`;
- `W10 APPROVAL GOVERNANCE PASS`;
- `W10 SMTP EXTERNAL DELIVERY PASS` against the isolated E2E SMTP sink;
- complete Docker stack shutdown PASS;
- `W10 FULL REVENUE OUTCOME NOT_VERIFIED: E2E SMTP sink only; no real customer delivery or revenue claimed`.

This closes the **governed provider-path / deferred email execution checkpoint** for W10. It does not close real external customer outreach, response ingestion, customer conversation, or revenue generation. Those remain **NOT VERIFIED** until a tenant-owned real SMTP/provider configuration is exercised against an authorized recipient and separately evidenced.

This remains post-v1.4.11 mainline engineering evidence and does not modify the immutable v1.4.11 certification boundary.


## W10 sales response ingestion & attribution checkpoint — 2026-10-02

The W10 provider-path was extended into a governed sales engagement measurement loop. Outreach delivery is correlated from the transactional outbox to an immutable tenant-scoped sales engagement event, and synthetic inbound responses are recorded through an idempotent event contract.

Implementation:
- `backend/app/services/workforce_sales_engagement.py` provides tenant-scoped engagement events and attribution summaries using the immutable audit ledger;
- delivery events are emitted by the dedicated email worker after SMTP acceptance, and the E2E no longer manually injects the delivery event;
- outbound records carry stable Sales correlation metadata through the transactional outbox, including `tool_call_id` and `deal_id`;
- response ingestion is idempotent by a stable `event_key`;
- the W10 certification replays the same inbound response and verifies that it resolves to the original event rather than creating a duplicate;
- attribution evidence covers `sent=1, delivered=1, responded=1`;
- the E2E workflow remains isolated to the deterministic SMTP sink.

Final GitHub Actions run **36971624051** / job **110726669120** completed successfully at commit **3eff76c8a2217ceb91339bbaed692f193b3d59cb**.

Evidence:
- `W10 SMTP OUTREACH PROVIDER QUEUE PASS`;
- `W10 SALES DELIVERY EVENT INGESTION PASS`;
- `W10 SALES DELIVERY + RESPONSE INGESTION PASS`;
- `W10 SALES RESPONSE IDEMPOTENCY PASS`;
- `W10 SALES ATTRIBUTION PASS sent=1 delivered=1 responded=1`;
- `W10 SMTP EXTERNAL DELIVERY PASS`;
- complete Docker shutdown PASS;
- `W10 FULL REVENUE OUTCOME NOT_VERIFIED: E2E SMTP sink only; no real customer delivery or revenue claimed`.

The W10 governed sales engagement measurement checkpoint is **VERIFIED on the real stack** for the isolated E2E provider path. The new evidence specifically verifies that the delivery event is produced by the email worker and reaches the immutable ledger, rather than being synthetically inserted by the certification script. Real customer response, customer conversation, and revenue generation remain **NOT VERIFIED**. The current evidence proves governed queueing, SMTP-sink acceptance, worker-generated delivery-event recording, deterministic response ingestion, replay idempotency, and attribution mechanics—not real-world customer behavior or revenue.

This remains post-v1.4.11 mainline engineering evidence and does not modify the immutable v1.4.11 certification boundary.
