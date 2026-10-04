# Current Project Status

**Architecture baseline:** V1.5 Agentic Operating Model  
**Certified release baseline:** `v1.4.16`  
**Latest certified release:** `v1.4.16` — exact-SHA certification PASS  
**Certified release commit:** `434a0c4a4501af08a393faaf58092add764df2a2`  
**Mainline engineering head:** resolve directly from the repository; this document intentionally does not embed the mutable current `main` SHA  
**Status date:** 2026-10-04  
**Latest published release:** `v1.4.16`  
**Latest certified release:** `v1.4.16`  
**Certification run:** `37188879277` — PASS (exact `v1.4.16` SHA)  
**Production deployment:** OPEN — PENDING EXTERNAL EXECUTION

The architecture baseline, release identity and engineering phase are independent axes. V1.5 is not a release number. The certified `v1.4.16` release is immutable and points to the exact SHA certified by the Production Certification workflow. Historical releases remain immutable and are not rewritten. Mainline contains post-certification documentation changes and is not itself certified.

## Executive status

Phase 11 Unified Execution acceptance is **COMPLETE**. Phase 12 Test Center P12.1-P12.6 is **IMPLEMENTED / OPERATIONAL HARDENING**. Phase 13 Agent Teams & Marketplace engineering is **COMPLETE**. Phase 14 engineering is **COMPLETE WHERE TRACKED**.

The exact-SHA Production Certification suite passed for `v1.4.16`. Certification run `37188879277` / job `111396657270` checked out SHA `434a0c4a4501af08a393faaf58092add764df2a2`, recorded the required certification evidence, and completed successfully. This is repository/GitHub-hosted production-like certification evidence; it does not claim external production deployment.

## v1.4.16 certified and published release

- **Release status:** **PUBLISHED** — exact certified SHA `434a0c4a4501af08a393faaf58092add764df2a2`.
- Exact-SHA Production Certification: **PASS**, run `37188879277`, job `111396657270`.
- Evidence artifact: `production-certification-evidence-v1.4.16-434a0c4a4501af08a393faaf58092add764df2a2`.
- Evidence digest: `sha256:7af4640395aefcffe0485fc3b276dad0dc794a97333efe59d531ef8af74d3d70`.
- `v1.4.16` tag resolves to the certified SHA; post-certification engineering commits are not part of the certified snapshot.
- `production_deployment_claimed=false`.

## Historical releases

- `v1.4.10` remains immutable at certified SHA `b09f3e35d512e3c4d21be9d930539cbbe1d2d451`.
- `v1.4.9` remains immutable at certified SHA `f1ce20c010779f5273eb5d0051da24cdd57b33f6`.
- Historical release records are retained for traceability and are not rewritten as current status.

## Release and deployment status

| Item | Status | Evidence |
|---|---|---|
| `v1.4.16` tag | VERIFIED | Exact certified release tag resolves to `434a0c4...` |
| `v1.4.16` Production Certification | PASSED | Run `37188879277` / Job `111396657270` |
| Certified release SHA | VERIFIED | `434a0c4a4501af08a393faaf58092add764df2a2` |
| Production deployment claimed | FALSE | Certification evidence records `production_deployment_claimed=false` |
| External production deployment | OPEN — PENDING EXTERNAL EXECUTION | No external target is currently in use |
| Customer acceptance | OPEN — PENDING EXTERNAL EXECUTION | No external acceptance evidence |

## Evidence boundary

Repository tests, PR CI, CodeQL, local Docker, GitHub-hosted production-like validation, synthetic load/security evidence, simulated providers and local RBAC acceptance are supporting engineering/release evidence only. They do not substitute for live production deployment, live provider evidence, measured production SLO/DR, independent security/compliance review or customer acceptance.

Certification never transfers automatically across SHAs.

## Product completeness finding — 2026-09-21

The product-completeness work identified in the 2026-09-21 audit has since been closed for the audited scope and incorporated into the v1.4.11 certified release. The current posture is regression watch, not an open launch-blocking implementation gate.

- **Persian/RTL:** customer operational EN/FA browser acceptance and lang=fa / dir=rtl coverage are implemented.
- **Employee Templates:** seven tenant-safe bilingual starter templates are present with lifecycle/installation metadata.
- **Lists / tables / CRUD:** Product, Customer, Order/Invoice and Schedule lifecycle parity was reviewed with resource-specific non-destructive semantics where retention/auditability requires them.
- **Edition-aware Test Center:** Vendor/Reseller/Customer definition visibility and execution boundaries are edition-aware; shared controls remain covered at the shared boundary.
- **Analytics/reporting:** retry, empty-state and locale-aware formatting parity is covered.
- **Governance/localization:** the audited customer operational localization scope is complete.

Canonical historical record: docs/current/PRODUCT_COMPLETENESS_GATE_2026-09-21.md. The original findings remain historical evidence and are not rewritten.

## Post-v1.4.11 workforce governance engineering — 2026-09-23

After the v1.4.11 certified boundary, the following governed AI workforce engineering slices are now merged on mainline: durable CEO delegation (#641), runtime-bound Manager proposal provenance (#644), unrestricted Manager role selection plus four first-party role templates (#645), Manager workforce dashboard reporting (#646), and explicit workforce-role runtime enforcement (#647).

The runtime governance layer fails closed for missing/unknown workforce roles, rejects human-approval-required operations, and requires matching governed runtime identity plus active CEO delegation for Internal Manager operations. It does not provision or activate workforce roles and does not change the immutable v1.4.11 certification identity.

The next engineering frontier is to connect concrete role-specific capabilities/tools to explicit workforce-operation bindings without inferring authority from tool names, then add a tenant-owned SLA target contract before reporting SLA compliance. New role instances remain subject to AgentTemplate evaluation/publish, Board/CEO approval, access review and activation.


## Workforce Tool Registry audit — 2026-09-24

Post-v1.4.11 runtime hardening now includes PR #655, which moves Workforce role/operation validation ahead of Tool Registry resolution and adds regression coverage for that ordering. All required PR CI/security/runtime gates passed before merge; merge commit is `ab68798b73ada478bd2e7dffa9adca92bc77d4fc`.

The Tool Registry count and workforce operation count are now mutable mainline values after W0–W6; use `python scripts/workforce_binding_inventory.py` as the source-derived inventory rather than the historical fixed counts. The W0 code-derived inventory now covers the expanded nine-role catalog and all explicit semantic bindings; do not use the historical 14-binding count in this section. Run `python scripts/workforce_binding_inventory.py` from `backend/` for the authoritative current count. `ai_trader:market_research -> workforce_market_research`, `ai_trader:risk_analysis -> workforce_market_risk_analysis`, and `ai_trader:prepare_trading_plan -> workforce_market_trading_plan`. This binding is intentionally read-only, requires `run.execute`, has no autonomous trading side effect, and remains dependent on an operator-configured market-data provider. No existing generic tool is being approximated as another workforce capability. In particular, existing sales, product, calculator, document, order, and analysis tools are not silently reclassified as trading, campaign, creative, engineering, or executive-governance capabilities.

The `workforce_market_research`, `workforce_market_risk_analysis`, and `workforce_market_trading_plan` handlers are tenant-context-bound and fail closed when the provider is not configured, returns invalid data, or returns an error. Risk analysis is read-only and does not authorize order execution, capital allocation, leverage changes, or withdrawals. The provider endpoint is configuration-owned rather than caller-supplied, and production configuration requires HTTPS.

PR #658 is now merged on mainline at `5aef9a245d2e7a065b11b6eb0f60883842e06c3c`. PR #662 subsequently added the read-only `workforce_market_trading_plan` semantic capability and explicit `prepare_trading_plan` binding; its squash merge is `7434808483b10a8b6ae78ba92a7174f280e04a92`. The trading-plan provider contract is fail-closed, tenant-context-bound, and explicitly non-executing: it prepares a plan but does not place orders or allocate capital. The hardening work included explicit staging-secret placeholder validation, service-boundary validation for market-research inputs, provider-boundary tests, and a correction to the production secret-management validator so indented Compose declarations and line-local environment assignments are parsed correctly. All 16 required final check runs for the merge candidate completed successfully.

**Next implementation gate:** add further dedicated semantic workforce tools only where the operation can be implemented with a real, tenant-safe handler; then bind each operation explicitly and add runtime integration coverage for role authorization, capability freshness, tool binding, permissions, approval state, tenant identity, and execution provenance. Unsupported operations remain denied until such a binding exists.

## Workforce Tool Registry dispatch hardening — 2026-09-24

PR #664 is merged at `0671b31e9a4b8017e2aa418755cebc0bf5c900f3`. The three governed semantic market tools now execute through their registered `RegisteredTool.handler` implementations; duplicate name-based service dispatch was removed from `ToolRegistry.execute()`. Post-merge backend, frontend, architecture, infrastructure, validation, SLO, CodeQL and DAST checks all passed. This remains post-v1.4.11 engineering and does not alter the certified release identity.


## Internal Manager CEO report semantic binding — 2026-09-24
PR #667 is merged at `af29eb595d5b00b7257e678ab768e713aead3215`. Internal Manager `prepare_ceo_report` now has the first dedicated semantic Tool Registry binding: `workforce_prepare_ceo_report`. It delegates to the existing tenant-scoped workforce dashboard service, is read-only, requires `run.execute`, fails closed without tenant Run context, and remains subject to the existing explicit workforce-operation and CEO-delegation governance boundary. No staffing, provisioning, activation, financial authority, or release identity changed.

The governed semantic binding inventory is maintained against source code rather than this historical narrative. The 2026-09-30 audit found 14 explicit bindings in ai_workforce_roles.py, while only the subset with dedicated registered handlers and the required evidence should be treated as executable. Unsupported workforce operations remain denied until a dedicated semantic handler and explicit binding exists. See docs/blueprint/AI_WORKFORCE_IMPLEMENTATION_ROADMAP.md.

## Workforce handler dispatch regression coverage — 2026-09-24

PR #665 is merged at `7c9dd56a93fc3b4294467a55cd41b3daadf0bbbd`. Regression coverage now explicitly verifies governed market-research tenant-context enforcement and that a registered Workforce handler receives the runtime `db` and `tenant_id` context. The merge passed backend, frontend, architecture, infrastructure, recovery, CodeQL and DAST checks. This remains post-v1.4.11 engineering only.


## Current frontier

The current release frontier is `v1.4.16 RELEASE-CERTIFIED / LOCAL-ENGINEERING / EXTERNAL GATES OPEN`. Post-v1.4.11 semantic workforce engineering now includes an explicit code-reconciled binding inventory. The current source audit identifies 14 explicit Role → Operation → Tool bindings, while executable/evidenced status remains capability-specific. Unsupported workforce operations remain denied until a dedicated binding exists. No post-certification source changes are included in the certified snapshot. Continue regression watch for the audited product-completeness scope; do not reopen completed work without a regression, new requirement, or newly discovered unsupported surface.

W16 commercial skill purchase entitlement is now merged and real-stack verified on post-v1.4.16 mainline; it is not part of the immutable v1.4.16 release. The next application-code change requires a new candidate boundary and fresh exact-SHA certification. External production evidence remains intentionally open while the project is local.

## Semantic Workforce runtime evidence checkpoint — 2026-09-29

The post-v1.4.11 audit now distinguishes implementation from evidence:

- The canonical Agent Run path enforces Workforce role → operation → tool binding before `ToolRegistry.execute()`; this is implemented after PR #827.
- The generic real-stack Agent WorkItem E2E passes through the real Docker/Celery execution path and verifies Run/audit correlation.
- A semantic Workforce real-stack matrix is **not yet evidenced**.
- The repository does not currently contain a local market-data provider stub/server, and the deterministic E2E AI provider does not emit `tool_calls`.
- Therefore no semantic Workforce bypass or production defect is being claimed. The remaining item is an explicit E2E evidence/infrastructure slice.

### Code-reconciled workforce implementation roadmap

The repository-wide source audit on 2026-09-30 confirms that the workforce governance foundation is implemented, but the broader Internal AI Company workforce remains only partially executable. The canonical roadmap is now docs/blueprint/AI_WORKFORCE_IMPLEMENTATION_ROADMAP.md.

Implementation phases:
1. W0 — Evidence and contract reconciliation
2. W1 — Internal Company Control Plane
3. W2 — Engineering Employee
4. W3 — Content & Creative Workforce
5. W4 — Social / Instagram Employee
6. W5 — Sales & Lead Generation Workforce
7. W6 — Website Employee
8. W7 — SEO & Growth Employee
9. W8 — Customer Success / Support Employee
10. W9 — QA & DevOps Employees
11. W10 — Internal AI Company Dogfood / first revenue workflow

The highest-priority engineering gap is not additional role catalog breadth; it is dedicated, tenant-safe execution tooling for engineering, creative/media, social distribution and revenue workflows.

### Next engineering order

1. Add the minimum E2E-only deterministic tool-call/provider infrastructure without changing production defaults.
2. Execute the existing governed Workforce path through WorkItem → Run → Celery → ToolRegistry → semantic handler.
3. Verify persisted provenance/audit and negative controls for wrong role, approval-required operation, tenant isolation and stale capability contract.
4. Reconcile the evidence index.
5. Only if the resulting scope is release-worthy, cut a new release candidate and obtain fresh exact-SHA certification.

## Security rule

Do not commit production hosts, private keys, registry credentials, webhook secrets, payment secrets, customer data or environment-specific access tokens. Missing required production inputs must fail closed.

### Edition-aware Test Center gate
- Test Center acceptance is scoped by Vendor / Reseller / Customer capability ownership.
- Shared authentication, tenant isolation/RBAC, audit, policy, safe execution and evidence controls are tested at the shared boundary.
- Edition-specific tests cover only authorized service groups; full service duplication across editions is explicitly not required.
- Cross-edition negative authorization tests remain mandatory.

## Marketing growth semantic binding — 2026-09-24
PR #671 is merged at `2d19d870e7cef68fd9c6a4985690721a28176546`. The AI Marketing & Advertising Manager now has one dedicated read-only semantic binding: `ai_marketing_advertising_manager:prepare_growth_report -> workforce_prepare_growth_report`. The handler is tenant-scoped and uses existing tenant-owned orders and sales-deal data to produce an auditable commercial growth report. It does not claim campaign attribution or advertising-performance analysis, and it has no write, spend, launch, or external side effect. Campaign-specific operations remain unbound until a real campaign domain exists.

## Marketing campaign-plan semantic binding — 2026-09-24
PR #673 is merged at `30514627594ed022332f2b501aaa5ba86009133f`. The AI Marketing & Advertising Manager now has a second dedicated read-only semantic binding: `ai_marketing_advertising_manager:draft_campaign_plan -> workforce_draft_campaign_plan`. The handler produces a deterministic planning draft only; campaign launch, external spend, and measured campaign attribution remain separately governed and unbound from this planning capability.

## Marketing content-coordination semantic binding — 2026-09-24
PR #675 is merged at `8added213b49c84e11b2790e6afdb18aad35cf59`. The AI Marketing & Advertising Manager now has a third dedicated read-only semantic binding: `ai_marketing_advertising_manager:coordinate_content -> workforce_coordinate_content`. The handler produces a tenant-scoped, channel-aware content work package only; publication, external provider access, attribution, spend, and campaign launch remain outside this capability and require separate governed execution. The merge passed backend, frontend, architecture, infrastructure, recovery, rollback-contract, observability, security/privacy, tenant isolation/RBAC, CodeQL and DAST checks.

## Workforce semantic-domain audit — 2026-09-24

A repository-wide audit of the remaining Graphic Designer and Software Developer routine capabilities found no first-party tenant-safe semantic domain/handler that can currently back those workforce operations. The repository has no concrete Creative/Media/Asset domain for the Graphic Designer operations, and no dedicated engineering-workspace/change-set domain for the Software Developer operations. Existing generic sales, product, document, analysis, repository, or other tools are not reclassified to satisfy these contracts.

Accordingly, the following routine operations remain intentionally unbound and fail closed: Graphic Designer `create_visual_asset`, `revise_visual_asset`, `prepare_brand_variant`, `prepare_campaign_creative`; Software Developer `implement_routine_fix`, `write_tests`, `prepare_integration`, `refactor_non_critical_code`, `prepare_change_proposal`. This is a deliberate semantic-integrity boundary, not missing implementation work to be papered over with generic wrappers.

The next implementation gate is therefore domain-first: introduce a real tenant-safe domain/service only when the product model requires it, then add a dedicated handler, explicit role-operation binding, regression coverage, and governance/runtime integration checks. No release is created from this documentation reconciliation.

## W0–W6 implementation checkpoint — 2026-09-30

The post-v1.4.11 workforce implementation pass now contains a code-derived W0 binding inventory plus governed semantic foundations for W2–W6. The implementation is deliberately split from production/provider evidence.

- W0: code-derived binding inventory and focused reconciliation tests added.
- W1: existing Internal Manager control-plane tools remain governed; dedicated full-cycle CEO-to-report real-stack evidence is still open.
- W2: tenant-scoped Engineering Workspace artifact/change-set and delivery-proposal tools added; repository/deployment providers remain an explicit dependency.
- W3: Content Producer role/template and Graphic Designer semantic bindings added; creative provider execution remains unconfigured.
- W4: Social/Instagram semantic operations added with external-impact approval boundaries; live Instagram provider evidence remains open.
- W5: Sales/Lead Generation role/template and governed research/proposal operations added; autonomous external outreach remains approval-gated and provider-dependent.
- W6: Website Employee role/template and governed website delivery operations added; actual repository deployment remains dependent on W2 provider tooling.

These are mutable mainline engineering changes after certified v1.4.11. They must not be described as part of the immutable v1.4.11 production certification until a new RC is certified.


## W0–W6 contract gate verification — 2026-10-01

The dedicated Workforce W0–W6 Contract Gate is now **PASS** on mainline after correcting the W2 provider-state contract. GitHub Actions run `36831599565`, job `110269241283`, completed successfully: source compilation, code-derived W0 inventory, and all focused W0–W6 tests passed (`13 passed`).

The W2 semantic domain now reports both `provider_required/requires_provider=true` and `provider_execution=not_configured` consistently for provider-bound operations. This is an evidence/contract correction; it does not claim a live engineering provider.

## W1 control-plane E2E harness — 2026-10-01

A dedicated real-stack W1 certification harness was added at `backend/scripts/e2e_workforce_w1_control_plane_verify.py`. It exercises the intended control-plane chain against the live application stack: CEO-owned delegation → Internal Manager `assign_task` → specialist Agent WorkItem execution → persisted Run/audit verification → Internal Manager `prepare_ceo_report`.

The harness provisions its own tenant-scoped fixture, Manager and specialist Agent identities, and a bounded CEO delegation. It does not change the immutable `v1.4.11` release.

**Evidence status:** **VERIFIED**. GitHub Actions run `36830129984`, job `110264598687`, completed successfully. The run passed database migration checks, application health, the full W1 real-stack certification, and shutdown. The certification output recorded `W1 CEO DELEGATION PASS`, `W1 MANAGER ASSIGN_TASK PASS`, `W1 SPECIALIST RESULT PASS`, `W1 CEO REPORT VERIFICATION PASS`, and `WORKFORCE W1 CONTROL-PLANE REAL-STACK E2E PASS`. Specialist Run evidence: `cd46f769-0823-4141-b012-72c0f7e6b0f2`.

The W1 evidence path also required two mainline corrections discovered by real-stack execution: Manager lookup now uses the governed `workforce_role_code` rather than a fixed template slug, and the W1 stack now starts the transactional-outbox dispatcher/beat services required to deliver the persisted `agent.run.execute` handoff. These are post-v1.4.11 mainline changes and do not alter the immutable certified release.


## W2 Engineering semantic verification — 2026-10-01

W2 now has dedicated real-stack semantic evidence. GitHub Actions run `36832544726`, job `110272236014`, completed successfully after Alembic migration checks. The certification verified tenant-scoped workspace create/list/edit, cross-tenant read rejection, durable unique change-set artifacts, provider fail-closed behavior for test/lint/build, and approval-gated deployment proposals.

The W2 change-set implementation was corrected so each change set receives a unique durable artifact key instead of overwriting a shared `change-set.json`. This is semantic/provider-boundary evidence only: no live Git hosting, CI, deployment, or health provider is claimed.


## W2 engineering provider boundary — 2026-10-01

The W2 engineering domain now routes provider-bound operations through an explicit named provider interface at `backend/app/services/workforce_engineering_providers.py`. Production/default resolution is the fail-closed `none` provider; the deterministic `contract-test` adapter is available only for non-mutating contract verification. Unknown provider names fail closed. The semantic domain exposes provider identity and execution state instead of implying that Git, CI, deployment, or health operations executed.

**Evidence boundary:** provider-interface/contract behavior is implemented and covered by focused tests plus the W2 real-stack harness. A live Git hosting, CI, deployment, or health provider is still **NOT CONFIGURED / NOT VERIFIED** because no operator-controlled external credentials/endpoints are present. No generic shell execution was introduced.


## W2 provider-selection hardening — 2026-10-01

A provider-selection flaw found during continuation review has been corrected. Runtime Workforce semantic execution no longer accepts an `engineering_provider` value from tool execution context. Engineering provider selection is now operator-owned through `ENGINEERING_PROVIDER_NAME` / application settings, with the default remaining `none`. The deterministic `contract-test` provider remains available for controlled test/bootstrap use, but is not selectable by an agent through semantic tool arguments.

This closes the provider-selection control boundary; it does **not** create a live Git/CI/deployment provider. Live external engineering execution remains **NOT CONFIGURED / NOT VERIFIED**.
## W2 read-only GitHub provider — 2026-10-01

A first real provider adapter is now present, but remains fail-closed unless explicitly configured by the operator:

- provider: `github-readonly`;
- supported operation: `ci_status` only;
- tenant-to-repository mapping is operator-owned through application settings;
- GitHub token and timeout are operator-owned settings;
- repository URL, token, headers, and provider selection cannot be supplied by workforce tool input;
- the adapter never reports external execution; it returns read-only verification or an explicit configuration/provider error;
- branch, commit, PR, deployment, health, and rollback execution remain unavailable.

A follow-up review also corrected W2 semantic metadata so `git_branch` is explicitly classified as an external side effect and approval-gated.

This is post-v1.4.11 mainline work. No live GitHub provider has been certified yet.

## W2 provider and engineering-side-effect hardening — 2026-10-01

Continuation review found two additional control-boundary defects and corrected them:

- all provider-bound Engineering operations now resolve through the operator-owned ENGINEERING_PROVIDER_NAME setting; runtime engineering_provider context is ignored;
- the W2 E2E no longer expects the deterministic contract-test provider in the default real-stack environment and explicitly verifies that runtime provider override is rejected;
- git_branch is now treated as an external side effect and is approval-gated;
- workforce_git_branch and workforce_git_commit_proposal registry metadata now matches the authoritative role contract (external_side_effects=true, requires_approval=true);
- the W2 pull-request gate now triggers on provider/configuration/test changes as well as semantic-domain changes.

This remains post-v1.4.11 mainline engineering. Live GitHub/CI/deployment execution remains NOT CONFIGURED / NOT VERIFIED.



## W10 sales response ingestion & attribution verification — 2026-10-02

The W10 governed SMTP path now has end-to-end sales engagement measurement evidence on the real stack.

Final GitHub Actions run **36971624051** / job **110726669120** completed successfully at commit **3eff76c8a2217ceb91339bbaed692f193b3d59cb**.

Verified evidence:
- `W10 SMTP OUTREACH PROVIDER QUEUE PASS`;
- `W10 SALES DELIVERY EVENT INGESTION PASS` — the delivery event was observed after the dedicated email worker processed the transactional outbox; the certification script did not manually insert the delivery event;
- `W10 SALES DELIVERY + RESPONSE INGESTION PASS`;
- `W10 SALES RESPONSE IDEMPOTENCY PASS`;
- `W10 SALES ATTRIBUTION PASS sent=1 delivered=1 responded=1`;
- `W10 SMTP EXTERNAL DELIVERY PASS` against the isolated deterministic E2E SMTP sink;
- complete Docker shutdown PASS.

The delivery-event correlation includes the governed `tool_call_id`, `outbox_id`, and `deal_id`. Response replay resolves to the existing immutable event rather than creating a duplicate.

Status boundary: **W10 governed sales delivery/response ingestion, idempotency, and attribution mechanics are VERIFIED on the real stack for the isolated E2E SMTP provider path.** Real customer delivery, real customer response/conversation, and revenue remain **NOT VERIFIED**. The E2E sink is deterministic test infrastructure and is not evidence of real-world customer behavior or revenue.

This is post-v1.4.11 mainline engineering evidence and does not modify the immutable v1.4.11 certification boundary.


## W16 commercial skill purchase entitlement — 2026-10-04

PR #851, `feat: gate W16 commercial skills on verified purchase entitlement`, was validated at exact head `0afd8d021afc5b71fb53f84d7c187a33545ec4f7` and merged with merge commit `bbafa2c7b754cd69d421c6011bf42f5523fdeaa2`.

Exact-head validation before merge completed successfully across the W16 Skill API Real-Stack Contract, CI, CodeQL, Architecture Guard, Security/Privacy, Runtime Isolation/RBAC, HA Failure Recovery, Production Infrastructure, Ephemeral DAST, Provider Integration, Production Rollback & Alerting, and Production Observability gates.

The W16 real-stack evidence exercised same-tenant install/list/revoke, cross-tenant list/revoke rejection, commercial skill fail-closed without an active entitlement, verified payment creating the tenant-scoped entitlement, and commercial skill installation after the verified payment.

The purchase entitlement ledger is presentation-only ownership state. It does not add permissions, allowed tools, capability contracts, approval policy or tool bindings. Commercial skill installation remains fail-closed without a matching active verified entitlement.

Post-merge W10 Internal Company Dogfood E2E run `37196994830` completed successfully on merge SHA `bbafa2c7b754cd69d421c6011bf42f5523fdeaa2`. This is post-release engineering evidence; it does not create a new production certification for the merge SHA.

**Current boundary:** W16 commercial purchase entitlement, third-party SkillPackage publication/discovery, governed SkillPackage provider execution, cross-tenant marketplace purchase/settlement mechanics, marketplace financial allocation accounting, and read-only marketplace financial outcome reporting are **VERIFIED on the real PostgreSQL stack** for their exact validated mainline boundaries. External production skill-provider execution, external seller payout execution, and real customer marketplace revenue remain **NOT VERIFIED**. The immutable `v1.4.16` certification remains unchanged.

## W16 third-party Skill Marketplace publication — 2026-10-04

PR #853, `feat(w16): add third-party skill marketplace publishing`, was validated at exact head `9a2a8fe00b0da1b8bf61a6036b435e5f3a56b4a7` and merged with merge commit `dbacb01c4111174493b8d520a2934a07561a9a08`.

The exact-head gate set completed successfully:
- W16 Third-Party Skill Publishing Real-Stack — run `37198545817`;
- W16 Skill API Real-Stack Contract — run `37198545857`;
- CI — run `37198545866`;
- CodeQL — run `37198545818`;
- Architecture Guard — run `37198545942`;
- Security/Privacy — run `37198545795`;
- Runtime Isolation/RBAC — run `37198545767`;
- HA Failure Recovery — run `37198545794`;
- Production Infrastructure Validation — run `37198545861`;
- Ephemeral DAST — run `37198545868`;
- Production Rollback & Alerting — run `37198545797`;
- Production Observability — run `37198545870`.

The dedicated real-stack publishing scenario verified:
- owner tenant can publish an already-published SkillPackage;
- public publication is discoverable by another tenant;
- public lookup exposes publication metadata without manifest/compatibility payloads;
- private publication is hidden cross-tenant;
- wrong-tenant publication is rejected;
- duplicate publication is rejected;
- publication metadata is immutable.

The publication record is presentation/discovery metadata only. It does not create or modify permissions, allowed tools, capability contracts, approval policy, tool bindings, installation entitlement or execution authority.

**Current boundary:** third-party SkillPackage publication/discovery is **VERIFIED on the real PostgreSQL stack** for the exact PR head above. External skill-provider execution and real marketplace/customer revenue remain **NOT VERIFIED**. The `v1.4.16` Production Certification remains the immutable certified release; the merge SHA above is not production-certified.

## W16 governed SkillPackage provider execution — 2026-10-04

PR #855, `feat(w16): add governed SkillPackage provider execution`, was validated at exact head `20727001c2f967d850bda036c53acf7ccd326f81` and merged with merge commit `659c1e757c3cdc6dcc1d7c390a5bdd74bd3feff8`.

Exact-head validation completed successfully across the observed application/security gate set:
- W16 Skill Provider Execution Real-Stack — run `37199713576`;
- CI — run `37199713528`;
- CodeQL — run `37199713526`;
- Provider Integration Contract — run `37199713527`;
- Runtime Isolation/RBAC — run `37199713590`;
- Production Infrastructure Validation — run `37199713566`;
- HA Failure Recovery — run `37199713653`;
- Ephemeral DAST — run `37199713615`;
- Architecture Guard — run `37199713621`;
- Production Secret Management — run `37199713523`;
- Production Observability — run `37199713593`;
- Production Rollback & Alerting — run `37199713539`;
- Production Hardening — run `37199713605`;
- Phase 14.14 Security/Privacy — run `37199713604`;
- Workforce W0-W6 Contract Gate — run `37199713600`;
- Workforce W1/W2/W3/W4/W5/W6/W7/W8/W9/W10 real-stack gates — exact-head runs `37199713521`, `37199713613`, `37199713617`, `37199713531`, `37199713607`, `37199713575`, `37199713536`, `37199713519`, `37199713598`, `37199713599` respectively.

The dedicated W16 provider execution real-stack gate verified:
- a tenant-installed free SkillPackage reaches the operator-configured deterministic HTTP provider only after mandatory approval;
- the provider receives tenant, employee, package and stable request correlation identity;
- provider response execution is audited with `external_execution=true` and `executed=true`;
- cross-tenant execution is rejected;
- commercial SkillPackage execution fails closed without the separately verified purchase entitlement;
- provider configuration is not selectable through runtime skill input;
- provider redirects and oversized responses are rejected by the adapter;
- certification-boundary assertion succeeds and the fixture is torn down.

A first execution attempt exposed two real defects in CI: workflow provider settings were not injected into the API container, and the ToolRegistry workforce dispatch dropped `tool_call_id`. Both were corrected before the final exact-head validation passed.

**Evidence boundary:** governed SkillPackage provider execution is **VERIFIED on the deterministic CI HTTP provider fixture** for the exact PR head above. This is not evidence of an external production provider or customer environment. External production provider execution, customer acceptance, and real marketplace revenue remain **NOT VERIFIED**. The `v1.4.16` Production Certification remains the immutable certified release; `659c1e757c3cdc6dcc1d7c390a5bdd74bd3feff8` is not production-certified.


## W16 cross-tenant Skill Marketplace purchase — 2026-10-04

PR #857, `feat(w16): add cross-tenant Skill Marketplace purchase`, was validated at exact head `272ce9f52b73fcd72354d2f41efe1278a921e7a8` and merged with merge commit `8487f0b1133e20c4ce142d43fffd3ee69bf010c1`.

Exact-head validation completed successfully for the dedicated marketplace and shared application/security gates:
- W16 Cross-Tenant Skill Purchase Real-Stack — run `37201453142`;
- CI — run `37201453176`;
- CodeQL — run `37201453185`;
- W16 Skill API Real-Stack Contract — run `37201453134`;
- W16 Skill Provider Execution Real-Stack — run `37201453112`;
- W16 Third-Party Skill Publishing Real-Stack — run `37201453159`;
- Runtime Isolation/RBAC — run `37201453102`;
- Production Infrastructure Validation — run `37201453113`;
- HA Failure Recovery — run `37201453146`;
- Ephemeral DAST — run `37201453141`;
- Architecture Guard — run `37201453158`;
- Security/Privacy — run `37201453101`;
- Production Observability — run `37201453103`;
- Production Rollback & Alerting — run `37201453138`;
- Provider Integration — run `37201453190`.

The dedicated real-stack scenario verified:
- seller tenant owns the published SkillPackage and paid Product;
- buyer tenant owns the Employee;
- only the buyer can prepare the purchase and only a public publication can be purchased cross-tenant;
- purchase idempotency returns the same durable buyer-side purchase and deal;
- verified provider payment settles the purchase to PAID;
- the buyer receives a tenant-scoped verified purchase entitlement referencing the seller tenant and source publication;
- the buyer Employee receives an installation referencing the seller-owned package;
- the WorkforceRevenueEvent correlates the marketplace purchase and seller tenant;
- replay of the same verified provider event does not create duplicate purchase, entitlement, installation or revenue rows;
- direct buyer installation without the marketplace publication path remains rejected.

The database boundary keeps buyer Employee ownership separate from seller SkillPackage/Product ownership through tenant-consistent composite foreign keys. Marketplace ownership does not grant permissions, allowed tools, capability contracts or approval authority.

A first validation exposed ORM/migration index-name drift; the migration and ORM declarations were reconciled before the final exact-head gate passed. The full backend CI then passed 1240 tests with the corrected W16 tenant/FK contract.

**Evidence boundary:** cross-tenant marketplace purchase, verified settlement, entitlement creation, installation, revenue-event correlation, replay idempotency, and deterministic gross/platform-fee/seller-net allocation are **VERIFIED on the deterministic contract-test payment provider / real PostgreSQL CI stack**. This is engineering evidence, not proof of a real external customer purchase or realized customer revenue. External seller payout execution, tax calculation/settlement, and external production customer revenue remain **NOT VERIFIED**. No new Production Certification is claimed for `8487f0b1133e20c4ce142d43fffd3ee69bf010c1`.

## W16 marketplace financial allocation checkpoint — 2026-10-04

PR #860, `feat(w16): add marketplace settlement allocation ledger`, was validated at exact head `26e34cca56522d13880bc1599523e01767640425` and merged with merge commit `e4084462e414cd408b7035997bbd2b469b77c14a`.

Exact-head evidence:
- W16 Cross-Tenant Skill Purchase Real-Stack — PASS — Run `37202824376`;
- W16 Skill API Real-Stack Contract — PASS — Run `37202824326`;
- W16 Skill Provider Execution Real-Stack — PASS — Run `37202824380`;
- W16 Third-Party Skill Publishing Real-Stack — PASS — Run `37202824356`;
- CI — PASS — Run `37202824398`;
- CodeQL — PASS — Run `37202824329`;
- Ephemeral DAST — PASS — Run `37202824343`;
- Runtime Isolation/RBAC — PASS — Run `37202824391`;
- Architecture Guard — PASS — Run `37202824355`;
- Production Infrastructure Validation — PASS — Run `37202824370`;
- HA Failure Recovery — PASS — Run `37202824314`;
- Production Secret Management — PASS — Run `37202824344`;
- Production Observability — PASS — Run `37202824350`;
- Production Rollback & Alerting — PASS — Run `37202824366`;
- Production Hardening — PASS — Run `37202824330`;
- Phase 14.14 Security/Privacy — PASS — Run `37202824372`;
- Provider Integration Contract — PASS — Run `37202824365`;
- Workforce W1/W2/W3/W4/W5/W6/W8/W9 and related exact-head gates observed successful on the same head.

The settlement ledger records an explicit, operator-configured marketplace financial allocation after verified payment:
- gross payment amount;
- platform commission in basis points;
- platform commission amount;
- seller net amount;
- buyer tenant and seller tenant;
- verified provider event correlation;
- payout status fixed to `not_executed`;
- tax treatment fixed to `not_calculated`.

PostgreSQL constraints enforce valid fee bounds, non-negative amounts, and `platform_fee_amount + seller_net_amount = gross_amount`. The E2E gate verified the 15% CI policy fixture, seller net calculation, persistence, and one-row replay idempotency.

The settlement ledger is accounting state only. It does not execute money transfer to the seller, calculate tax, or create execution authority.

**Evidence boundary:** marketplace financial allocation accounting is **VERIFIED on the deterministic payment provider / real PostgreSQL CI stack** for the exact PR head above. External seller payout execution, tax calculation/settlement, external production customer payment and realized marketplace revenue remain **NOT VERIFIED**. The immutable `v1.4.16` production certification remains unchanged; merge SHA `e4084462e414cd408b7035997bbd2b469b77c14a` is not production-certified.

## W16 marketplace payout proposal checkpoint — 2026-10-04

PR #862, `feat(w16): add platform-admin seller payout proposals`, was validated at exact head `881ca9d498989ec7af522ec799fbb693dd708c5e` and merged with merge commit `c8fd849e77d2181f32700e1a7e52f03e48cd21e8`.

The platform-control-plane payout proposal boundary is now implemented and real-stack verified:
- proposal creation requires an active vendor tenant and active `is_platform_admin=true` user;
- the proposal derives only the recorded settlement seller-net amount and currency;
- payout provider remains `none`;
- destination remains `not_configured`;
- execution status remains `not_executed`;
- tax treatment remains `not_calculated`;
- one settlement can produce at most one active proposal;
- proposal replay returns the existing proposal without creating another row;
- creation is audited;
- no Workforce Tool, Agent capability, external payout call, bank destination or tax engine is introduced.

Exact-head W16 Cross-Tenant Skill Purchase Real-Stack Run `37203634612` completed PASS and recorded:
`MARKETPLACE SELLER PAYOUT PROPOSAL CREATION PASS`
and
`MARKETPLACE SELLER PAYOUT PROPOSAL IDEMPOTENCY PASS`.

The same exact head also passed W16 Skill API `37203634599`, W16 Third-Party Publication `37203634686`, CI `37203634678`, CodeQL `37203634695`, DAST `37203634654`, Runtime Isolation/RBAC `37203634634`, Architecture `37203634622`, Production Infrastructure `37203634605`, HA `37203634742`, Production Observability `37203634636`, Production Rollback & Alerting `37203634710`, and Security/Privacy `37203634663`.

**Evidence boundary:** seller payout proposal generation is **VERIFIED** on the deterministic CI / real PostgreSQL stack. Actual seller payout execution, payout-provider integration, tax calculation/settlement, external customer payment and realized marketplace revenue remain **NOT VERIFIED**. The immutable `v1.4.16` Production Certification remains unchanged; `c8fd849e77d2181f32700e1a7e52f03e48cd21e8` is not production-certified.


## W16 marketplace financial outcome reporting — 2026-10-04

PR #864, `feat(w16): add read-only marketplace financial outcome reporting`, was validated at exact head `bbef175cb0926827db065323ee718e1f080cedac` and merged with merge commit `027d8005df6ac9069a4734b9679bf839d1129a35`.

Exact-head validation completed successfully for the dedicated and shared gates:
- W16 Marketplace Financial Reporting Real-Stack — run `37204822747`;
- W16 Cross-Tenant Skill Purchase Real-Stack — run `37204822786`;
- CI — run `37204822802`;
- CodeQL — run `37204822799`;
- Runtime Isolation/RBAC — run `37204822831`;
- Ephemeral DAST — run `37204822773`;
- Architecture Guard — run `37204822768`;
- Production Infrastructure Validation — run `37204822764`;
- HA Failure Recovery — run `37204822782`;
- Production Observability — run `37204822766`;
- Production Rollback & Alerting — run `37204822752`;
- Security/Privacy — run `37204822753`.

The reporting contract is deliberately read-only and aggregates only recorded `SkillMarketplaceSettlement` rows, with seller-scoped filtering and payout-proposal counts. The real-stack gate verified gross amount, platform fee, seller net, verified settlement count, paid purchase count, seller filtering and zero-result isolation for another seller tenant. It also asserts that the reporting service contains no Stripe/ZarinPal/payment-provider calls and no create/mutation path.

**Evidence boundary:** marketplace financial outcome reporting is **VERIFIED** on the real PostgreSQL CI stack for the exact PR head above. This is reporting of recorded verified engineering/settlement state, not proof of a real external customer payment, realized customer revenue, or external seller payout. The immutable `v1.4.16` Production Certification remains unchanged; `027d8005df6ac9069a4734b9679bf839d1129a35` is not production-certified.


## W16 cross-tenant marketplace purchase HTTP API verification — 2026-10-04

PR #866, `test(w16): verify cross-tenant marketplace purchase HTTP API`, was validated at exact head `a481c4093879a4e7b58cfa03b3d6ea84a377959a` and merged with merge commit `34a0010087f7f821164ef7214f133fc83446e361`.

The exact-head HTTP/API verification added a real Docker Compose stack with PostgreSQL and Redis, a built API/worker/beat service, Alembic migration consistency checks, a deterministic `contract-test` payment provider, the HTTP marketplace purchase E2E, and focused purchase API contract tests.

Exact-head evidence observed on the merged PR:
- W16 Cross-Tenant Skill Purchase Real-Stack — PASS — Run `37205970070`;
- W16 Cross-Tenant Skill Purchase API Real-Stack — PASS — Run `37205970267`;
- CI — PASS — Run `37205970205`;
- CodeQL — PASS — Run `37205970054`;
- Architecture Guard — PASS — Run `37205970162`;
- Production Infrastructure Validation — PASS — Run `37205970102`;
- HA Failure Recovery — PASS — Run `37205970099`;
- Ephemeral DAST — PASS — Run `37205970056`.

The dedicated HTTP/API scenario verified, through the actual API boundary:
- seller tenant publication;
- buyer-tenant public discovery;
- cross-tenant purchase using buyer-owned Employee identity;
- buyer/seller tenant separation;
- seller self-purchase rejection;
- deterministic provider settlement state;
- durable purchase/deal buyer-side correlation;
- idempotent replay of the same purchase request;
- database-level buyer/seller/package ownership assertions;
- fixture cleanup through tenant deprovisioning.

The API verification also adds explicit route-order and request-schema regression coverage for the purchase endpoint. The HTTP evidence is engineering evidence only and uses the deterministic contract-test payment provider; it does not establish external customer payment or realized marketplace revenue.

**Evidence boundary:** W16 cross-tenant marketplace purchase HTTP/API verification is **VERIFIED** for exact head `a481c4093879a4e7b58cfa03b3d6ea84a377959a` and merged mainline `34a0010087f7f821164ef7214f133fc83446e361`. External customer payment, realized marketplace revenue, external seller payout execution and tax settlement remain **NOT VERIFIED**. The immutable `v1.4.16` Production Certification remains unchanged; `34a0010087f7f821164ef7214f133fc83446e361` is not production-certified.


### W16 governed marketplace payout-provider contract checkpoint — 2026-10-04

PR #869 introduced the explicit provider boundary for marketplace seller payouts without executing a seller payout.

Implementation boundary:
- `MarketplacePayoutProvider` is a named provider contract with explicit payout request/result state;
- the provider request requires proposal, settlement, seller tenant, positive amount, three-letter currency, destination reference and idempotency key;
- operator configuration selects the provider; runtime request data cannot select a provider;
- default provider `none` fails closed with `not_configured` and no execution;
- deterministic `contract-test` accepts/simulates a payout request but records `executed=false` and `external_execution=false`;
- unknown provider names fail closed;
- no payout proposal execution state was mutated;
- no bank, Stripe/Connect, tax engine or generic HTTP/shell execution was introduced.

Exact-head evidence:
- PR #869 exact head: `47f40a74e5910afd1aa5e172ad4443e6bd0b973c`;
- W16 Cross-Tenant Skill Purchase Real-Stack: PASS — Run `37213503702`, Job `111469255749`;
- the same real-stack job explicitly completed `Run focused purchase and payout-provider contracts` successfully;
- CI: PASS — Run `37213503698`;
- Provider Integration Contract: PASS — Run `37213503684`;
- Architecture Guard: PASS — Run `37213503691`;
- CodeQL: PASS — Run `37213503719`;
- Production Hardening: PASS — Run `37213503661`;
- Production Infrastructure Validation: PASS — Run `37213503706`;
- Security/Privacy Compliance: PASS — Run `37213503672`.

The validated PR head was squash-merged as `6f720cec7ee981afdc4e8b3c1824d60d5769c74c`.

Evidence boundary:
- governed marketplace payout-provider contract: **VERIFIED** on the exact PR head;
- deterministic contract-test payout adapter: **VERIFIED** as non-external/simulated;
- external seller payout execution: **NOT VERIFIED**;
- tax calculation/settlement: **NOT VERIFIED**;
- external customer payment / realized marketplace revenue: **NOT VERIFIED**;
- post-merge workflow evidence for `6f720cec7ee981afdc4e8b3c1824d60d5769c74c`: **NOT RUN / NOT VERIFIED**;
- production certification of the merge SHA: **NOT RUN / NOT VERIFIED**.

The immutable `v1.4.16` production certification remains unchanged.
