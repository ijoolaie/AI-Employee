# Current Status

**Last reconciled:** 2026-10-04
**Latest certified release:** `v1.4.15`
**Certified release SHA:** `226dddcfbab7abde166c8cd6967d63a03f2d4e71`
**Stable Git tag:** `v1.4.15` — VERIFIED
**GitHub Release:** `v1.4.15` — PUBLISHED
**Exact-SHA Production Certification:** Run `37185102432` — PASS
**Certification job:** `111385347811` — PASS
**Current engineering head:** `w16-skills-marketplace` — post-`v1.4.15` branch; latest reviewed SHA `0b0507b5b7ac5572a5631ac5e587c206b031aa72`
**Current status:** v1.4.15 CERTIFIED / W16 FOUNDATION IN IMPLEMENTATION / EXACT-SHA W16 CERTIFICATION NOT RUN

## Release boundary

Certification applies only to the exact certified SHA `226dddcfbab7abde166c8cd6967d63a03f2d4e71`. W16 branch commits are post-release engineering work and do not inherit v1.4.15 certification.

## Executive truth

`v1.4.15` is the latest published, exact-SHA Production-Certified release. Its certification evidence reports Product Gate failures = 0, Playwright = 8 passed, and production deployment claimed = false.

W15 Employee Cosmetic Entitlements is implemented and release-certified in v1.4.15. Real external customer cosmetic payment/revenue remains NOT VERIFIED.

W16 Skills Marketplace has now started from the certified v1.4.15 SHA on branch `w16-skills-marketplace`. The first foundation slice adds versioned tenant-scoped skill packages and a tenant-scoped employee installation ledger. Skill manifests explicitly reject execution-authority fields, and installation audit metadata records that permissions, allowed tools, and execution authority are unchanged.

**W16 exact-SHA CI, security gates, real-stack evidence, and Production Certification are NOT RUN / NOT VERIFIED.**

## Current-main post-certification engineering revalidation

Current-main and post-release engineering evidence must never be treated as v1.4.15 certification.

## Previous certified release boundary

- Release: `v1.4.12`
- Exact certified SHA: `9c3f0ff7dc8fffcce8e069e18b11cf13d4dc0519`
- Production Certification: PASS
- Product Gate failures: **0**
- Frontend Playwright: PASS
- Evidence artifact: `production-certification-evidence-v1.4.12-rc.1-9c3f0ff7dc8fffcce8e069e18b11cf13d4dc0519`
- Evidence JSON SHA-256: `sha256:b380f8849b6347995c17bcec8a97de979b2a67b01d88dc26d0f02258b8779af1`
- Artifact ID: `11279782875`
- Production deployment claimed by certification: **false**
- Stable Git tag: **VERIFIED**
- GitHub Release: **PUBLISHED**
- Current execution stage: **LOCAL / ENGINEERING**
- Current main head: **resolve directly from the repository**
- External production & commercial gates: **OPEN — PENDING EXTERNAL EXECUTION**

Certification applies only to the exact certified SHA. Post-release code or documentation commits do not inherit certification.

## Executive truth

The latest repository-certified release is **v1.4.12 / `9c3f0ff...`**; W13 has now passed fresh exact-SHA Production Certification and is the next release candidate.

The latest code-bearing engineering head is PR #832 merge commit `b352ce41ab65031b5463542e254ddd3a2a1f459b`, followed by documentation-only PR #833 (`3d29aeffb44bcba7d833ca906884b6dc5fca814a`) and PR #834. The W13 candidate SHA `5d57d9929cc5e924c5b9147dc0b0a41d25f39d83` has independent exact-SHA certification evidence in run `37141161822`; it is not yet a published release.

Repository engineering, CI, production-like validation, product completeness work and fresh exact-SHA Production Certification are complete for the v1.4.11 tracked scope.

The project is currently being executed on the developer/local environment. No external production target is being used at this stage. Therefore gates that require a real target, live providers, staffed operations or external acceptance are intentionally **OPEN — PENDING EXTERNAL EXECUTION**. They are not current engineering failures and do not block local development or repository-level certification.

## Post-v1.4.11 production-readiness audit

| Area | Status | Evidence boundary |
|---|---|---|
| Immutable release identity | PASS | Tag `v1.4.11` resolves to certified SHA; GitHub Release published |
| Repository production-like certification | PASS | Exact-SHA certification run 35848311037, Product Gates 0, Playwright PASS |
| Production Compose topology | PASS | `docker-compose.production.yml` defines PostgreSQL, Redis, API, worker, Beat and frontend with health/restart controls |
| Migration gate | PASS | Certification workflow runs `alembic upgrade head`, `alembic check`, and single-head validation |
| Backup/restore engineering path | PASS | Backup/restore scripts and local recovery evidence exist |
| Rollback engineering contract | PASS | Controlled rollback/recovery scripts and runbook exist |
| Observability/SLO engineering contract | PASS | Prometheus/SLO/error-budget engineering contract and alert-routing contract exist |
| Real production deployment | OPEN — PENDING EXTERNAL EXECUTION | No external target is currently in use; this gate is intentionally open |
| Deployed image/digest identity | OPEN — PENDING EXTERNAL EXECUTION | Requires an external registry and deployed target |
| TLS/DNS/firewall/ingress on target | OPEN — PENDING EXTERNAL EXECUTION | Target-layer responsibility; external target does not yet exist |
| Secret-manager lifecycle/rotation on target | OPEN — PENDING EXTERNAL EXECUTION | Requires external secret manager and target lifecycle |
| Live provider/payment integration | OPEN — PENDING EXTERNAL EXECUTION | Requires live provider credentials/target validation |
| Production SLO/SLI/error budget | OPEN — PENDING EXTERNAL EXECUTION | Requires real production traffic and monitoring |
| Real backup/restore and measured RPO/RTO | OPEN — PENDING EXTERNAL EXECUTION | Local rehearsal exists; target measurement awaits external deployment |
| Vendor → Reseller → Customer target isolation/RBAC | OPEN — PENDING EXTERNAL EXECUTION | Requires deployed target actor-matrix execution |
| Authenticated DAST on deployed target | OPEN — PENDING EXTERNAL EXECUTION | Requires a running external target |
| Independent penetration/security review | OPEN — PENDING EXTERNAL EXECUTION | Intentionally deferred to external/security-review phase |
| HA/failure recovery on target | OPEN — PENDING EXTERNAL EXECUTION | Engineering contract exists; target drill awaits external deployment |
| Incident response/on-call | OPEN — PENDING EXTERNAL EXECUTION | Requires staffed external operations |
| Vendor/Reseller/Customer acceptance | OPEN — PENDING EXTERNAL EXECUTION | Acceptance occurs only after external target execution |
| Commercial go-live | OPEN — FUTURE EXTERNAL GATE | Becomes mandatory when moving from local execution to external/commercial operation |

## Current-main post-certification engineering revalidation

Current-main validation is **engineering evidence only** and does not transfer the v1.4.11 exact-SHA certification.

The post-certification dependency update PR #809 is merged at `c9c3cf...`. PR #826 is merged at `d32845d...` for the CI timeout process-termination fix. PR #827 is merged at `e844d55...` for the governed Workforce runtime-binding fix. PR #828 is merged at `783ab44...` and is documentation-only. The PR #827 head passed its listed engineering/security gates; no claim is made here that the post-certification main head is release-certified.

The current-main evidence boundary remains:

`CURRENT MAIN ENGINEERING EVIDENCE` ≠ `V1.4.11 RELEASE CERTIFICATION` ≠ `EXTERNAL PRODUCTION EVIDENCE`.

## Post-v1.4.11 governed Workforce semantic runtime evidence — 2026-09-29

The repository audit has now separated **runtime implementation** from **runtime evidence**:

- **Implemented:** governed Workforce role → operation → tool binding is enforced on the canonical Agent Run path after PR #827. The enforcement is active before `ToolRegistry.execute()`, and the governed runtime context remains active through actual Run execution.
- **Validated:** the generic real-stack Agent WorkItem E2E passes through Tenant → AgentDefinition → AgentTemplate → AgentInstance → AgentIdentity → Access Review → Runtime Binding → WorkItem → Run → Celery → audit correlation.
- **Evidenced:** PR #832 adds the minimum E2E-only deterministic tool-call/provider infrastructure and the local real-stack semantic matrix.
- **Validated:** the matrix executed the governed market-research tool through WorkItem → Run → Celery → ToolRegistry and verified persisted `tool.call` audit evidence plus negative controls for wrong role, stale capability, approval-required operation and cross-tenant assignment.
- **Scope rule:** production provider defaults and production market-provider behavior remain unchanged; the added provider is Compose/E2E-only.
- **Evidence boundary:** this is engineering evidence on the post-certification mainline and does not certify `v1.4.11` or constitute external-production evidence.

The semantic Workforce evidence gap identified by the roadmap is therefore closed for the currently implemented binding. Further workforce work should follow the domain-first rule: add a dedicated tenant-safe handler and explicit binding only when a concrete operation requires it.

## External-gate status rule

`OPEN — PENDING EXTERNAL EXECUTION` means the gate is intentionally unexecuted because the current project stage is local/engineering execution. It is neither PASS nor FAIL. Once an external target is provisioned, these gates become mandatory and must be evidenced before external/commercial go-live.

## Documentation authority rule

For current status, use this precedence:

1. `CURRENT_STATUS.md`
2. `CURRENT_PRIORITIES.md`
3. current roadmap/execution packs
4. dated historical audit documents
5. architecture/blueprint documents for architecture truth only

A blueprint, historical document or plan must not override current release/evidence truth.

## Security rule

No production host, private key, registry credential, webhook secret, payment secret, customer data or environment-specific access token belongs in Git history, GitHub issues, documentation or chat. Missing required production inputs must fail closed.



## W10 live sales response evidence — 2026-10-03

The post-v1.4.11 W10 dogfood workflow now has real live SMTP + mailbox response evidence.

- Live certification Run: **37103195020**
- Job: **111146601368**
- SHA: **7f7b0d9c917b0deb8891e23a862a227ef3bc939d**
- Result: **SUCCESS**
- Live SMTP send/provider acceptance: **VERIFIED**
- Live mailbox response observation: **VERIFIED**
- Live Message-ID response correlation: **VERIFIED**
- Live response ingestion: **VERIFIED**
- Live response idempotency: **VERIFIED**
- Live attribution: **VERIFIED — sent=1, delivered=1, responded=1**
- Customer identity/customer status: **NOT VERIFIED**
- Payment/revenue outcome: **NOT VERIFIED**

The certification observed the mailbox response on polling attempt 3/12 after the INBOX count increased from 83 to 84. This is live provider evidence on post-release mainline code, not v1.4.11 release evidence.

Current W10 commercial boundary: the technical sales engagement loop is verified through real SMTP → mailbox → correlated response → idempotent ingestion → attribution. The next evidence boundary is an independently verified customer outcome and, ultimately, a payment/revenue event.


## W11 Humanized Employee Identity & Visual Presentation — 2026-10-03

- W11 foundation: **IMPLEMENTED on post-v1.4.11 mainline**.
- Stable Employee name: **ALREADY SUPPORTED** by the Employee identity model.
- Stable Employee avatar reference: **IMPLEMENTED** as nullable `employees.avatar_url` via migration `w11_employee_avatar_identity`.
- API create/read path: **IMPLEMENTED**.
- Static avatar rendering UI: **NOT VERIFIED / NOT IMPLEMENTED IN THIS SLICE**.
- Voice/TTS: **NOT IMPLEMENTED IN THIS SLICE**.
- Real-time visual chat / camera / talking avatar: **NOT IMPLEMENTED / NOT VERIFIED**.
- GPU requirement: **NOT introduced by the identity foundation**.
- Release certification: **NOT RUN for this post-v1.4.11 change**.

Evidence boundary: W11 identity metadata is a lightweight foundation. It does not certify any image-generation, vision, TTS, lip-sync or video provider.

## Product Experience Expansion — 2026-10-03

The post-v1.4.11 workforce program now includes a planned Virtual AI Company Headquarters presentation layer over the governed Workforce Runtime.

- W11 Employee identity/avatar foundation: IMPLEMENTED on post-v1.4.11 mainline.
- W12 Virtual Office UI: NOT IMPLEMENTED / NOT VERIFIED.
- W13 Customer HQ progression/tiering: NOT IMPLEMENTED / NOT VERIFIED.
- W14 Employee appearance customization: NOT IMPLEMENTED / NOT VERIFIED.
- W15 Clothing/cosmetic commerce: NOT IMPLEMENTED / NOT VERIFIED.
- W16 Skill marketplace: NOT IMPLEMENTED / NOT VERIFIED.
- W17 Employee career/reputation presentation: NOT IMPLEMENTED / NOT VERIFIED.
- W18 Virtual meeting rooms: NOT IMPLEMENTED / NOT VERIFIED.
- W19 Voice/TTS/real-time visual avatar: NOT IMPLEMENTED / NOT VERIFIED.
- W20 Third-party Employee marketplace: NOT IMPLEMENTED / NOT VERIFIED.
- W21 AI Business Network: PLANNED / NOT IMPLEMENTED.
- New GPU requirement: NONE introduced by this architecture.

The Virtual Office must consume authoritative Employee, WorkItem, Run, Governance, Approval, Audit and business-metric state. Frontend animation must not invent operational state. Commercial cosmetics and marketplace assets must remain tenant-scoped and must not bypass permissions or approvals.

Next concrete slice: W12 Virtual Office Foundation — inspect existing status/read APIs, define a read-only office-state contract, map real runtime states, build the first CEO Office/employee-floor vertical slice, then test and evidence it.

No release is created merely because these plans are documented.

## W12 Virtual Office Foundation — 2026-10-03

W12 has now moved from planned design into a first implementation slice on post-v1.4.11 mainline.

### Implemented
- Tenant-scoped read-only `GET /api/v1/customer-dashboard/office` contract.
- Office state is derived from real `Employee`, `Run`, `WorkflowStepRun` and pending `WorkflowApproval` records; no second operational state store was introduced.
- Employee presentation states currently map real runtime evidence to `WORKING`, `WAITING_APPROVAL`, `IDLE`, `BLOCKED`, and `ESCALATED`. `MEETING` and richer project/cluster states remain future slices until their underlying runtime/session contracts exist.
- First customer `/office` UI with Executive/CEO desk, workforce floor, employee cards, avatar rendering and live polling.
- Customer navigation and dashboard entry point now expose the Virtual Office.

### Not yet implemented / verified
- Office progression/tiering based on spend, projects and workforce size: NOT IMPLEMENTED / NOT VERIFIED.
- Department/floor/campus clustering: NOT IMPLEMENTED / NOT VERIFIED.
- Appearance/gender/clothing customization: NOT IMPLEMENTED / NOT VERIFIED.
- Cosmetic/wardrobe commerce: NOT IMPLEMENTED / NOT VERIFIED.
- Virtual meetings, voice, TTS, real-time avatar/video: NOT IMPLEMENTED / NOT VERIFIED.

### As-built record
Detailed implementation record: `docs/current/W12_VIRTUAL_OFFICE_IMPLEMENTATION.md`.

### Evidence boundary
This W12 slice is post-v1.4.11 application code. Exact-SHA CI/certification for the current mainline is **NOT RUN / NOT VERIFIED**. No release tag is created from this implementation alone.



W12.2 checkpoint: current employee work visibility implemented from authoritative `Run.work_item_id` → tenant-scoped `WorkItem`; synthetic task/project/progress/meeting state remains intentionally unimplemented. Exact-SHA certification remains **NOT RUN / NOT VERIFIED**.


W12.3 checkpoint: Virtual Office CEO Desk now surfaces real tenant-scoped pending WorkflowApproval records and links them to the existing approvals workspace. The presentation layer does not mutate approval state. Exact-SHA certification remains **NOT RUN / NOT VERIFIED**.


## v1.4.12 release reconciliation — 2026-10-03

- Release: **v1.4.12**
- Exact certified/checked-out SHA: `9c3f0ff7dc8fffcce8e069e18b11cf13d4dc0519`
- Production Certification Run: **37138840482**
- Certification Job: **111248877948**
- Certification result: **PASS**
- Product Gate failures: **0**
- Evidence artifact: `production-certification-evidence-v1.4.12-rc.1-9c3f0ff7dc8fffcce8e069e18b11cf13d4dc0519`
- Evidence artifact SHA-256: `sha256:b380f8849b6347995c17bcec8a97de979b2a67b01d88dc26d0f02258b8779af1`
- GitHub Release: **PUBLISHED**
- Release assets: **BUILT/PUBLISHED** by the immutable release workflow.
- Production deployment: **NOT VERIFIED**; certification explicitly records `production_deployment_claimed:false`.
- Customer acceptance / live payment revenue: **NOT VERIFIED**.

This section supersedes older v1.4.11-only “latest release” statements above. Historical v1.4.11 evidence remains immutable and unchanged.

## W13 Customer HQ Progression — 2026-10-03

W13 is implemented on post-v1.4.12 mainline and has now passed exact-SHA Production Certification.

### Implemented
- Tenant-scoped HQ tier derived from authoritative subscription entitlement.
- Tenant-scoped plan, subscription, employee, workflow, monthly-run and monthly-token metrics exposed by the existing Virtual Office endpoint.
- Enabled capability labels derived only from truthy billing-plan feature data.
- Customer `/office` now presents HQ tier/capacity without creating authorization or execution authority.
- Backend tests cover entitlement-to-tier mapping and preservation of W12 office state/tenant boundaries.

### Evidence boundary
W13 exact-SHA CI/product gates: **VERIFIED PASS** on `5d57d9929cc5e924c5b9147dc0b0a41d25f39d83`. Production Certification: **PASS** — Run `37141161822`, Job `111255715821`. Evidence artifact: `production-certification-evidence-v1.4.13-rc.1-5d57d9929cc5e924c5b9147dc0b0a41d25f39d83`, digest `sha256:35e4b5dea1c57a3c021051f4dacaa841dee2f6c17cea9f0ed5db505676ea9479`. Certification records `production_deployment_claimed:false`. `v1.4.13` is not yet tagged/published.

As-built record: `docs/current/W13_CUSTOMER_HQ_PROGRESSION.md`.

Next slice: W14 Employee Appearance & Customization, preserving the hard boundary between presentation identity and business identity.


## v1.4.13 release reconciliation — 2026-10-03

- Release: **v1.4.13**
- Exact source/certified SHA: `5d57d9929cc5e924c5b9147dc0b0a41d25f39d83`
- Git tag: **VERIFIED** and resolves to the certified SHA.
- GitHub Release: **PUBLISHED** (release `402628656`).
- Production Certification: Run `37141161822`, Job `111255715821` — **PASS**.
- Evidence artifact: `production-certification-evidence-v1.4.13-rc.1-5d57d9929cc5e924c5b9147dc0b0a41d25f39d83`.
- Evidence digest: `sha256:35e4b5dea1c57a3c021051f4dacaa841dee2f6c17cea9f0ed5db505676ea9479`.
- Release assets: **BUILT/PUBLISHED**.
- Production deployment: **NOT VERIFIED**; certification records `production_deployment_claimed:false`.
- Customer acceptance / live payment revenue: **NOT VERIFIED**.

W13 is therefore inside the immutable v1.4.13 release boundary. W14 begins after v1.4.13 and requires fresh exact-SHA certification.

## W14 Employee Appearance & Customization — 2026-10-03

W14 foundation is now implemented on post-v1.4.13 mainline. Employee presentation profile is tenant-scoped and presentation-only. It cannot change permissions, quotas, approvals, tenant isolation, execution authority or billing.

Implemented: bounded gender presentation, outfit, hair style and accessory fields; tenant-scoped update endpoint; audit event; customer employee appearance controls.

Exact-SHA CI/certification for W14: **NOT RUN / NOT VERIFIED**.


## W16 Skills Marketplace — 2026-10-04

**Status: FOUNDATION IMPLEMENTED + HARDENED — EXACT-SHA CERTIFICATION NOT RUN / NOT VERIFIED.**

Implemented on post-v1.4.15 branch `w16-skills-marketplace`:
- versioned `SkillPackage` catalog records;
- tenant-scoped `EmployeeSkillInstallation` ownership/install ledger;
- bounded skill manifest rule rejecting `allowed_tools`, permissions, approval policy, capability contracts, and tool bindings;
- tenant-scoped install/revoke/list service operations;
- employee skill install/revoke/list API endpoints;
- audit provenance explicitly recording that installation does not change permissions, allowed tools, or execution authority;
- migration `w16_skill_marketplace`.

Not implemented by this slice:
- automatic permission/tool/capability expansion;
- silent changes to EmployeeVersion allowed tools;
- provider execution of a skill;
- verified payment-to-skill entitlement settlement;
- third-party skill publishing;
- exact-SHA CI/security/real-stack certification.

The next W16 slice should add governed package evaluation/compatibility checks and, separately, commercial purchase/verified-payment linkage if required. No skill installation may become an authorization shortcut.


### W16 review corrections — 2026-10-04

A focused security/tenant-boundary review identified and corrected:
- marketplace invariant errors previously surfaced as generic Python exceptions; they now use the application 422 error contract;
- skill revoke is now performed directly through a tenant + employee + package scoped service query, avoiding redundant lookup/TOCTOU behavior;
- skill listing now returns NOT_FOUND for an employee outside the tenant rather than silently returning an empty list;
- the Product foreign key is now RESTRICT rather than SET NULL, preventing a commercial SkillPackage from silently becoming an unpriced/free package when its product is deleted;
- tests cover the hardened error contract and product FK policy.

**W16 validation after these corrections: NOT RUN / NOT VERIFIED.**