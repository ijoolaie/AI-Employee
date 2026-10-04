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


## W10 live SMTP + mailbox response checkpoint — 2026-10-03

The W10 dogfood revenue workflow has now crossed from isolated provider-path evidence into a real live SMTP/mailbox response loop.

Final GitHub Actions live certification:
- Run **37103195020**
- Job **111146601368**
- SHA **7f7b0d9c917b0deb8891e23a862a227ef3bc939d**
- Workflow: `Workforce W10 Live SMTP Certification`
- Result: **SUCCESS**

Live evidence:
- governed SMTP queue: PASS;
- live SMTP send/provider acceptance: PASS;
- IMAP mailbox connection and INBOX selection: PASS;
- mailbox response discovered during polling attempt **3/12**;
- response correlation against the application Message-ID: PASS;
- live sales response ingestion: PASS;
- live response idempotency replay: PASS;
- live attribution: **sent=1 delivered=1 responded=1**.

The certification logs show the mailbox response was actually discovered after the INBOX message count increased from 83 to 84, with `In-Reply-To` search matches and `valid_responses=1`. This is live provider evidence, not an SMTP-sink simulation.

### W10 status boundary after live certification

**VERIFIED:**
- live SMTP application/provider acceptance;
- live mailbox response observation;
- live response correlation;
- live response ingestion;
- live response idempotency;
- live sales attribution mechanics.

**NOT VERIFIED:**
- independent verification that the responding mailbox identity represents a customer;
- customer/conversation qualification;
- payment or revenue outcome.

The immutable `v1.4.11` certification boundary remains unchanged. This evidence belongs to post-v1.4.11 mainline SHA `7f7b0d9...` and does not transfer certification to that SHA.

The next W10 work should therefore focus on **customer-outcome evidence** (qualified customer conversation → proposal/pilot → payment/revenue event) and on reconciling the authoritative current-status/evidence documents, rather than repeating the already verified live SMTP response loop.


## Phase W11 — Humanized Employee Identity & Visual Presentation

**Status: FOUNDATION IMPLEMENTED — post-v1.4.11 mainline; not release-certified.**

**Goal:** give every Employee a stable human-readable identity and optional visual presentation without coupling identity to heavy inference or video generation.

### Identity contract

- `Employee.name` is the stable display name and survives EmployeeVersion changes.
- `Employee.avatar_url` is optional stable presentation metadata stored on the Employee identity, not on EmployeeVersion.
- The backend treats `avatar_url` as inert metadata: it does not fetch, execute, proxy, or dereference the URL.
- Tenant isolation follows the existing Employee authorization path; system Employees remain platform-owned and tenant Custom Employees remain tenant-scoped.
- Historical Runs continue to resolve the immutable EmployeeVersion; changing a name/avatar does not rewrite historical execution definitions.

### Presentation tiers

1. **Name + static avatar:** lightweight and available without GPU inference.
2. **Name + avatar + voice:** optional presentation layer; TTS/provider work is separate from core Employee identity.
3. **Real-time visual conversation:** future capability. Camera/vision, LLM, TTS and talking-avatar/lip-sync processing must be provider-backed and isolated from the core runtime. It is not claimed implemented by this phase.

### Engineering boundary

Do not store generated image bytes in the Employee row. Prefer durable object/media storage and reference metadata. Do not make the Agent/Employee runtime download arbitrary avatar URLs. Visual-chat providers must be explicit capabilities with tenant, permission, approval and audit controls when they introduce external side effects or paid compute.

### Current implementation

- Added nullable `employees.avatar_url` via Alembic migration `w11_employee_avatar_identity`.
- Employee create/read schemas expose `avatar_url`.
- Employee identity creation persists the optional avatar reference.
- No image generation, camera processing, lip-sync or video streaming is enabled by this change.
- No GPU requirement is introduced by the identity foundation.

### Next acceptance slices

- UI employee cards/profile with name + avatar.
- Media storage contract with tenant-safe asset ownership and lifecycle.
- Optional voice profile contract.
- Visual-chat session contract: text/voice/vision transport, provider selection, latency/cost limits, consent and audit.
- Real-provider evidence before claiming visual-chat execution.

**Evidence rule:** implementation of identity metadata is not evidence that visual chat or a real avatar provider is operational.

## Product Experience & Monetization Expansion — 2026-10-03

The workforce product is expanding from an AI operations dashboard into a visual **AI Company Headquarters**, while the governed Workforce Runtime remains the single source of business truth.

### Product principles
1. Game-like presentation, enterprise-grade semantics.
2. Presentation is separate from execution and authorization.
3. Cosmetics never bypass governance, permissions, approvals or tenant isolation.
4. Dashboard, Executive Office, Virtual Office, mobile and future 3D/VR views consume the same backend truth.
5. Commerce-ready contracts should not couple marketplace features to core authorization.

### Planned experience roadmap

**W12 — Virtual Office Foundation**
- CEO/Executive Office as the primary command interface.
- Employee floor, department clusters, project rooms and meeting-room presentation.
- Real employee states such as WORKING, WAITING_APPROVAL, BLOCKED, MEETING, IDLE, COMPLETED and ESCALATED.
- Read-only presentation contracts over Workforce API data.
- Frontend must never infer business state.

**W13 — Customer HQ Progression**
- Office tier derived from authoritative customer metrics and entitlements.
- Inputs may include subscription/usage, active projects, employee count and enabled capabilities.
- Expandable rooms, floors and clusters; Enterprise/white-label presentation options.
- Presentation tier is not an authorization shortcut.

**W14 — Employee Appearance & Customization**
- Stable visual identity separate from business identity.
- Avatar, gender presentation, appearance, hairstyle, body presentation, clothing and accessories where supported.
- Professional presentation settings such as language and communication style.
- Role, permissions and capabilities remain independent of appearance.

**W15 — Wardrobe & Cosmetic Marketplace**
- Clothing/uniforms, accessories, office furniture/decorations, themes and seasonal or limited collections.
- Tenant-scoped, auditable, non-authoritative commercial assets.

**W16 — Skills Marketplace**
- Versioned, governed skill packages attachable to eligible employees.
- Skill installation cannot silently expand permissions.
- Paid skills may be recurring or one-time products.

**W17 — Employee Career & Reputation Presentation**
- Work history, tenure, completed projects and verified operational KPIs.
- Achievements/badges are presentation metadata and cannot fabricate business performance.

**W18 — Virtual Meeting Rooms**
- CEO-to-employee conversations and multi-employee governed sessions.
- Project-focused meeting context.
- Meeting state tied to real Workforce sessions/runs.

**W19 — Voice & Visual Interaction**
- Voice input/output, TTS and visual/avatar providers behind explicit contracts.
- Camera, lip-sync and video remain optional presentation capabilities.
- Heavy GPU/video workloads remain isolated from core runtime.

**W20 — Third-party Employee Marketplace**
- Employee templates, specialist personas, governed skill bundles, workflows and visual packs.
- Third-party packages require validation, versioning, permissions review and tenant isolation.

**W21 — AI Business Network**
- Future governed company-to-company workforce requests, partner/customer handoffs and controlled agent-to-agent business workflows.
- Commercial and contractual boundaries remain explicit and approval-gated.

### Employee identity boundary

Employee business identity contains role, permissions, capabilities, memory and work history. Presentation identity contains avatar, appearance, clothing, accessories and office placement. Changing presentation must never change business authority.

### Presentation architecture

Workforce Core (Employee / WorkItem / Run / Governance / Approval / Audit / Metrics) feeds a Presentation Layer (Executive Office / Virtual Office / Avatar / Clothing / Meetings / Analytics). The Presentation Layer is never an alternative execution or authorization path.

### Customer HQ progression

The visual progression may evolve from Office → Department Clusters → Floors → Campus. The tier must be computed from authoritative customer metrics and entitlements, not arbitrary frontend counters.

### Monetization model

1. Recurring SaaS: employees, projects, usage, skills and enterprise capabilities.
2. Marketplace revenue: third-party employees, skills, workflows, themes and cosmetics, with platform commission where applicable.
3. Premium experience: office customization, branded HQ, avatars, voice/visual presentation and white-label capabilities.

The primary business KPI remains First Revenue Generated by AI Workforce. Cosmetic and marketplace revenue is additive.

### CEO experience

The Executive Office should expose real business state as a living company: morning brief, approvals/documents on the CEO desk, employees visibly working or waiting, project/department navigation, meeting transitions and company growth milestones. These are visualizations over real data, not simulated business activity.

### Anti-pay-to-win boundary

Commercial cosmetics and presentation upgrades must not increase permissions, bypass approval, change tenant isolation, unlock unauthorized privileged operations, or fabricate employee performance/revenue.

### Evidence rule

All W12–W21 phases remain PLANNED until their contracts, implementation, tests and relevant real-stack evidence exist. No marketplace, cosmetic purchase, visual provider or revenue claim may be described as live without evidence.

### W12 implementation checkpoint — 2026-10-03

**Status: FIRST FOUNDATION SLICE IMPLEMENTED; EXACT-SHA CERTIFICATION NOT RUN.

W12.2 checkpoint: current employee work visibility implemented from authoritative `Run.work_item_id` → tenant-scoped `WorkItem`; synthetic task/project/progress/meeting state remains intentionally unimplemented. Exact-SHA certification remains NOT RUN / NOT VERIFIED.**

Implemented on post-v1.4.11 mainline:
- tenant-scoped read-only office-state API;
- presentation state derived from real Employee/Run/WorkflowApproval data;
- initial customer Virtual Office UI with CEO desk and employee floor;
- avatar presentation from stable Employee avatar metadata;
- navigation/dashboard entry point.

The current slice intentionally does not invent department clusters, office tiers, meetings, voice or video states. Those require real underlying contracts in later phases.


W12.3 checkpoint: Virtual Office CEO Desk now surfaces real tenant-scoped pending WorkflowApproval records and links them to the existing approvals workspace. The presentation layer does not mutate approval state. Exact-SHA certification remains **NOT RUN / NOT VERIFIED**.


## W13 implementation checkpoint — 2026-10-03

W13 Customer HQ Progression is implemented on post-v1.4.12 mainline.

- Added authoritative HQ tier derivation from tenant subscription entitlement.
- Added tenant-scoped plan/capacity/usage metrics to the existing read-only Virtual Office contract.
- Added presentation of tier and capacity in `/office`.
- Added backend coverage for tier mapping and authoritative metric preservation.
- No project/department/room state is fabricated without an authoritative source.
- HQ tier is presentation-only and cannot alter permissions, quotas, approvals, tenant isolation or execution authority.

**Evidence boundary:** W13 exact-SHA CI/product gates/Production Certification are **NOT RUN / NOT VERIFIED**. W13 must not inherit `v1.4.12` certification.

## W14 checkpoint — Employee Appearance & Customization — 2026-10-03

**Status:** IMPLEMENTED on post-v1.4.13 mainline; exact-SHA certification **NOT RUN / NOT VERIFIED**.

Implemented foundation:
- tenant-scoped `Employee.presentation_profile` storage;
- bounded presentation-only fields: gender presentation, outfit, hair style, accessory;
- authenticated tenant write endpoint with audit provenance;
- customer employee appearance controls;
- explicit boundary: presentation metadata never affects permissions, governance, approvals, quotas, execution or billing;
- unit/API-adjacent tests for bounded values, tenant seam and audit evidence.

Next: W15 Wardrobe / Cosmetic Marketplace. Any commerce capability must use authoritative product/order/payment state and must not grant employee runtime authority.


## W16 real-stack lifecycle checkpoint — 2026-10-04

W16 Skills Marketplace has moved beyond the initial foundation into hardened real-stack lifecycle evidence on post-v1.4.16 mainline.

### Implemented and hardened

- Versioned, tenant-scoped `SkillPackage` catalog and `EmployeeSkillInstallation` ledger.
- Skill metadata validation rejects execution-authority declarations such as allowed tools, permissions, approval policy, capability contracts and tool bindings.
- Concurrent installation uses the database unique constraint as the authoritative race boundary.
- Tenant consistency is enforced at the database boundary with tenant-scoped unique identity keys and composite foreign keys.
- Published skill package content is immutable after publication at the PostgreSQL boundary; lifecycle status remains mutable for governed suspension/retirement behavior.
- Install/revoke/list operations preserve tenant-scoped Employee and SkillPackage ownership.
- Audit provenance records installation as presentation-only and explicitly records unchanged permissions, allowed tools and execution authority.
- Audit ledger entry IDs are assigned before entry-hash computation, preserving ledger verification after persistence.

### Real-stack evidence

PR #846, `test: verify W16 skill lifecycle on real PostgreSQL`, was merged at **`d7550e0489ed43c5a3cda9e9151e199d05a07119`** after exact-head validation of **`73f6f15916926a80c872031cf200ef9e39ee47ce`**.

Observed exact-head gates:
- CI: PASS — Run `37193115014`
- CodeQL: PASS — Run `37193114955`
- Architecture Guard: PASS — Run `37193114850`
- Security/Privacy: PASS — Run `37193114998`
- Production Infrastructure Validation: PASS — Run `37193115005`
- HA Failure Recovery Validation: PASS — Run `37193114996`
- Production Observability: PASS — Run `37193114997`
- Production Rollback & Alerting: PASS — Run `37193115020`
- Runtime Isolation/RBAC Contract: PASS — Run `37193114911`
- Ephemeral DAST: PASS — Run `37193114933`

The real-stack lifecycle scenario verifies publication, installation, revocation, reactivation of the same installation, cross-tenant rejection, audit actions, audit metadata invariants, ledger verification and persisted audit-row count.

The certification run exposed and corrected an actual audit-hash persistence defect: the AuditLog UUID was generated during flush after hashing. The service now assigns the UUID before hashing, with a regression assertion covering the invariant.

### Evidence boundary

W16 lifecycle behavior is **VERIFIED on the real PostgreSQL CI stack** for the exact PR head above.

The following remain **NOT VERIFIED**:
- post-v1.4.16 exact-SHA Production Certification;
- verified purchase entitlement settlement;
- third-party skill publishing;
- external skill-provider execution;
- real customer marketplace revenue.

This evidence is post-release engineering evidence and does not inherit v1.4.16 certification.

### W16 commercial purchase entitlement checkpoint — 2026-10-04

The previously planned entitlement slice is now implemented, real-stack verified, and merged on mainline through PR #851.

Implementation:
- tenant/employee/skill-package scoped `SkillPurchaseEntitlement` ownership ledger;
- entitlement creation only from the existing provider-verified sales-payment settlement path;
- exact employee/product/package contract validation against the published package and active employee-skill Product;
- commercial skill installation requires an active verified entitlement;
- free skills remain unaffected;
- entitlement state is presentation-only and does not grant permissions, allowed tools, capability contracts, approval policy or tool bindings;
- provider event and tenant/employee/package uniqueness constraints preserve replay and ownership boundaries.

Real-stack evidence:
- PR #851 exact head `0afd8d021afc5b71fb53f84d7c187a33545ec4f7` passed the full applicable CI/security/real-stack gate set before merge;
- merge commit: `bbafa2c7b754cd69d421c6011bf42f5523fdeaa2`;
- W16 Skill API Real-Stack run `37196737015` / job associated with the exact head completed **PASS**;
- post-merge W10 dogfood run `37196994830` completed **PASS** on the merge SHA.

Evidence boundary:
- W16 commercial purchase entitlement and commercial-install fail-closed behavior: **VERIFIED**;
- third-party skill publishing: **NOT VERIFIED**;
- external skill-provider execution: **NOT VERIFIED**;
- real marketplace/customer revenue: **NOT VERIFIED**;
- production certification of the post-v1.4.16 merge SHA: **NOT RUN / NOT VERIFIED**.

The next W16 work should focus on independently evidenced marketplace/customer outcome behavior or other concrete business requirements, not reimplementing the entitlement gate.

### W16 third-party Skill Marketplace publication checkpoint — 2026-10-04

PR #853 introduced and real-stack verified the third-party SkillPackage publication/discovery boundary.

Evidence:
- exact PR head: `9a2a8fe00b0da1b8bf61a6036b435e5f3a56b4a7`;
- merged as `dbacb01c4111174493b8d520a2934a07561a9a08`;
- W16 Third-Party Skill Publishing Real-Stack: PASS — run `37198545817`;
- W16 Skill API Real-Stack Contract: PASS — run `37198545857`;
- CI: PASS — run `37198545866`;
- CodeQL: PASS — run `37198545818`;
- Architecture Guard: PASS — run `37198545942`;
- Security/Privacy: PASS — run `37198545795`;
- Runtime Isolation/RBAC: PASS — run `37198545767`;
- HA Failure Recovery: PASS — run `37198545794`;
- Production Infrastructure Validation: PASS — run `37198545861`;
- Ephemeral DAST: PASS — run `37198545868`;
- Production Rollback & Alerting: PASS — run `37198545797`;
- Production Observability: PASS — run `37198545870`.

The real-stack scenario verified owner publication, cross-tenant public discovery, metadata-only public lookup, private-publication hiding, wrong-tenant rejection, duplicate-publication rejection and publication immutability.

The migration revision initially exceeded the existing Alembic `version_num VARCHAR(32)` boundary. Real-stack execution exposed the failure; the revision was corrected to `w16_skill_mkt_publications`, after which the exact-head gate set passed. Alembic's documented version table uses a string `version_num` column, and the repository's concrete failure was the database rejecting the longer revision value.

**Evidence boundary:**
- third-party SkillPackage publication/discovery: **VERIFIED** on the real PostgreSQL stack;
- installation authority: remains governed separately by the existing Employee Skill entitlement/install boundary;
- external skill-provider execution: **NOT VERIFIED**;
- real marketplace/customer revenue: **NOT VERIFIED**;
- production certification of `dbacb01c4111174493b8d520a2934a07561a9a08`: **NOT RUN / NOT VERIFIED**.

This checkpoint does not change the immutable `v1.4.16` production-certified release.

### W16 governed SkillPackage provider execution checkpoint — 2026-10-04

PR #855 added a dedicated runtime path for installed SkillPackage execution through an explicit operator-configured provider.

Implementation boundary:
- `workforce_execute_installed_skill` is a registered Tool Registry capability;
- execution requires an active tenant Run context, `run.execute`, Employee allowed-tool guardrails and mandatory approval for the external side effect;
- execution requires an active tenant-scoped Employee Skill installation;
- commercial SkillPackages additionally require the independently verified purchase entitlement;
- provider name, endpoint, credentials and timeout are operator-owned configuration; runtime Skill input cannot select a provider or endpoint;
- the default provider remains fail-closed `none`;
- the deterministic HTTP provider used by CI is test infrastructure only;
- provider payload carries tenant, employee, package, Skill version and stable request correlation identity;
- execution audit records provider, external execution state and unchanged execution authority;
- redirects and oversized provider responses are rejected;
- no generic shell or arbitrary command execution is introduced.

Exact-head evidence:
- PR head: `20727001c2f967d850bda036c53acf7ccd326f81`;
- merge SHA: `659c1e757c3cdc6dcc1d7c390a5bdd74bd3feff8`;
- W16 Skill Provider Execution Real-Stack: PASS — Run `37199713576`;
- CI: PASS — Run `37199713528`;
- CodeQL: PASS — Run `37199713526`;
- Provider Integration Contract: PASS — Run `37199713527`;
- Runtime Isolation/RBAC: PASS — Run `37199713590`;
- Production Infrastructure Validation: PASS — Run `37199713566`;
- HA Failure Recovery: PASS — Run `37199713653`;
- Ephemeral DAST: PASS — Run `37199713615`;
- Architecture Guard: PASS — Run `37199713621`;
- Production Secret Management: PASS — Run `37199713523`;
- Production Observability: PASS — Run `37199713593`;
- Production Rollback & Alerting: PASS — Run `37199713539`;
- Production Hardening: PASS — Run `37199713605`;
- Phase 14.14 Security/Privacy: PASS — Run `37199713604`;
- Workforce W0-W6 Contract Gate: PASS — Run `37199713600`;
- Workforce W1/W2/W3/W4/W5/W6/W7/W8/W9/W10 exact-head gates: PASS — Runs `37199713521`, `37199713613`, `37199713617`, `37199713531`, `37199713607`, `37199713575`, `37199713536`, `37199713519`, `37199713598`, `37199713599`.

The real-stack gate also exposed and corrected two implementation/wiring defects before the final PASS: provider settings were initially present only in the workflow runner rather than the API container, and the generic Workforce Tool Registry dispatch initially dropped the stable `tool_call_id`. The final exact head passed after both corrections.

**Evidence boundary:**
- governed SkillPackage provider execution against the deterministic CI HTTP provider fixture: **VERIFIED**;
- external production Skill provider execution: **NOT VERIFIED**;
- customer acceptance / marketplace revenue: **NOT VERIFIED**;
- production certification of `659c1e757c3cdc6dcc1d7c390a5bdd74bd3feff8`: **NOT RUN / NOT VERIFIED**.

The `v1.4.16` production-certified release remains immutable and is not extended by this checkpoint.


### W16 cross-tenant Skill Marketplace purchase checkpoint — 2026-10-04

PR #857 closes the buyer/seller separation needed for the next W16 commerce boundary.

Implemented:
- buyer-side `SkillMarketplacePurchase` ledger with buyer/seller tenants, publication, Employee, package, Product and idempotency correlation;
- buyer Employee remains tenant-owned while the SkillPackage/Product remain seller-owned;
- EmployeeSkillInstallation and SkillPurchaseEntitlement now retain the source owner tenant;
- public publication is required for cross-tenant purchase;
- purchase creates a buyer-tenant BusinessDeal and uses the existing provider-neutral sales payment checkout boundary;
- verified payment settles the purchase, creates/reconciles buyer entitlement, installs the seller-owned package for the buyer Employee, and records correlated WorkforceRevenueEvent metadata;
- repeated verified provider events remain idempotent;
- purchase/install/execution paths do not create permissions, allowed tools, capability contracts, approval authority or seller payout authority.

Exact-head evidence:
- PR #857 exact head: `272ce9f52b73fcd72354d2f41efe1278a921e7a8`;
- merge SHA: `8487f0b1133e20c4ce142d43fffd3ee69bf010c1`;
- W16 Cross-Tenant Skill Purchase Real-Stack: PASS — Run `37201453142`;
- CI: PASS — Run `37201453176`;
- CodeQL: PASS — Run `37201453185`;
- W16 Skill API: PASS — Run `37201453134`;
- W16 Skill Provider: PASS — Run `37201453112`;
- W16 Third-Party Publishing: PASS — Run `37201453159`;
- Runtime Isolation/RBAC: PASS — Run `37201453102`;
- Production Infrastructure: PASS — Run `37201453113`;
- HA Recovery: PASS — Run `37201453146`;
- Ephemeral DAST: PASS — Run `37201453141`;
- Architecture Guard: PASS — Run `37201453158`;
- Security/Privacy: PASS — Run `37201453101`;
- Production Observability: PASS — Run `37201453103`;
- Production Rollback & Alerting: PASS — Run `37201453138`;
- Provider Integration: PASS — Run `37201453190`.

The first exact-head attempt exposed ORM/migration index-name drift. After the migration/model names were reconciled, the final exact head passed migration consistency and the full backend CI suite.

Evidence boundary:
- cross-tenant marketplace purchase/settlement mechanics: **VERIFIED** on the deterministic contract-test payment provider and real PostgreSQL CI stack;
- real external customer purchase: **NOT VERIFIED**;
- realized customer marketplace revenue: **NOT VERIFIED**;
- marketplace financial allocation accounting (gross/platform fee/seller net): **VERIFIED**; external seller payout execution and tax settlement remain **NOT VERIFIED**;
- Production Certification for `8487f0b1133e20c4ce142d43fffd3ee69bf010c1`: **NOT RUN / NOT VERIFIED**.

Next W16 work should not add financial distribution semantics implicitly. Any seller payout, platform commission, refunds, chargebacks or tax treatment requires separate contracts and evidence.

### W16 marketplace financial allocation checkpoint — 2026-10-04

PR #860 added an explicit settlement-allocation ledger after verified cross-tenant marketplace payment.

Implementation boundary:
- settlement record is created only after the verified payment path has produced the WorkforceRevenueEvent;
- gross amount is taken from the settled marketplace purchase;
- platform commission is an explicit operator-configured basis-point policy;
- seller net is calculated as gross minus platform fee using deterministic currency-precision rounding;
- database constraints enforce fee bounds and balanced gross/fee/net amounts;
- provider event and purchase uniqueness preserve replay idempotency;
- payout execution is explicitly `not_executed`;
- tax treatment is explicitly `not_calculated`;
- no payout provider, tax engine, refund, chargeback or distribution authority is introduced.

Exact-head evidence:
- PR #860 exact head: `26e34cca56522d13880bc1599523e01767640425`;
- merge SHA: `e4084462e414cd408b7035997bbd2b469b77c14a`;
- W16 Cross-Tenant Skill Purchase Real-Stack: PASS — Run `37202824376`;
- CI: PASS — Run `37202824398`;
- CodeQL: PASS — Run `37202824329`;
- Ephemeral DAST: PASS — Run `37202824343`;
- W16 Skill Provider Execution: PASS — Run `37202824380`;
- W16 Skill API: PASS — Run `37202824326`;
- W16 Third-Party Publication: PASS — Run `37202824356`;
- Runtime Isolation/RBAC: PASS — Run `37202824391`;
- Architecture Guard: PASS — Run `37202824355`;
- Production Infrastructure: PASS — Run `37202824370`;
- HA Failure Recovery: PASS — Run `37202824314`;
- Production Secret Management: PASS — Run `37202824344`;
- Production Observability: PASS — Run `37202824350`;
- Production Rollback & Alerting: PASS — Run `37202824366`;
- Production Hardening: PASS — Run `37202824330`;
- Security/Privacy: PASS — Run `37202824372`;
- Provider Integration Contract: PASS — Run `37202824365`.

The real-stack scenario verified the configured 15% CI allocation policy, persisted gross/platform-fee/seller-net split, buyer/seller correlation, payout status `not_executed`, tax treatment `not_calculated`, and one-row replay idempotency.

**Evidence boundary:**
- marketplace financial allocation accounting: **VERIFIED** on the deterministic payment provider / real PostgreSQL CI stack;
- external seller payout execution: **NOT VERIFIED**;
- tax calculation/settlement: **NOT VERIFIED**;
- external customer payment/revenue: **NOT VERIFIED**;
- Production Certification for `e4084462e414cd408b7035997bbd2b469b77c14a`: **NOT RUN / NOT VERIFIED**.

The immutable `v1.4.16` production-certified release remains unchanged.
