## Active engineering track — 2026-11-18: Multi-Vendor acceptance (#1350)

This checkpoint supersedes older dated priorities for the current continuation. Work is restricted to the Multi-Vendor tenant ownership, delegated authorization and portal acceptance track. Do not start unrelated product, World Mode, external production or release work.

Current evidence:
- PR #1434 is OPEN/unmerged at exact head fed62f56a75dd0f6de09c41e14a00506593d14c5, matching the active local branch.
- 20 GitHub Actions suites and one GitHub Advanced Security suite succeeded on that head. Freebuff Web suite 117539141336 is queued; combined commit status is pending. No merge.
- PR #1433 (master handoff) is OPEN/unmerged. PR #1447 is Draft and stacked on #1434. Issue #1350 remains OPEN.
- The local worktree has 80 uncommitted paths (61 tracked, 19 untracked). They are outside the committed test-only scope of PR #1434 and must be preserved and classified before further implementation.

Single ordered path:
1. Complete remaining Actor x Resource x Action route/action/topology cases, one documented gap per step.
2. Local ephemeral PostgreSQL evidence now passes for Outbox entitlement/provider fencing (8), Test Center suspended delayed execution (5), delegated Portal/reporting and sibling invoice export denial (21), and Lifecycle races/API (5); obtain exact-head GitHub CI evidence next.
3. Delegated `/usage/optimization` and `/usage/cost-forecast` are now accepted in the live Portal scenario; only exact-head CI evidence remains for this slice.
4. Verify delegated audit attribution for failed access, grant revocation and background workers.
5. Keep legacy migration rehearsal and human visual acceptance behind their separate approval gates; realtime transport is a separate follow-on, not an Issue #1350 blocker.
6. Treat backend cache isolation as not applicable unless a server response/data cache is introduced; preserve future tenant/context cache requirements.
7. Keep persistent database changes, commit/push/merge, deploy and release promotion behind separate explicit authorization.

Explicit decision gates:
- WebSocket/SSE is not implemented. Treat it as an architecture decision only; do not implement a transport without a separate approved decision.
- Desktop/mobile visual acceptance requires separate explicit approval.
- No persistent DB migration/backfill, Staging/Production mutation, commit, push, merge, deploy or release promotion without separate explicit authorization.

Detailed checkpoint: docs/current/AI_EMPLOYEE_MASTER_HANDOFF_2026-11-18.md.
Source-backed gap register: docs/current/MULTI_VENDOR_ACCEPTANCE_MATRIX_AUDIT_2026-11-08.md.

---
## Verified checkpoint — 2026-10-30 (PRs #1310 and #1311 merged)

Application baseline: `main` at `3d3f7f72c4c5e56a4d7e3f1c73cd282c41aea10f` after the two merges below. This documentation checkpoint does not change application behavior.

- PR [#1310](https://github.com/ijoolaie/AI-Employee/pull/1310) merged as `f262a1df58ba4d8c24fccc7e4573ee04c3efe4fb`. All 15/15 exact-head checks passed before merge; all 11/11 post-merge checks on the merge SHA have now completed successfully. Missing-slot preflight skips RAG retrieval, memory retrieval/embedding and automatic memory extraction; the regression test instruments the actual provider/embedding boundaries.
- PR [#1311](https://github.com/ijoolaie/AI-Employee/pull/1311) merged as `3d3f7f72c4c5e56a4d7e3f1c73cd282c41aea10f`. It was synchronized with the #1310 merge, all 4/4 exact-head checks passed, and all 5/5 post-merge checks have now completed successfully.
- Open PR inventory: only [#1257](https://github.com/ijoolaie/AI-Employee/pull/1257), intentionally Draft/on hold for human visual acceptance. Do not merge based on CI or synthetic screenshots.
- [Issue #1258](https://github.com/ijoolaie/AI-Employee/issues/1258) remains the active engineering/product acceptance tracker. Implemented slot provenance and conservative preflight are partial increments, not proof of trusted order/payment/stock/policy outcomes, durable staff delivery, browser-to-real-API acceptance, complete tenant/privacy acceptance, or live customer acceptance.
- [Issue #1288](https://github.com/ijoolaie/AI-Employee/issues/1288) remains blocked on authorized non-production SMTP delivery evidence, a named human owner and an agreed measurable SLA. Mocked SMTP/outbox tests do not prove delivery.
- [Issue #1305](https://github.com/ijoolaie/AI-Employee/issues/1305) remains blocked on explicit owner approval of retention duration, audit requirements and purge schedule. Logical expiry is not physical erasure; do not enable purge before approval.
- [Issue #1061](https://github.com/ijoolaie/AI-Employee/issues/1061) remains blocked on real prospective-customer discovery (target: five decision-maker conversations and two concrete sample/trial commitments). No customer demand or revenue is claimed.
- [Issue #1044](https://github.com/ijoolaie/AI-Employee/issues/1044) and Draft PR #1257 remain deferred pending actual-runtime desktop/mobile evidence and explicit human visual approval. [Issue #1250](https://github.com/ijoolaie/AI-Employee/issues/1250) remains upstream advisory watch; no guessed dependency override or suppression.
- External gates #19, #210, #259 and #269 remain open for target-production RBAC, exact-SHA release promotion, production operations/security/DR and customer acceptance evidence. No repository CI result closes these gates.
- Latest production-certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. The newer mainline commits are not covered by that certification. No deployment or new release certification is claimed.

The older dated checkpoints below are retained as historical records; this verified checkpoint supersedes their pending/running descriptions of PRs #1310 and #1311.

---

## Follow-up checkpoint — provider-boundary fix PR #1310 (2026-10-30)

- Documentation reconciliation PR #1308 merged as `315e3ea71a136bca3ce64772bf28d8a03687f744`; its post-merge CodeQL runs were still running at last inspection.
- PR #1309 was closed as superseded after backend CI showed its new test patched the memory-extraction facade wrapper, which correctly receives disabled settings during preflight. This was a test-design false positive, not proof of a provider call.
- Replacement [PR #1310](https://github.com/ijoolaie/AI-Employee/pull/1310) is based on latest main and corrects the regression test to instrument the actual memory AI gateway and embedding function. It also retains assertions that RAG and memory retrieval do not run during preflight.
- Exact-head `36e0f1abcc3dcac974b2648485a5148732598a09` CI was queued/running at this checkpoint; do not merge before all required checks pass.
- Issue #1258 remains open for the broader trusted-evidence, handoff, real API, tenant/privacy and live-customer acceptance matrix.

---

## Roadmap checkpoint — customer-support Run-path preflight merged (2026-10-30)

The project remains in **Post-release Reconciliation → External Production & Customer Acceptance**; this increment does not change release certification or authorize deployment.

- PR #1307 merged to main as `31e869542d12aa141745667b8d44b9c1d9650c93` from exact tested head `f202aa0208f112ed7b8c773f2530fd276a64ae2d`; 15/15 exact-head checks passed.
- The customer-support Run path now performs conservative intent-based missing-slot preflight for ETA, variant stock, bulk discount, returns/exchanges, payment issues and damaged orders, plus existing shipping-fee preflight. Missing context is requested before the primary response-generation gateway call; ambiguity is not guessed. Optional provider-backed retrieval and automatic memory extraction are tracked in [PR #1310](https://github.com/ijoolaie/AI-Employee/pull/1310); PR #1309 is closed as superseded, and #1310 remains subject to exact-head CI.
- Next acceptance remains Issue #1258: trusted policy/evidence outcomes, durable handoff/outbound approval, browser-to-real-API and complete tenant/privacy plus live customer acceptance.
- Issue #1305 remains gated on owner approval of retention duration, audit requirements and purge schedule; logical expiry is not physical erasure.
- Issue #1288 still requires authorized non-production SMTP delivery, named human ownership and measurable SLA. Issue #1061 remains the customer-discovery gate. World redesign #1044 / Draft PR #1257 remains deferred.
- All **11/11 post-merge checks** on merge SHA `31e869542d12aa141745667b8d44b9c1d9650c93` completed successfully; zero failures or pending checks.
- Latest certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. No deployment or new release certification.

---

## Roadmap checkpoint — customer conversation slots merged (2026-10-30)

The project remains in **Post-release Reconciliation → External Production & Customer Acceptance**; this engineering increment does not change release certification or authorize deployment.

- PR #1303 merged to main as `1cb51001d3a8922b1e48c9d87b376a1cb4aa7831` from exact tested head `c38c6dda9ab835995a5e457f9079cc49dabd9e7f`; 23/23 exact-head checks passed.
- Structured tenant-scoped customer slots now have exact customer-source-message provenance, allowlisted conservative extraction, per-slot logical expiry, fail-closed source-content validation and validated prior-city reuse.
- **Next engineering acceptance:** continue Issue #1258 for ETA, variants, bulk discount, returns/payment, durable handoff/outbound approval, browser-to-real-API and complete privacy/tenant scenarios.
- **Retention follow-up:** Issue #1305 remains gated on owner approval of retention duration, audit requirements and schedule. No production purge is enabled; expiry is not physical erasure.
- **Operational handoff:** Issue #1288 still requires authorized non-production SMTP delivery, named human ownership and a measurable SLA.
- **Customer evidence:** Issue #1061 remains a separate discovery gate (five decision-maker conversations and two concrete sample/trial commitments).
- **World redesign:** #1044 / Draft PR #1257 remain deferred pending explicit human visual acceptance.
- All **17/17 post-merge checks** on merge SHA `1cb51001d3a8922b1e48c9d87b376a1cb4` completed successfully; zero failed or pending.
- Latest certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. No deployment or new release certification.

---

# AI Employee Platform — Productization & Delivery Roadmap

## Roadmap truth — 2026-10-13

**Documentation reconciliation:** Current-state summaries must follow the release ledger and exact GitHub evidence. The manifest, gap register and evidence index were found to contain stale release/current-state summaries; root-cause assessment and preventive actions are tracked in [Capability Reality Audit & Commercial Readiness Plan](CAPABILITY_REALITY_AUDIT_AND_COMMERCIAL_READINESS_PLAN_2026-10-13.md). The latest release certification is not proof of external deployment or revenue.

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

## Step completion — 2026-11-18

Notification recipient lookup is evidenced with one focused test (1 passed, 2 deselected; no database). The broader Notifications/Outbox row remains partial. Continue next with the existing entitlement expiry/suspension evidence and only the remaining in-flight/background boundary; do not repeat expired-grant or paused-subscription tests already present.

## Entitlement slice result — 2026-11-18

Outbound Email/WhatsApp workers use the existing commercial execution-entitlement guard before provider I/O; deterministic denial follows the dead-letter path. Eight focused PostgreSQL tests now pass on a disposable local database, including no-entitlement denial for both providers and Subscription revocation serialization across the provider transaction. Next ordered slice is a bounded inventory of remaining Celery/async workers for tenant provenance and execution-time authorization.

## Worker inventory slice result — 2026-11-18

Test Center delayed execution revalidates current tenant/commercial entitlement using the durable TestRun tenant before starting. The suspended-tenant PostgreSQL integration case now passes with valid paid entitlement fixtures; all five Test Center integration tests pass locally on the disposable PostgreSQL database. The remaining reviewed schedule/event/Run/Workflow/outbox tasks use explicit or durable-row-derived tenant identity with existing guards. Next ordered domain: server-side cache isolation, followed by remaining report/export topology gaps.

## Cache isolation decision — 2026-11-18

- Targeted backend scan found no tenant-scoped server response/data cache or cache decorator. Redis is used for IP rate limiting, tenant resource leases and fair scheduling, not response caching. Frontend QueryClient identity clearing is already evidenced by #1413–#1415.
- Do not build a cache subsystem or add cache tests. Mark backend cache isolation not applicable for this source baseline; retain a guard for any future server cache to include effective tenant/context and revoke/switch invalidation.
- Next: reports, privacy exports and generated artifact ownership gaps.

## Latest report/export evidence — 2026-11-18

- Added one Reseller→Customer negative assertion: sibling Customer invoice PDF export must return 404. Ruff and diff check passed; PostgreSQL scenario not run locally.
- Existing portal live-API evidence already covers owned invoice PDF export/download and revoked-grant denial; the new assertion closes only the sibling export action gap.
- CI execution remains pending.

## Knowledge search/indexing source reconciliation - 2026-11-18

Existing portal live-API acceptance covers direct Customer and Vendor-to-Reseller contexts: tenant-owned indexing, sibling file rejection, search results excluding sibling/foreign tenant markers, and 403 after grant revocation. RAG search filters KnowledgeChunk, KnowledgeDocument and active FileObject by effective tenant. API supports bounded top_k (1..20), not page pagination or arbitrary filters; no result cache exists. Do not invent tests for nonexistent features. Search/index isolation is covered for the exercised contexts; the full Actor x Resource x Action matrix remains partial pending remaining hierarchy permutations and authorized CI evidence.

## Worktree status refresh - 2026-11-18

Current worktree is 80 changed paths (61 tracked, 19 untracked), with no staged changes. Four additional tracked paths were changed in the entitlement and report/export slices since the 76-path checkpoint. Preserve all existing edits. Branch remains test/knowledge-revoked-portal-context-20261108 at fed62f56a75dd0f6de09c41e14a00506593d14c5. No commit/push/merge/deploy or database mutation; local changes are not part of PR #1434.

## Reseller Customer user lifecycle evidence - 2026-11-18

Added a live portal acceptance scenario for Reseller-owned Customer user management: invite/revoke in its direct Customer and deny invitation into a sibling Reseller's Customer. Ruff and diff check passed; PostgreSQL scenario not run locally. Isolated CI evidence is pending.

## Scope clarification - realtime is not an Issue #1350 blocker

Issue #1350's approved scope explicitly names APIs, search, reports, files, exports, background jobs and dashboards, but does not require WebSocket/SSE. Realtime remains a separate product/architecture follow-on and must not be implemented in this continuation. It does not block Issue #1350 acceptance unless the product owner formally extends the approved scope.
## Action-grant and child-tenant lifecycle live acceptance - 2026-11-20

- Executed the PostgreSQL 16 live API acceptance on a disposable container with an isolated network namespace and tmpfs database storage. The complete local Alembic graph, including `w34_assignment_commands` and `w35_assignment_recovery_claims`, migrated successfully.
- `test_reseller_action_grant_enables_direct_customer_provisioning_and_revocation`, `test_vendor_action_grant_enables_reseller_provisioning_and_revocation`, and `test_vendor_reseller_lifecycle_routes_enforce_direct_child_boundaries` passed: **3 passed**. The lifecycle case covers Vendor -> direct Reseller, Vendor -> direct Customer, and Reseller -> direct Customer, including invalid transitions, parent/child guards, sibling/wrong-kind denial, audit attribution and user deactivation.
- The first execution exposed a test-fixture mismatch, not an application defect: the two new grantor fixtures used a non-canonical role name (`Action Grant Admin`), while the established edition-admin dependency requires `Admin`. Updated only those test fixtures; rerun passed. No production code changed.
- The existing Vendor -> direct Customer action-grant baseline test was not part of this filtered run. No GitHub CI was triggered. Disposable PostgreSQL container was removed; no persistent DB, Staging service, or existing container was modified.
- Remaining gates: exact-head CI evidence; unresolved product decision on Vendor parent administration of child-tenant users; audit failure-event transaction/privacy policy; legacy migration rehearsal and human UX acceptance. Issue #1350 remains OPEN.
## Vendor direct-Customer action-grant baseline execution - 2026-11-20

- Executed the previously omitted baseline `test_user_action_grant_enables_scoped_provisioning_and_revocation` independently against a fresh disposable PostgreSQL 16 container (`support_test`, isolated network namespace, tmpfs data directory).
- The full Alembic graph migrated from the initial schema through `w35_assignment_recovery_claims`; the focused test passed: **1 passed, 2 deselected**.
- Combined with the three passing live acceptance cases recorded above, Vendor -> direct Customer, Vendor -> direct Reseller, Reseller -> direct Customer grant/revoke, and the Vendor/Reseller child lifecycle matrix now all have local PostgreSQL execution evidence.
- No Production source changed. The test container was uniquely named, stopped, and auto-removed. Staging services and the persistent databases were not targeted. GitHub CI remains untriggered; Issue #1350 remains OPEN.

## Legacy Vendor permission-backfill rehearsal evidence - 2026-11-20

- Executed the existing PostgreSQL TEMP-table rehearsal `backend/tests/test_vendor_permission_backfill_postgres.py` on disposable PostgreSQL 16: **1 passed**.
- The fixture exercises two root Vendors, a shared role assigned to both a platform administrator and an ordinary user, Vendor child Reseller/Customer roles, Vendor Admin/Owner role-name variants, preservation of an existing permission description, idempotent repeated upgrade, and non-revoking downgrade behavior. The test rolls back its transaction; no persistent schema or data is changed.
- This is synthetic representative-fixture evidence, not a rehearsal against a sanitized historical production snapshot. The acceptance matrix's real legacy-snapshot review remains OPEN; no Staging/Production migration or backfill was run.
- Disposable PostgreSQL container was uniquely named, isolated, tmpfs-backed, stopped, and auto-removed. No Production source changed. Issue #1350 remains OPEN.

## Exact-head GitHub CI and remaining action-scope contracts - 2026-11-20

- Re-read GitHub PR #1434 and the complete Check Runs collection for exact head `fed62f56a75dd0f6de09c41e14a00506593d14c5`: **23/23 check runs completed successfully**, including CI backend/frontend, CodeQL (Python and JavaScript/TypeScript), security/privacy, architecture, tenant hierarchy isolation/RBAC, real-stack E2E, DAST, infrastructure, observability, recovery and rollback. This supersedes earlier handoff notes describing a queued/pending check on this same SHA.
- PR #1434 remains OPEN and unmerged. PR #1447 remains OPEN, Draft, stacked on #1434. Issue #1350 remains OPEN.
- Important evidence boundary: these GitHub checks ran against the pushed `fed62f56` tree. They do **not** include the current uncommitted worktree changes (87 changed paths), including the focused test additions and current documentation updates. No new workflow was triggered.
- Ran DB-free acceptance contracts against the repository's dependency-complete Python 3.12 container with the backend mount read-only: `test_edition_api_key_scope_contract.py` and `test_vendor_permission_backfill_migration.py` — **17 passed**. Pytest emitted only a cache warning because the source mount was intentionally read-only; test results were successful and no repository artifacts were written by the runner.
- Legacy Vendor permission backfill PostgreSQL TEMP-table rehearsal remains **1 passed** on disposable PostgreSQL 16 (synthetic fixture; not a historical snapshot rehearsal). Action-grant/lifecycle PostgreSQL cases remain as recorded above.
- No commit, push, merge, deploy, persistent database mutation, or Issue #1350 state change. Continue to preserve all local edits.


## 2026-11-20 - Vendor descendant user administration decision
- Product decision received: Vendor has full user lifecycle and access-management authority throughout its own tenant subtree (direct Resellers, direct Customers, and Customers beneath its Resellers).
- Authority is ancestry-validated server-side on every request; no sibling-Vendor or external-tenant access. User identities/roles stay tenant-local; platform-admin/superuser and platform-only permissions are never delegable.
- Required actions include list, invite, invitation revoke, activate/deactivate, and tenant-local role assignment/management under delegation ceilings, with last-admin, entitlement, API-key scope and audit controls preserved.
- Existing Reseller -> direct Customer router is insufficient. Next implementation slice is a shared hierarchy-aware service plus Vendor/Reseller route surfaces and a PostgreSQL-backed Actor x Target hierarchy matrix. No application code changed in recording this decision.
- Open gates remain: audit failure-event transaction/privacy policy, historical migration snapshot, human portal UX acceptance, exact-head CI for local dirty changes. No commit/push/merge/deploy; Issue #1350 remains OPEN.

## Implementation reconnaissance - hierarchy boundary (2026-11-20)

Source inspection confirms `edition_service.assert_can_access` is intentionally limited to Vendor -> direct Reseller/Customer and Reseller -> direct Customer. `backend/tests/test_edition_boundaries.py::test_vendor_can_access_direct_resellers_and_direct_customers_only` explicitly rejects Vendor -> Reseller -> Customer. Do not broaden this shared cross-edition helper: it is used outside user administration and changing it would expand unrelated API access.

The user-management implementation must therefore use a dedicated, database-backed target resolver that validates the complete persisted ancestry for the user-management routes only. It must support Vendor -> direct Reseller, Vendor -> direct Customer, Vendor -> Reseller -> Customer, and Reseller -> direct Customer; reject sibling Vendor and foreign ancestry; and lock/revalidate the target tenant before writes. The existing `tenant_admin` role loader is also actor-tenant-bound and rejects `vendor.*` permissions, while the Reseller router has a fixed Customer-member role and only list/invite/revoke/status operations. These cannot simply be reused unchanged for Vendor target administration.

No authorization code was changed in this reconnaissance step. The next implementation slice is the dedicated hierarchy resolver plus its unit/PostgreSQL contract tests, followed by target-tenant-aware user lifecycle and role operations with explicit API-key route scopes.
### Vendor delegated user-management resolver — implementation checkpoint (2026-11-20)
- Added `backend/app/services/tenant_user_management_service.py` with a DB-backed resolver that loads actor, target, parent, and (for nested Customer targets) grandparent from persisted `tenants` rows. It rejects inactive tenants, non-root Vendor actors, malformed Reseller ancestry, non-Customer actors, self-targeting, sibling/foreign ancestry, and unsupported hierarchy edges.
- The resolver is intentionally separate from `edition_service.assert_can_access`; no global edition access policy was widened.
- Added `backend/tests/test_tenant_user_management_service.py`; focused pure-policy tests: **8 passed**. `git diff --check` passed.
- Not yet integrated into HTTP routes; no invitation/list/revoke/status/role API behavior changed. No PostgreSQL resolver integration test has run yet.
- An attempted combined run with `test_edition_boundaries.py` had 18 passes and one environment/import failure because the local interpreter is Python 3.10 and an existing module imports `enum.StrEnum` (Python 3.11+); this is not evidence of a product regression. The first attempt also exposed an incorrect test expectation (a Reseller is allowed to manage all its own direct Customers); the test was corrected to use a Customer under a different Reseller.

### Vendor descendant user read APIs — implementation checkpoint (2026-11-20)
- Added `backend/app/api/v1/vendor_tenant_users.py` with target-tenant-scoped GET endpoints for tenant-local users and assignable roles, using the DB-backed ancestry resolver. The route only exposes users whose `User.tenant_id` matches the resolved target; role listing is limited to target-tenant roles and system roles.
- Registered the router and added a dedicated API-key scope `edition.vendor.users.read` with explicit route-template mappings for both GET routes. The API-key scope contract remains fail-closed for unmapped routes.
- Authorization requires the Vendor administrator context plus the target-kind read permission (`vendor.reseller.read` or `vendor.customer.read`). The resolver enforces active target and persisted Vendor subtree ancestry.
- Validation: Python compileall succeeded for changed runtime modules; focused resolver + API-key scope tests: **23 passed**.
- Write operations (invite/revoke/status/role assignment) are not yet exposed for Vendor; no DB-backed live API test has run for these new endpoints. No PostgreSQL or persistent database was touched.

### Validation correction (2026-11-20)
- After adding the new Vendor users read scope to the Vendor API-key allowlist, the final focused run completed with **25 passed** across `test_tenant_user_management_service.py` and `test_edition_api_key_scope_contract.py`; compileall and `git diff --check` also succeeded.

## 2026-11-20 - Vendor delegated user lifecycle progress
Vendor descendant user invite/revoke/status routes are now implemented locally, with persisted hierarchy resolution, tenant locks, last-admin and entitlement checks, auth-token revocation, dual audit entries, and a dedicated API-key manage scope. Next: settle the role-assignment permission boundary from existing bootstrap/system-role contracts, implement role writes, then run focused PostgreSQL live API acceptance. Keep Issue #1350 open until evidence and exact-head CI are complete.

## 2026-11-20 - Vendor role administration progress
Vendor descendant role replacement is now implemented locally. It preserves non-target assignments, allows only target-local/system roles, applies the existing permission ceiling, blocks platform/Vendor control-plane escalation, protects the last active target admin, and writes dual-scope audit. Next validation is PostgreSQL live HTTP coverage for the complete Vendor user lifecycle, then remaining Issue #1350 acceptance evidence.

### Vendor user-management authorization revalidation - 2026-11-20
- Source review confirmed that Vendor descendant role replacement already exists in `vendor_tenant_users.py`; it is limited to target-local and NULL-tenant system roles, enforces the existing actor-permission ceiling, blocks `vendor.*`/`platform.*` and named Platform Admin/Superuser grants, preserves non-target assignments, and protects the last active target administrator.
- Found a concurrency gap in write authorization: target tenant was locked, but the Vendor actor's active status and role permissions were not reloaded under lock before mutation. Added `_refresh_vendor_actor` to reload the actor with role permissions and `populate_existing=True` under `FOR UPDATE` after acquiring the target lock; inactive/missing actors now fail closed before the write permission check.
- Validation after the change: `test_tenant_user_management_service.py` + `test_edition_api_key_scope_contract.py`: **34 passed**; `compileall` and `git diff --check` passed. Git emitted existing LF/CRLF warnings only.
- This is focused contract/unit validation, not PostgreSQL/live HTTP acceptance. No database migration, staging/production access, CI, commit, push, or deployment occurred. Existing local worktree changes were preserved.

### Vendor subtree PostgreSQL acceptance attempt and cleanup - 2026-11-20
- Created a dedicated PostgreSQL 16.15 test database on loopback port 15436, with database files on container tmpfs. The complete Alembic migration graph reached head successfully, including `w34_assignment_commands` and `w35_assignment_recovery_claims`.
- Added `backend/tests/test_vendor_tenant_users_live_postgres.py`, a strict disposable-database-only HTTP acceptance covering Vendor reads across direct/nested descendants, foreign-Vendor denial, invitation creation/revocation and hashed token persistence, accepted-invite activation, deactivation, target-local role assignment, last-admin protection, dual-tenant audit attribution, and ledger verification.
- HTTP execution under the default local Python 3.10 stopped at application import because `enum.StrEnum` requires Python 3.11+. Python 3.12 successfully ran the focused DB-free suites: **34 passed**; compileall and `git diff --check` passed. The attempted PostgreSQL HTTP pytest invocation was not completed, so this acceptance remains unverified; do not count it as a pass.
- The disposable PostgreSQL container was stopped and auto-removed; its tmpfs database vanished with it. No persistent Docker volume, staging container, staging/production database, or other container was changed. No generated test database files remain.
- GitHub publication was explicitly requested by the user. Before publishing, preserve branch/PR stacking and inspect the complete dirty worktree; do not merge or deploy. The local worktree contains pre-existing cross-cutting Agent/Outbox/AssignmentCommand changes as well as Vendor user-management work, so publication must not silently omit or discard any of these files.

### GitHub publication checkpoint - 2026-11-20
- Published the Vendor descendant user-management implementation, resolver, API-key route scopes, focused unit/contract tests, disposable-PostgreSQL HTTP acceptance test, and current acceptance/roadmap/handoff documentation in commit `d32833ec9ffe7886ab5ca9fb15d0ae8991dc6d2f` on `test/knowledge-revoked-portal-context-20261108`.
- GitHub PR #1434 remains OPEN; its head was verified as the published commit. PR #1447 remains OPEN and stacked on #1434. No PR was merged and Issue #1350 remains OPEN.
- Exact-head CI was triggered by the push. At the last check, all 23 checks were pending; rerun/refresh before treating CI as complete.
- Published scope was deliberately limited to the 13 Vendor/acceptance/documentation files. Other 81 dirty paths in this worktree belong to other in-progress Agent/Outbox/AssignmentCommand work and remain untouched locally rather than being bundled into this PR.
- PostgreSQL 16 migrations completed on the temporary tmpfs database; the Vendor HTTP acceptance test is committed but not yet verified as passed. The disposable container was removed. No persistent DB, staging service, deployment, or merge was performed.

### GitHub CI follow-up and corrective cleanup - 2026-11-20
- Exact-head CI for documentation publication commit `a43fe9e0925031ee528d61ff895d2482f4c09999` identified three actionable issues: UTF-8 BOM in the new ancestry resolver (production-completeness parser failure), nine redundant f-string prefixes in the API-key contract test (Ruff failure), and `opentelemetry-api==1.45.1` flagged by pip-audit as CVE-2026-126360 (fixed in 1.45.2).
- Corrected the resolver to UTF-8 without BOM; removed the nine redundant f-string prefixes; raised the declared minimum and direct lock pin for `opentelemetry-api` to 1.45.2. No other OpenTelemetry package versions were changed.
- Local revalidation: production completeness baseline **PASS**; focused Vendor resolver/API-key contract suite **34 passed**; targeted Ruff **all checks passed**; Python 3.12 compileall and `git diff --check` passed.
- These fixes are queued for a follow-up commit/push and a fresh exact-head CI run. The previous CI failures are not considered resolved until the new commit's GitHub checks complete successfully.

### OpenTelemetry patch alignment correction - 2026-11-20
- The first dependency-only API bump exposed an exact-version constraint: `opentelemetry-sdk==1.45.1` requires `opentelemetry-api==1.45.1`. The partial lock update therefore failed dependency installation in CI before the audit stage.
- Aligned the three version-coupled direct distributions (`opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http`) to **1.45.2** in both `requirements.txt` minimums and `requirements.lock`. Instrumentation package versions remain unchanged.
- Revalidation after alignment: full backend Ruff (`app` + `tests`) passed; focused Vendor resolver/API-key tests **34 passed**; production completeness baseline passed; `git diff --check` passed. Fresh exact-head CI is still required to verify dependency resolution and pip-audit.

### OpenTelemetry instrumentation alignment correction - 2026-11-20
- CI dependency resolution confirmed that OpenTelemetry SDK 1.45.2 requires semantic-conventions 0.66b2, while the pinned FastAPI/SQLAlchemy instrumentation 0.66b1 requires semantic-conventions 0.66b1. The mixed set cannot be installed together.
- Aligned both direct instrumentation packages to **0.66b2** in `requirements.txt` and `requirements.lock`, matching SDK 1.45.2. This follows the exact resolver error; no broad dependency refresh was performed.
- Local static/test checks remain clean. A fresh CI run is required to verify the full lock install and security audit after this final alignment.

### PostgreSQL acceptance test CI isolation correction - 2026-11-20
- The full backend CI run completed **2,033 passed, 1 deselected**, with one failure: the new Vendor PostgreSQL acceptance test raised when its dedicated `LIFECYCLE_TEST_DATABASE_URL` was absent. The test is intentionally local/disposable-database-only and CI does not provision its reserved loopback:15436 database.
- Changed the test's missing-environment behavior to `pytest.skip`; a supplied but non-matching database URL still fails closed. This keeps the live acceptance explicitly gated to the dedicated ephemeral database without failing generic CI or allowing accidental use of staging/shared DBs.
- No live PostgreSQL acceptance is claimed from this correction. Re-run full CI on the new exact head; local Ruff and focused suite are to be revalidated before publication.

### Vendor user administration exact-head CI acceptance - 2026-11-20
- GitHub exact-head CI completed successfully for commit `f0cc11e067eda256c3f238a4da5e8a4dd44a62f4` on PR #1434: **35/35 reported checks passed** (no pending or failed checks at verification time), including Backend, Architecture, Security/Privacy, Tenant Isolation/RBAC, CodeQL, DAST, Recovery, and real-stack suites.
- Backend CI summary: **2,033 passed, 1 skipped, 1 deselected**. The single skip is `test_vendor_subtree_user_lifecycle_over_http`, intentionally requiring the dedicated `LIFECYCLE_TEST_DATABASE_URL` test database on loopback port 15436. The HTTP acceptance is not considered passed; local PostgreSQL migration rehearsal succeeded, but live Vendor API acceptance remains open.
- Local validation: full Ruff `backend/app` + `backend/tests` passed; focused resolver/API-key suite **34 passed**; OpenAPI lists all six Vendor user routes; production-completeness baseline passed.
- The temporary Vendor PostgreSQL 16 container was stopped and auto-removed; its tmpfs database was destroyed. Existing Staging PostgreSQL/Redis containers remain running. An unrelated container observed on port 15436 was not touched.
- Published branch head at this checkpoint: `f0cc11e067eda256c3f238a4da5e8a4dd44a62f4`. PR #1434 and stacked PR #1447 remain OPEN; Issue #1350 remains OPEN. No merge, deploy, or persistent database mutation.

### Vendor descendant administration live PostgreSQL and exact-head CI acceptance - 2026-11-20
- The committed `test_vendor_subtree_user_lifecycle_over_http` was executed against a fresh PostgreSQL 16.15 database on loopback port 15436. Database files used container tmpfs; the container ran on a dedicated test-only Docker network. Alembic reached head through `w35_assignment_recovery_claims`.
- Live HTTP acceptance: **1 passed in 5.54s**. Verified direct descendant list, nested descendant list, foreign Vendor denial (403), invitation create/revoke, hashed token persistence, user activate/deactivate, tenant-local role assignment, admin role removal, last-active-admin protection (409), target/Vendor audit attribution, and both tenant audit-ledger verifications.
- The PostgreSQL container and dedicated network were removed after the test. No named persistent volume was created. Staging PostgreSQL/Redis remained untouched.
- GitHub exact-head CI for `0b85595034fd86a85a540d4a83717fb000ccfe87` completed with **30 workflow runs, all successful** (including full backend, security/privacy, CodeQL, architecture, tenant hierarchy isolation/RBAC, DAST, infrastructure, recovery, and real-stack E2E). The branch and PR #1434 point at this exact SHA at the time of verification.
- PR #1434 remains open; PR #1447 remains open and stacked; Issue #1350 remains open. This is not final Issue acceptance: human portal UX, sanitized historical migration snapshot, and the separately unresolved audit-policy questions remain outstanding.

### Vendor role-boundary negative coverage extension - 2026-11-20
- Extended the disposable PostgreSQL HTTP acceptance to exercise `GET .../users/roles`, reject role IDs belonging to a different tenant (**400**), and reject the global `Platform Admin` system role (**403**) while retaining successful target-tenant role assignment.
- Re-ran the full migration-to-head + HTTP lifecycle acceptance on a fresh PostgreSQL 16.15 tmpfs database: **1 passed in 5.74s**. Observed and asserted the new 400/403 denials, alongside existing subtree, invitation, activation, last-admin and audit-ledger checks.
- The dedicated temporary container and network were removed after the run. This test extension is local pending publication and fresh exact-head CI.
