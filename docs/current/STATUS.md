# Current Project Status

**Architecture baseline:** V1.5 Agentic Operating Model  
**Certified release baseline:** `v1.4.11`  
**Latest certified release:** `v1.4.11` — exact-SHA certification PASS  
**Certified release commit:** `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`  
**Mainline engineering head:** `ee8996fdc82a7c9098ff808cece3e329ae3a6ddb`  
**Status date:** 2026-09-23  
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

The current Tool Registry contains 25 registered tools. The five governed workforce roles currently expose capability contracts for 53 operations, with exactly one approved semantic binding: `ai_trader:market_research -> workforce_market_research`. This binding is intentionally read-only, requires `run.execute`, has no autonomous trading side effect, and remains dependent on an operator-configured market-data provider. No existing generic tool is being approximated as another workforce capability. In particular, existing sales, product, calculator, document, order, and analysis tools are not silently reclassified as trading, campaign, creative, engineering, or executive-governance capabilities.

The `workforce_market_research` handler is tenant-context-bound and fails closed when the provider is not configured, returns invalid data, or returns an error. The provider endpoint is configuration-owned rather than caller-supplied, and production configuration requires HTTPS.

**Next implementation gate:** add further dedicated semantic workforce tools only where the operation can be implemented with a real, tenant-safe handler; then bind each operation explicitly and add runtime integration coverage for role authorization, capability freshness, tool binding, permissions, approval state, tenant identity, and execution provenance. Unsupported operations remain denied until such a binding exists.

## Current frontier

The current release frontier is `v1.4.11 RELEASE-CERTIFIED / LOCAL-ENGINEERING / EXTERNAL GATES OPEN`. No post-certification source changes are included in the certified snapshot. Continue regression watch for the audited product-completeness scope; do not reopen completed work without a regression, new requirement, or newly discovered unsupported surface.

The next application-code change requires a new candidate boundary and fresh exact-SHA certification. External production evidence remains intentionally open while the project is local.

## Security rule

Do not commit production hosts, private keys, registry credentials, webhook secrets, payment secrets, customer data or environment-specific access tokens. Missing required production inputs must fail closed.

### Edition-aware Test Center gate
- Test Center acceptance is scoped by Vendor / Reseller / Customer capability ownership.
- Shared authentication, tenant isolation/RBAC, audit, policy, safe execution and evidence controls are tested at the shared boundary.
- Edition-specific tests cover only authorized service groups; full service duplication across editions is explicitly not required.
- Cross-edition negative authorization tests remain mandatory.
