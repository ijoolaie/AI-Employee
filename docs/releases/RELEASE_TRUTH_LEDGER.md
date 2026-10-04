# Release Truth Ledger

**Last reconciled:** 2026-10-04
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