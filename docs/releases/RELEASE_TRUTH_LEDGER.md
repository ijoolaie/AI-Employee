# Release Truth Ledger

**Last reconciled:** 2026-10-05
**Authority:** Git metadata + GitHub release records + explicit certification and deployment evidence

## Semantics

- **TAGGED** — Git tag exists and resolves to the recorded object.
- **BUILT** — build/CI evidence exists for the exact release commit or artifact.
- **CERTIFIED** — explicit certification evidence exists for the exact release commit.
- **DEPLOYED** — verified deployment evidence exists for the exact release identity.
- **EXTERNALLY_ACCEPTED** — independent Vendor/Reseller/Customer acceptance evidence exists.

These states are independent and must not be inferred from release names. `OPEN / PENDING EXTERNAL EXECUTION` is a deliberate project-stage state, not a failure.

## Current release identities

| Release | Commit | Tag | Certification | Deployment | External acceptance |
|---|---|---|---|---|---|
| `v1.4.16` | `434a0c4a4501af08a393faaf58092add764df2a2` | **VERIFIED** | **CERTIFIED** — Run `37188879277` / Job `111396657270` | **NOT VERIFIED / NOT CLAIMED** | **NOT VERIFIED** |
| `v1.4.15` | `226dddcfbab7abde166c8cd6967d63a03f2d4e71` | **VERIFIED** | **CERTIFIED** — Run `37185102432` / Job `111385347811` | **OPEN — PENDING EXTERNAL EXECUTION** | **OPEN — PENDING EXTERNAL EXECUTION** |
| `v1.4.14` | historical | **VERIFIED** | **CERTIFIED** | **OPEN — PENDING EXTERNAL EXECUTION** | **OPEN — PENDING EXTERNAL EXECUTION** |
| `v1.4.13` | `5d57d9929cc5e924c5b9147dc0b0a41d25f39d83` | **VERIFIED** | **CERTIFIED** — Run `37141161822` / Job `111255715821` | **OPEN — PENDING EXTERNAL EXECUTION** | **OPEN — PENDING EXTERNAL EXECUTION** |
| `v1.4.12` | `9c3f0ff7dc8fffcce8e069e18b11cf13d4dc0519` | **VERIFIED** | **CERTIFIED** — Run `37138840482` / Job `111248877948` | **OPEN — PENDING EXTERNAL EXECUTION** | **OPEN — PENDING EXTERNAL EXECUTION** |
| `v1.4.11` | `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f` | **VERIFIED** | **CERTIFIED** — Run `35848311037` / Job `107139710452` | **OPEN — PENDING EXTERNAL EXECUTION** | **OPEN — PENDING EXTERNAL EXECUTION** |

## v1.4.16 promotion checkpoint

`v1.4.16` is the latest published and exact-SHA certified release.

- certified SHA: `434a0c4a4501af08a393faaf58092add764df2a2`;
- Production Certification: Run `37188879277`, Job `111396657270` — **PASS**;
- Product Gate failures: **0**;
- evidence artifact: `production-certification-evidence-v1.4.16-434a0c4a4501af08a393faaf58092add764df2a2`;
- evidence digest: `sha256:7af4640395aefcffe0485fc3b276dad0dc794a97333efe59d531ef8af74d3d70`;
- Git tag: **VERIFIED**;
- GitHub Release: **PUBLISHED**;
- production deployment: **NOT CLAIMED / NOT VERIFIED**;
- W10 Dogfood Run `37189332690` / Job `111398049109`: **PASS**.

No later commit inherits this release certification.


## v1.4.11 promotion checkpoint

`v1.4.11` passed fresh exact-SHA Production Certification on 2026-09-23 and has now been promoted as the stable release.

- certified/checked-out SHA: `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`;
- workflow run: `35848311037`;
- certification job: `107139710452`;
- Product Gate failures: **0**;
- frontend Playwright: **PASS**;
- evidence JSON SHA-256: `bfd75a37126bc3fcb98080d9f4a9522ae1d0c05ab05ca686f0be985f53334048`;
- artifact ID: `10744805746`;
- stable Git tag: **VERIFIED** and resolves to the certified SHA;
- GitHub Release: **PUBLISHED** for `v1.4.11`;
- production deployment claimed by certification: **false**.

No source changes were made to the certified release commit after certification. Post-release documentation work is on top of the release boundary.

## v1.4.16 post-release certification record — 2026-10-04

W16 Skills Marketplace Foundation at `434a0c4a4501af08a393faaf58092add764df2a2` passed fresh exact-SHA Production Certification and was subsequently published as `v1.4.16`.

- Production Certification workflow run: `37188879277`;
- certification job: `111396657270`;
- certification result: **PASS**;
- Product Gate failures: **0**;
- evidence artifact: `production-certification-evidence-v1.4.16-434a0c4a4501af08a393faaf58092add764df2a2`;
- evidence artifact digest: `sha256:7af4640395aefcffe0485fc3b276dad0dc794a97333efe59d531ef8af74d3d70`;
- production deployment claimed by certification: **false**;
- Git tag/release: **VERIFIED / PUBLISHED**;
- W10 Dogfood Run `37189332690` / Job `111398049109`: **PASS**.

This supersedes the earlier candidate-state wording below/above; the immutable release remains bound to the exact certified SHA.

## External production boundary

The following remain intentionally open because the current project stage is local/engineering execution. They are independent of repository Production Certification:

- real production target and deployed-identity verification;
- live provider/payment/integration validation;
- measured production SLO/SLI and error budget;
- real backup/restore/DR with measured RPO/RTO;
- external Vendor → Reseller → Customer runtime isolation/RBAC;
- deployed-target authenticated DAST;
- independent penetration/security review;
- production networking/TLS and secret-management lifecycle evidence;
- HA/failure recovery and incident-response rehearsal;
- staffed alert ownership/on-call evidence;
- final Vendor → Reseller → Customer acceptance;
- residual-risk disposition and commercial go-live authorization.

These are not release-certification claims. They are future external gates, not current engineering failures.

## Current execution-stage rule

Until an external target is provisioned, deployment and external acceptance remain `OPEN — PENDING EXTERNAL EXECUTION`. When the project moves to external/commercial operation, these gates become mandatory and must be evidenced against the exact immutable release identity.

## Historical integrity rule

Do not retag, rewrite or reinterpret historical certified/failed releases. `v1.4.9` remains immutable at its certified SHA.


## Post-v1.4.11 W11 engineering checkpoint — 2026-10-03

A new application-code change has been added after the certified `v1.4.11` boundary:

- commit: `086aadef3e1025d06f98610847ea3b4f6baf7cac`
- scope: stable Employee avatar identity metadata + API/schema/migration/test foundation
- release tag: **NONE**
- exact-SHA certification: **NOT RUN**
- deployment: **NOT VERIFIED**

This change must not be described as `v1.4.11` functionality or certification. If promoted to a release, create a new immutable release from the exact certified SHA only after the applicable CI/product gates and fresh exact-SHA certification complete.

## Post-v1.4.11 Product Experience Expansion — 2026-10-03

The experience/commerce roadmap is planned mainline work, not release-certified functionality:
- W11 Employee Identity / Avatar foundation — implemented post-release; exact-SHA certification pending.
- W12 Virtual Office — implemented/evidenced post-release; exact-SHA certification boundary is separate from later mainline work.
- W13 Customer HQ Progression — implemented and exact-SHA certified/published in v1.4.13.
- W14 Employee Appearance & Customization — implemented post-release; exact-SHA certification pending.
- W15 Wardrobe / Cosmetic Marketplace — planned/not implemented.
- W16 Skills Marketplace — implemented + hardened + real-stack evidenced across lifecycle, API, publication, provider and marketplace-finance boundaries; post-v1.4.16 certification not verified.
- W17 Employee Career / Reputation — **IMPLEMENTED / REAL-STACK VERIFIED**; exact-SHA Production Certification not verified.
- W18 Virtual Meeting Rooms — **IMPLEMENTED / REAL-STACK VERIFIED** first vertical slice; exact-SHA Production Certification not verified.
- W19 Voice / Visual Interaction — planned.
- W20 Third-party Employee Marketplace — **IMPLEMENTED / REAL-STACK VERIFIED** first vertical slice on post-v1.4.16 mainline; dedicated W20 E2E Run `37308738607` passed on verification head `fe6377abcc7f110aa83a8cff3b8a0ea7e5c10c99`. External provider execution, marketplace revenue/payout/tax settlement and Production Certification remain NOT VERIFIED.
- W21 AI Business Network — planned.

Documentation of these phases does not create a release tag or certification. Any future release containing application code from these phases must be certified against its exact immutable SHA. Cosmetic/marketplace revenue is not claimed until a real commercial event is independently evidenced.

## W12 Virtual Office implementation checkpoint — 2026-10-03

Post-v1.4.11 mainline now contains the first W12 implementation slice:
- read-only tenant-scoped `/customer-dashboard/office` state contract;
- real Employee/Run/WorkflowApproval-derived presentation states;
- customer `/office` Virtual Office UI with CEO desk and employee floor;
- navigation/dashboard entry point.

Exact-SHA CI/certification: **NOT RUN / NOT VERIFIED**.
Release tag: **NONE**.
Deployment: **NOT VERIFIED**.
This does not modify immutable `v1.4.11`.



## v1.4.12 promotion checkpoint — 2026-10-03

`v1.4.12` is now the latest published and exact-SHA certified release.

- certified/checked-out SHA: `9c3f0ff7dc8fffcce8e069e18b11cf13d4dc0519`;
- Production Certification workflow run: `37138840482`;
- certification job: `111248877948`;
- Product Gate failures: **0**;
- certification result: **PASS**;
- evidence artifact: `production-certification-evidence-v1.4.12-rc.1-9c3f0ff7dc8fffcce8e069e18b11cf13d4dc0519`;
- evidence artifact digest: `sha256:b380f8849b6347995c17bcec8a97de979b2a67b01d88dc26d0f02258b8779af1`;
- GitHub Release: **PUBLISHED**;
- immutable release assets: **BUILT/PUBLISHED**;
- production deployment claimed by certification: **false**;
- external acceptance and revenue: **NOT VERIFIED**.

W12 Virtual Office and its tenant/approval/state hardening are inside this immutable release boundary. New W13 application-code work starts after this release and must not inherit v1.4.12 certification.

## v1.4.13 candidate certification checkpoint — 2026-10-03

W13 Customer HQ Progression has passed fresh exact-SHA Production Certification.

- candidate SHA: `5d57d9929cc5e924c5b9147dc0b0a41d25f39d83`;
- Production Certification workflow run: `37141161822`;
- certification job: `111255715821`;
- certification result: **PASS**;
- evidence artifact: `production-certification-evidence-v1.4.13-rc.1-5d57d9929cc5e924c5b9147dc0b0a41d25f39d83`;
- evidence artifact digest: `sha256:35e4b5dea1c57a3c021051f4dacaa841dee2f6c17cea9f0ed5db505676ea9479`;
- production deployment claimed by certification: **false**;
- Git tag/release: **NOT CREATED** at this checkpoint.

The candidate is therefore certification-complete but not yet a published release. A manual promotion must use exactly this SHA; no later SHA inherits the evidence.

## W17 active engineering checkpoint — 2026-10-05

W17 Employee Career & Reputation has been opened as issue #897 and its semantic design contract has been committed on branch `feat/w17-career-reputation-2026-10-05`.

Status:
- design contract: **CREATED**;
- application implementation: **NOT STARTED**;
- real-stack evidence: **NOT RUN**;
- exact-SHA Production Certification: **NOT RUN**.

The W17 contract is evidence-first and read-only for the first slice. It explicitly forbids fabricated career/reputation data and forbids W17 state from becoming an authorization or execution source.


## W17 post-merge checkpoint — 2026-10-05

W17 documentation/design (#898) and application implementation (#899) were merged into main through integration PR #900 at `e857528167e826b335a6448cce4b5ad3240a4d46`.

Current evidence boundary:
- W17 semantic contract: **MERGED**;
- W17 application API: **MERGED**;
- tenant/evidence unit coverage: **MERGED**;
- dedicated W17 real-stack E2E harness/workflow: **MERGED**;
- real PostgreSQL E2E result on the final mainline SHA: **PENDING / NOT VERIFIED**;
- exact-SHA Production Certification: **NOT RUN**.

Therefore W17 must not yet be called Implemented/Verified or Certified.


## W17 verification checkpoint — 2026-10-05

W17 Employee Career & Reputation has completed its implementation evidence gate.

- Implementation integration: `e857528167e826b335a6448cce4b5ad3240a4d46`.
- Dedicated real-stack E2E verification: Run `37298325542`, Job `111724800314` — **PASS**.
- Verification head: `f8b5a9734acbcc70ad165a2fbda2f326bfc2fa9a`.
- CodeQL on verification head: Run `37298325646` — **PASS**.
- Verification workflow reconciliation merged: `53e47d2031dfc00de1b32e8b4fc8f1be0073b139`.
- W17 status: **IMPLEMENTED / REAL-STACK VERIFIED**.
- Production Certification: **NOT RUN**. W17 does not inherit `v1.4.16` certification.

W18 is now the next permitted product-experience implementation slice.

## W18 verification checkpoint — 2026-10-05

W18 first vertical slice has completed its implementation evidence gate.

- PR #903 merge: `a5fd482e456ba2060705aa24ff3f63de0e2a7665`.
- Verification head: `7ae4fe590d5483185637a8f344cc592979fec8bf`.
- Dedicated real-stack E2E: Run `37299435745`, Job `111728381943` — **PASS**.
- CI: `37299435606` — PASS.
- CodeQL: `37299435510` — PASS.
- Architecture Guard: `37299435779` — PASS.
- Runtime Isolation/RBAC: `37299435639` — PASS.
- Security/Privacy: `37299435958` — PASS.
- DAST: `37299435653` — PASS.
- Production Infrastructure: `37299435583` — PASS.
- HA: `37299435752` — PASS.
- Observability: `37299435621` — PASS.
- Rollback/Alerting: `37299435625` — PASS.
- Production Certification: **NOT RUN**.

W19 is now the next permitted product-experience slice.

## W20 verification checkpoint — 2026-10-05

W20 #907 adds the first governed third-party Employee Marketplace slice.

- PR: #907.
- Scope: versioned seller package, evaluated source AgentTemplate, permission boundary, cross-tenant installation, buyer-owned import, revocation and audit.
- Real-stack E2E: **PENDING / NOT VERIFIED** at this checkpoint.
- Production Certification: **NOT RUN**.
- External provider execution and marketplace financial outcomes: **NOT VERIFIED**.



## W21 AI Business Network — 2026-10-05

W21 first governed vertical slice is **IMPLEMENTED / REAL-STACK VERIFIED** on post-v1.4.16 mainline.

- PR #909; merge SHA: `b6f9efdf067fdef5b9c6fad65002ee34998e5545`.
- Dedicated E2E: Run `37314768222` — PASS.
- CI/security/production-like gates on the verified head: PASS.
- Scope is proposal/approval/audit governed cross-company handoff only; no remote provider execution and no financial settlement.
- Exact-SHA Production Certification: **NOT RUN**.
- External customer/company network, contractual commitment, external revenue/payment/tax settlement, production deployment and customer acceptance: **NOT VERIFIED**.

This evidence does not alter the immutable v1.4.16 certification boundary. Any release containing W21 code requires fresh exact-SHA certification.
