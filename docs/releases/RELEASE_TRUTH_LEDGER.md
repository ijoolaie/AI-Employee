# Release Truth Ledger

**Last reconciled:** 2026-10-03
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
| `v1.4.12` | `9c3f0ff7dc8fffcce8e069e18b11cf13d4dc0519` | **VERIFIED** | **CERTIFIED** — Run `37138840482` / Job `111248877948` | **OPEN — PENDING EXTERNAL EXECUTION** | **OPEN — PENDING EXTERNAL EXECUTION** |
| `v1.4.11` | `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f` | **VERIFIED** | **CERTIFIED** — Run `35848311037` / Job `107139710452` | **OPEN — PENDING EXTERNAL EXECUTION** | **OPEN — PENDING EXTERNAL EXECUTION** |
| `v1.4.10` | `b09f3e35d512e3c4d21be9d930539cbbe1d2d451` | **VERIFIED** | **CERTIFIED** — Run `35840044046` / Job `107112696112` | **OPEN — PENDING EXTERNAL EXECUTION** | **OPEN — PENDING EXTERNAL EXECUTION** |
| `v1.4.9` | `f1ce20c010779f5273eb5d0051da24cdd57b33f6` | VERIFIED | **CERTIFIED** — Run `35575615877` / Job `106256713583` | **NOT VERIFIED** | Pending |
| `v1.4.8` | `4f7c4676850b546a1c6bdf219ab9401202302e2d` | VERIFIED | **CERTIFIED** — Run `35568392010` / Job `106234691683` | **NOT VERIFIED** | Pending |
| `v1.4.7` | `48a6df0ea8a2fb0624e831fbdea55ee4548807f6` | VERIFIED | **CERTIFIED** — Run `35498984521` / Job `106047204166` | **NOT VERIFIED** | Pending |
| `v1.4.6` | `f3d60031332450ba616e2a1c705e85c0c2c5aefd` | VERIFIED | **CERTIFIED** | **NOT VERIFIED** | Pending |
| `v1.4.5` | `cc94bc9536f4f95680bb7a183313914c116ffcf2` | VERIFIED | **FAILED PRODUCT CERTIFICATION** — historical immutable release | **NOT VERIFIED** | Not accepted |

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
- W12 Virtual Office — planned.
- W13 Customer HQ Progression — planned.
- W14 Employee Appearance & Customization — planned.
- W15 Wardrobe / Cosmetic Marketplace — planned.
- W16 Skills Marketplace — planned.
- W17 Employee Career / Reputation — planned.
- W18 Virtual Meeting Rooms — planned.
- W19 Voice / Visual Interaction — planned.
- W20 Third-party Employee Marketplace — planned.
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