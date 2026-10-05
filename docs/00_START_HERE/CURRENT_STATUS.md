# Current Status

**Last reconciled:** 2026-10-05
**Latest certified release:** `v1.4.16`
**Certified release SHA:** `434a0c4a4501af08a393faaf58092add764df2a2`
**Stable Git tag:** `v1.4.16` — VERIFIED
**GitHub Release:** `v1.4.16` — PUBLISHED
**Exact-SHA Production Certification:** Run `37188879277` — PASS
**Certification job:** `111396657270` — PASS
**Current engineering head:** `main` — mutable; resolve directly from Git metadata
**Current status:** v1.4.16 CERTIFIED at its immutable SHA / current main is post-release engineering and **NOT release-certified**

## Release boundary

Certification applies only to the exact certified SHA `434a0c4a4501af08a393faaf58092add764df2a2`. Later commits, including documentation-only changes, do not inherit v1.4.16 certification.

## Executive truth

`v1.4.16` is the latest published, exact-SHA Production-Certified release. Product Gate failures = 0 and `production_deployment_claimed=false`.

W16 Skills Marketplace engineering is post-v1.4.16 mainline work. The immutable v1.4.16 release does not include these later W16 changes. Commercial paid-skill execution remains fail-closed behind verified purchase entitlement.

W10 Internal Company Dogfood has independently passed on the same SHA:
- Run `37189332690`
- Job `111398049109`
- W10 real-stack certification: **PASS**
- Governed commercial commitment certification: **PASS**
- Synthetic Stripe reconciliation: **PASS**
- Synthetic ZarinPal idempotency: **PASS**
- Governed SMTP delivery: **PASS**
- Production deployment: **NOT CLAIMED / NOT VERIFIED**

The W10 workflow did not produce a separate artifact in the currently observed GitHub run, so no W10 artifact digest is claimed.

## Documentation authority

This file is the current-status authority. Historical sections below preserve prior release evidence and must not override the current release identity above.


## Current-main post-certification engineering revalidation

Current-main and post-release engineering evidence must never be treated as v1.4.16 certification. The mutable `main` branch is post-release engineering evidence only; resolve its exact SHA directly from Git metadata when reporting a point-in-time state.

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
- W16 Skill marketplace: FOUNDATION IMPLEMENTED + REAL-STACK LIFECYCLE VERIFIED; exact-SHA Production Certification NOT RUN / NOT VERIFIED.
- W17 Employee career/reputation presentation: **IMPLEMENTED / REAL-STACK VERIFIED** on post-v1.4.16 mainline; Production Certification remains NOT RUN.
- W18 Virtual meeting rooms: **IMPLEMENTED / REAL-STACK VERIFIED** first vertical slice; Production Certification remains NOT RUN.
- W19 Voice/TTS/real-time visual avatar: **DESIGN FOUNDATION ACTIVE / NOT IMPLEMENTED**; provider execution remains unconfigured.
- W20 Third-party Employee marketplace: **IMPLEMENTED / REAL-STACK VERIFIED** first governed vertical slice on post-v1.4.16 mainline; W20 E2E Run `37308738607` passed on verification head `fe6377abcc7f110aa83a8cff3b8a0ea7e5c10c99`. External provider execution, marketplace revenue/payout/tax settlement and Production Certification remain NOT VERIFIED.
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

## W16 real-stack lifecycle reconciliation — 2026-10-04

This section is the latest W16 evidence reconciliation and supersedes earlier W16 status wording in this historical document.

**Status: FOUNDATION IMPLEMENTED + HARDENED + REAL-STACK LIFECYCLE VERIFIED — post-v1.4.16 mainline; exact-SHA Production Certification NOT RUN / NOT VERIFIED.**

Implemented and hardened:
- versioned tenant-scoped `SkillPackage` catalog and `EmployeeSkillInstallation` ledger;
- skill metadata validation rejects execution-authority declarations such as allowed tools, permissions, approval policy, capability contracts and tool bindings;
- concurrent install race is closed by the authoritative unique constraint boundary;
- database-level tenant consistency is enforced with tenant-scoped unique keys and composite foreign keys;
- published skill package content is immutable at the PostgreSQL boundary after publication, while lifecycle status remains mutable;
- tenant-scoped install/revoke/list API paths preserve employee/package tenant boundaries;
- audit provenance records presentation-only installation semantics and explicitly records unchanged permissions, allowed tools and execution authority;
- audit ledger entry hashing now assigns the immutable AuditLog UUID before hash computation, preventing persisted-ID/hash mismatches.

### Exact-head real-stack evidence

PR #846, `test: verify W16 skill lifecycle on real PostgreSQL`, was merged only after the exact head passed all observed required validation workflows.

- PR head: `73f6f15916926a80c872031cf200ef9e39ee47ce`
- Merge SHA: `d7550e0489ed43c5a3cda9e9151e199d05a07119`
- CI: **PASS** — Run `37193115014`
- CodeQL: **PASS** — Run `37193114955`
- Architecture Guard: **PASS** — Run `37193114850`
- Security/Privacy: **PASS** — Run `37193114998`
- Production Infrastructure Validation: **PASS** — Run `37193115005`
- HA Failure Recovery Validation: **PASS** — Run `37193114996`
- Production Observability: **PASS** — Run `37193114997`
- Production Rollback & Alerting: **PASS** — Run `37193115020`
- Runtime Isolation/RBAC Contract: **PASS** — Run `37193114911`
- Ephemeral DAST: **PASS** — Run `37193114933`

The lifecycle E2E covers package publication, installation, revocation, reactivation of the same installation, cross-tenant rejection, audit-action verification, audit metadata invariants, ledger verification, and persisted audit-row count.

During this validation, the lifecycle test exposed a real audit-ledger defect: the AuditLog UUID was generated during flush after the entry hash had already been computed. The service was corrected to assign `uuid4()` before hashing, and the audit regression test asserts that a recorded entry has an assigned ID. The final exact-head CI passed with this correction.

### Evidence boundary

**VERIFIED:** W16 lifecycle behavior on the exact PR head through the repository's real PostgreSQL CI stack.

**NOT VERIFIED:** exact-SHA Production Certification for the post-v1.4.16 W16 changes; live commercial purchase entitlement settlement; third-party skill publishing; external skill-provider execution; real customer marketplace revenue.

The immutable `v1.4.16` certification boundary remains unchanged. These W16 changes are post-release engineering evidence and do not inherit v1.4.16 certification.


## W16 real-stack employee skill API checkpoint — 2026-10-04

W16 employee skill HTTP API behavior has now been exercised on the real Docker/PostgreSQL stack after the lifecycle evidence above.

### Real-stack API evidence

PR #849, `test: verify W16 employee skill API on real PostgreSQL`, was validated at exact head **`4684445224cb6cc09cb432fb56d84451abcca305`** and squash-merged at **`d582dab6fb42918a523093ce72791b2c2b9552ac`**.

Exact-head workflow evidence:
- W16 Skill API Real-Stack Contract: PASS — Run `37193659040`
- CI: PASS — Run `37193659060`
- CodeQL: PASS — Run `37193659013`
- Architecture Guard: PASS — Run `37193658995`
- Production Infrastructure Validation: PASS — Run `37193659051`
- HA Failure Recovery Validation: PASS — Run `37193658991`
- Ephemeral DAST Validation: PASS — Run `37193659048`

The real-stack scenario verifies:
- same-tenant employee skill installation through HTTP API;
- same-tenant skill listing and revocation;
- cross-tenant listing/revocation rejection;
- commercial skill installation remains fail-closed without a verified purchase entitlement.

### Evidence boundary

This closes the focused **employee skill API / tenant-isolation / entitlement-boundary engineering checkpoint** on the real PostgreSQL stack.

It does **not** establish:
- post-v1.4.16 Production Certification;
- a verified purchase/order/payment entitlement implementation;
- third-party skill publishing;
- external skill-provider execution;
- customer marketplace revenue.

The paid-skill path remains intentionally fail-closed. Skill installation does not grant permissions, allowed tools, approval policy, capability contracts or execution authority.

This is post-release engineering evidence and does not inherit the immutable v1.4.16 certification.

## W16 current evidence reconciliation — 2026-10-04

The W16 sequence now has separate real-stack evidence for lifecycle, employee Skill API, verified purchase entitlement, third-party publication/discovery, and governed provider execution.

Latest application-code merge:
- PR #855 exact head: `20727001c2f967d850bda036c53acf7ccd326f81`
- merge SHA: `659c1e757c3cdc6dcc1d7c390a5bdd74bd3feff8`
- W16 Skill Provider Execution Real-Stack: PASS — Run `37199713576`
- CI: PASS — Run `37199713528`
- CodeQL: PASS — Run `37199713526`
- Runtime Isolation/RBAC: PASS — Run `37199713590`
- Ephemeral DAST: PASS — Run `37199713615`
- Production Infrastructure Validation: PASS — Run `37199713566`

Current evidence boundary:
- W16 lifecycle/install/revoke/list: **VERIFIED**
- W16 employee Skill API and entitlement gate: **VERIFIED**
- W16 third-party publication/discovery: **VERIFIED**
- W16 governed SkillPackage provider execution on deterministic CI HTTP provider fixture: **VERIFIED**
- W16 cross-tenant marketplace purchase/verified settlement mechanics on deterministic payment provider: **VERIFIED**
- external production Skill provider execution: **NOT VERIFIED**
- real external customer marketplace purchase/revenue: **NOT VERIFIED**
- marketplace financial allocation accounting (gross/platform fee/seller net): **VERIFIED**; external seller payout execution and tax settlement remain **NOT VERIFIED**
- Production Certification for post-v1.4.16 W16 merge SHAs: **NOT RUN / NOT VERIFIED**

All of these remain post-release engineering evidence and do not extend the immutable `v1.4.16` certification.


## W16 cross-tenant marketplace purchase — 2026-10-04

PR #857 was merged at `8487f0b1133e20c4ce142d43fffd3ee69bf010c1` after exact-head `272ce9f52b73fcd72354d2f41efe1278a921e7a8` validation.

The deterministic real-stack purchase gate verified seller/buyer tenant separation, public publication purchase eligibility, buyer-side purchase idempotency, verified-payment settlement, buyer entitlement referencing the seller package/publication, buyer installation of the seller-owned package, WorkforceRevenueEvent correlation and replay idempotency.

This is post-v1.4.16 engineering evidence. It does not establish a real external customer purchase, realized customer revenue, seller payout, platform commission, tax settlement or Production Certification for the merge SHA.

## W16 marketplace settlement allocation — 2026-10-04

Latest W16 financial-accounting checkpoint:
- exact PR head: `26e34cca56522d13880bc1599523e01767640425`
- merge SHA: `e4084462e414cd408b7035997bbd2b469b77c14a`
- W16 Cross-Tenant Skill Purchase Real-Stack: **PASS** — Run `37202824376`
- CI: **PASS** — Run `37202824398`
- CodeQL: **PASS** — Run `37202824329`
- Ephemeral DAST: **PASS** — Run `37202824343`

The new ledger records gross payment, operator-configured platform fee bps, platform fee amount and seller net. It explicitly records seller payout as `not_executed` and tax treatment as `not_calculated`.

**VERIFIED:** deterministic marketplace financial allocation accounting on the real PostgreSQL CI stack.

**NOT VERIFIED:** external seller payout execution, tax calculation/settlement, real external customer payment/revenue, and Production Certification of the post-v1.4.16 merge SHA.

The immutable `v1.4.16` certification remains unchanged.

## W16 seller payout proposal — 2026-10-04

Latest W16 financial-control-plane boundary:
- seller payout proposal generation: **VERIFIED** on deterministic CI / real PostgreSQL;
- actual seller payout transfer: **NOT VERIFIED**;
- payout-provider integration: **NOT VERIFIED**;
- tax calculation/settlement: **NOT VERIFIED**;
- real external marketplace payment/revenue: **NOT VERIFIED**;
- post-v1.4.16 Production Certification: **NOT RUN / NOT VERIFIED**.

PR #862 exact head `881ca9d498989ec7af522ec799fbb693dd708c5e` passed the dedicated cross-tenant marketplace real-stack gate `37203634612`, CI `37203634678`, CodeQL `37203634695`, DAST `37203634654`, Runtime Isolation/RBAC `37203634634`, Architecture `37203634622`, Production Infrastructure `37203634605`, HA `37203634742`, Production Observability `37203634636`, Production Rollback & Alerting `37203634710`, and Security/Privacy `37203634663` before merge. Merge SHA: `c8fd849e77d2181f32700e1a7e52f03e48cd21e8`.

The proposal is platform-admin/vendor scoped and explicitly non-executing: provider `none`, destination `not_configured`, payout `not_executed`, tax `not_calculated`. This does not extend the immutable `v1.4.16` certification.

## W16 marketplace financial reporting — 2026-10-04

The latest W16 engineering chain now has a read-only marketplace financial outcome report derived from recorded settlements.

- PR #864 exact head: `bbef175cb0926827db065323ee718e1f080cedac`
- merge SHA: `027d8005df6ac9069a4734b9679bf839d1129a35`
- W16 Marketplace Financial Reporting Real-Stack: **PASS** — Run `37204822747`
- CI: **PASS** — Run `37204822802`
- CodeQL: **PASS** — Run `37204822799`
- Ephemeral DAST: **PASS** — Run `37204822773`
- Runtime Isolation/RBAC: **PASS** — Run `37204822831`
- Production Infrastructure: **PASS** — Run `37204822764`
- HA Failure Recovery: **PASS** — Run `37204822782`

The report is read-only and settlement-derived. It does not create payment events, execute payouts, infer customer revenue, or change employee execution authority.

**VERIFIED:** marketplace financial outcome reporting on the real PostgreSQL CI stack.

**NOT VERIFIED:** real external customer payment/revenue, external seller payout execution, tax settlement, and Production Certification of the post-v1.4.16 merge SHA.


## W17 Employee Career & Reputation — 2026-10-05

W17 is now the next active engineering slice.

- Issue: #897.
- Semantic design contract: `docs/current/W17_EMPLOYEE_CAREER_REPUTATION.md`.
- Status: **IMPLEMENTATION MERGED / REAL-STACK EVIDENCE PENDING / NOT VERIFIED**.
- Implementation is merged on main at `e857528167e826b335a6448cce4b5ad3240a4d46`; it provides a read-only, tenant-scoped career evidence API derived from authoritative Employee, WorkItem and Run records.
- Missing evidence remains **UNKNOWN / UNVERIFIED**, never zero-filled or model-invented.
- Reputation scoring is deferred until an explainable deterministic evidence model is proven.
- No W17 state may modify permissions, tool bindings, approvals, quotas, billing, execution state or provider selection.
- Required exit evidence: API/schema + tenant-safe handler + negative/authorization tests + real PostgreSQL evidence + CI + documentation reconciliation.

W17 is post-v1.4.16 mainline engineering and has no transferred release certification.


## W17 verification checkpoint — 2026-10-05

W17 Employee Career & Reputation is now **IMPLEMENTED / REAL-STACK VERIFIED**.

- Integration commit: `e857528167e826b335a6448cce4b5ad3240a4d46`.
- Verification PR: #901; verification head: `f8b5a9734acbcc70ad165a2fbda2f326bfc2fa9a`.
- Dedicated W17 real-stack E2E: Run `37298325542`, Job `111724800314` — **PASS**.
- CodeQL on the verification head: Run `37298325646` — **PASS**.
- Verification workflow reconciliation merged as `53e47d2031dfc00de1b32e8b4fc8f1be0073b139`.
- Exact-SHA Production Certification: **NOT RUN**; no certification is transferred from `v1.4.16`.
- External deployment/customer acceptance: **NOT VERIFIED**.

W17's implementation/evidence gate is closed. The next roadmap slice may proceed to W18.

## W18 verification checkpoint — 2026-10-05

W18 Virtual Meeting Rooms first vertical slice is **IMPLEMENTED / REAL-STACK VERIFIED**.

- PR #903 merged at `a5fd482e456ba2060705aa24ff3f63de0e2a7665`.
- Verification head: `7ae4fe590d5483185637a8f344cc592979fec8bf`.
- Dedicated W18 real-stack E2E: Run `37299435745`, Job `111728381943` — **PASS**.
- CI: Run `37299435606` — **PASS**.
- CodeQL: Run `37299435510` — **PASS**.
- Architecture Guard: Run `37299435779` — **PASS**.
- Runtime Isolation/RBAC: Run `37299435639` — **PASS**.
- Security/Privacy: Run `37299435958` — **PASS**.
- DAST: Run `37299435653` — **PASS**.
- Production Infrastructure: Run `37299435583` — **PASS**.
- HA: Run `37299435752` — **PASS**.
- Observability: Run `37299435621` — **PASS**.
- Rollback/Alerting: Run `37299435625` — **PASS**.
- Exact-SHA Production Certification: **NOT RUN**.
- External deployment/customer acceptance: **NOT VERIFIED**.

W18 implementation/evidence gate is closed. W19 is now the next roadmap slice.

## W19 active design checkpoint — 2026-10-05

W19 Voice & Visual Interaction is now the active next slice under issue #904. The provider-agnostic contract and privacy/resource boundaries are documented in `docs/current/W19_VOICE_VISUAL_INTERACTION.md`. No live voice/video provider execution, camera capture, deployment or certification is claimed.

## W19 verification checkpoint — 2026-10-05

W19 first contract vertical slice is **IMPLEMENTED / REAL-STACK VERIFIED**. PR #905 merged as `0c882946931152efabc360d3adca2a8a17ce64cd`. Verification head `2dde32f24d076ca8d560336732d58faa006993bc`; dedicated W19 E2E `37304108903` passed and CI/security/production-like gates passed. External STT/TTS, camera/video, biometric processing, production deployment and exact-SHA Production Certification remain **NOT VERIFIED**.