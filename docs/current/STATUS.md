# Current Project Status

**Architecture baseline:** V1.5 Agentic Operating Model  
**Certified release baseline:** `v1.4.11`  
**Latest certified release:** `v1.4.11` — exact-SHA certification PASS  
**Certified release commit:** `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`  
**Mainline engineering head:** resolve directly from the repository; this document intentionally does not embed the mutable current `main` SHA  
**Status date:** 2026-10-01  
**Latest published release:** `v1.4.11`  
**Latest certified release:** `v1.4.11`  
**Certification run:** `35848311037` — PASS (exact `v1.4.11` SHA)  
**Production deployment:** OPEN — PENDING EXTERNAL EXECUTION

The architecture baseline, release identity and engineering phase are independent axes. V1.5 is not a release number. The certified `v1.4.11` release is immutable and points to the exact SHA certified by the Production Certification workflow. Historical releases remain immutable and are not rewritten. Mainline contains post-certification documentation changes and is not itself certified.

## Executive status

Phase 11 Unified Execution acceptance is **COMPLETE**. Phase 12 Test Center P12.1-P12.6 is **IMPLEMENTED / OPERATIONAL HARDENING**. Phase 13 Agent Teams & Marketplace engineering is **COMPLETE**. Phase 14 engineering is **COMPLETE WHERE TRACKED**.

The exact-SHA Production Certification suite passed for `v1.4.11`. Certification run `35848311037` checked out SHA `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`, recorded the required certification evidence, and completed successfully. This is repository/GitHub-hosted production-like certification evidence; it does not claim external production deployment.

## v1.4.11 certified and published release

- **Release status:** **PUBLISHED** — exact certified SHA `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`.
- Exact-SHA Production Certification: **PASS**, run `35848311037`, job `107139710452`.
- Evidence artifact: `production-certification-evidence-v1.4.11-rc.1-90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`.
- Evidence digest: `sha256:bfd75a37126bc3fcb98080d9f4a9522ae1d0c05ab05ca686f0be985f53334048`.
- `v1.4.11` GitHub Release is published, not draft, not prerelease.
- `v1.4.11` tag resolves to the certified SHA; post-certification documentation commits are not part of the certified snapshot.

## Historical releases

- `v1.4.10` remains immutable at certified SHA `b09f3e35d512e3c4d21be9d930539cbbe1d2d451`.
- `v1.4.9` remains immutable at certified SHA `f1ce20c010779f5273eb5d0051da24cdd57b33f6`.
- Historical release records are retained for traceability and are not rewritten as current status.

## Release and deployment status

| Item | Status | Evidence |
|---|---|---|
| `v1.4.11` tag | VERIFIED | Exact certified release tag resolves to `90dd5cb...` |
| `v1.4.11` GitHub Release | PUBLISHED | Not draft, not prerelease |
| `v1.4.11` Production Certification | PASSED | Run `35848311037` / Job `107139710452` |
| Certified release SHA | VERIFIED | `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f` |
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

The current release frontier is `v1.4.11 RELEASE-CERTIFIED / LOCAL-ENGINEERING / EXTERNAL GATES OPEN`. Post-v1.4.11 semantic workforce engineering now includes an explicit code-reconciled binding inventory. The current source audit identifies 14 explicit Role → Operation → Tool bindings, while executable/evidenced status remains capability-specific. Unsupported workforce operations remain denied until a dedicated binding exists. No post-certification source changes are included in the certified snapshot. Continue regression watch for the audited product-completeness scope; do not reopen completed work without a regression, new requirement, or newly discovered unsupported surface.

The next application-code change requires a new candidate boundary and fresh exact-SHA certification. External production evidence remains intentionally open while the project is local.

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

