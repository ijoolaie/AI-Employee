# AI-Employee Master Handoff — 2026-11-02

**Repository:** `ijoolaie/AI-Employee`  
**Default branch baseline:** `main` at `0c921d85fae806851fad1a58170d37bf8d46114d`  
**Architecture tracker:** [Issue #1350](https://github.com/ijoolaie/AI-Employee/issues/1350)  
**Architecture specification:** [Multi-Vendor Account, RBAC and Portal Architecture](MULTI_VENDOR_PORTAL_ARCHITECTURE_2026-11-02.md)

## 1. Latest project decision

On 2026-11-02 the user approved the multi-vendor account architecture:

- One default Vendor at launch, with multi-Vendor support built into the model from the beginning.
- Public Reseller and Customer registration attaches to the default Vendor.
- No public Vendor signup; Vendor provisioning and initial Vendor Owner creation use an authorized path.
- Vendor and Reseller child-account creation is permission-controlled and restricted to the creator's ownership boundary.
- A Reseller can manage only its own Customers and must have no read access to other Resellers or their Customers.
- Vendor, Reseller and Customer portals have separate UX and explicit portal-access grants.
- Primary identity, role, permissions, membership and active portal context are separate concepts.
- Membership activation requires verified payment or an explicitly granted Demo entitlement.

Detailed requirements and phased acceptance gates are in the architecture specification and issue #1350.

## 2. GitHub state at this checkpoint

- `main` exact HEAD: `0c921d85fae806851fad1a58170d37bf8d46114d` (PR #1336 merge).
- PR #1348: open Draft; daily Celery Beat read-only retention preview. Not merged.
- PR #1349: open Draft; GitHub Actions read-only retention preview. Not merged; requires dedicated staging database secret/variable before activation.
- PR #1257: open Draft/on hold pending authenticated real-runtime desktop/mobile evidence and human visual approval.
- Dependabot PRs #1340–#1347 are present in the open-PR inventory; review their exact-head CI and dependency context before merge.
- Issue #1350 created for the approved multi-vendor implementation.
- Issue #19 remains the separate external-production Vendor/Reseller/Customer isolation and RBAC evidence gate.
- Issue #1305 remains open for retention operational acceptance. No production cleanup is authorized or claimed.
- Latest production-certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`; current mainline commits do not inherit that certification.

## 3. Local workspace state observed

### Isolated staging worktree

Path: `C:\Users\Ali\AI-Employee\.worktrees\Ai-employee Staging`

- HEAD is detached at `0c921d85fae806851fad1a58170d37bf8d46114d`, matching `origin/main` at inspection.
- Local modifications/untracked files are staging/runtime artifacts and are intentionally preserved:
  - modified `frontend/next-env.d.ts`, `frontend/tsconfig.json`;
  - `README.local-staging.md`, `docker-compose.retention-staging.yml`, `run-retention-preview.cmd`;
  - local retention acceptance/preview/cleanup scripts;
  - Celery Beat schedule database and WAL/SHM files.
- Do not stage or commit those unrelated local runtime artifacts as part of the architecture documentation or implementation.

### Primary checkout

Path: `C:\Users\Ali\AI-Employee`

- Git status is dirty and branch `work/support-acceptance-20261017` is 153 commits behind `origin/main` at inspection.
- It contains pre-existing modified and untracked commercial portal, login, edition, test and documentation work.
- **Do not reset, clean, stash, switch, rebase, pull, fast-forward or modify the primary checkout.** Preserve all its changes.

## 4. Local staging evidence

Previously recorded local-only state (reconfirm before relying on it):

- Isolated PostgreSQL 16 and Redis containers use loopback-only ports 15434 and 16379.
- Backend API: `http://127.0.0.1:8000`; frontend Next.js development server: `http://127.0.0.1:3000`.
- Celery worker and Beat were running; retention preview is read-only and the daily task does not perform deletion.
- Synthetic two-tenant retention acceptance passed, including tenant isolation and idempotency. No real user data was purged.
- Three local test users were reported created by the user. Their credentials and roles are not recorded here and must not be inferred or changed.
- The deterministic AI provider is configured; live AI provider, external SMTP, payments and external integrations are not certified by this local stack.

Local state is not re-certified by this documentation update. Re-run checks before relying on process/container status.

## 5. Work in progress and immediate next steps

1. Reconcile the isolated worktree with the documentation branch for this handoff; preserve all staging artifacts.
2. Audit actual source code for tenant models, User/Membership, signup/login, edition dependencies, RBAC delegation, portal guards, API data scoping, commercial entitlements and existing portal UIs.
3. Publish a source-backed Gap Analysis under issue #1350. Do not duplicate Phase 14 functionality already present.
4. Add tests for ownership and authorization gaps before changing behavior.
5. Implement in small isolated PRs: ownership/provisioning, scoped authorization, signup/membership, portal context, then separate UI.
6. Update this handoff, `docs/00_START_HERE/CURRENT_STATUS.md`, the architecture tracker and the local handoff after each meaningful checkpoint, recording exact SHAs and test evidence.

## 6. Synchronization protocol

- GitHub `main` is the shared integration source of truth; never assume a local checkout is current without checking its exact SHA.
- Use a dedicated branch/worktree per implementation slice.
- Before work: inspect local Git status, branch and HEAD; inspect GitHub main, open PRs/issues and relevant CI.
- During work: keep changes scoped and preserve unrelated untracked/runtime artifacts.
- Before publishing: run focused tests, full relevant checks, `git diff --check`, and review the exact diff.
- Publish the same content/commit lineage to GitHub; verify PR head SHA and local branch SHA match.
- After merge: fetch the new main SHA into the isolated worktree, rerun required smoke checks, and update local/GitHub handoff and state.
- Never claim local/GitHub parity when one side could not be inspected or synchronized.

## 7. Safety and release boundaries

- Production database, deployment, account mutation, payment activation and destructive retention require separate explicit authorization.
- Do not alter the user's three existing local accounts without an explicit request.
- Do not treat CI as production certification, live customer acceptance or visual QA.
- Keep the original dirty primary checkout untouched.
## 8. Source-backed architecture gap analysis — 2026-11-02

Source review was performed against `main` SHA `0c921d85fae806851fad1a58170d37bf8d46114d`. The detailed findings are in [MULTI_VENDOR_PORTAL_GAP_ANALYSIS_2026-11-02.md](MULTI_VENDOR_PORTAL_GAP_ANALYSIS_2026-11-02.md).

Confirmed reusable foundation:
- `Tenant.tenant_kind` / `parent_tenant_id` hierarchy, User-to-Tenant association, role/permission tables, edition-specific backend dependencies, direct-child provisioning, lifecycle and entitlement services.
- Vendor → Reseller and Reseller → Customer provisioning endpoints.
- Distinct frontend route groups; Reseller and Customer UI foundations; Phase 14 real-stack isolation/RBAC CI harness.

Confirmed gaps:
- Public registration creates a standalone root Customer tenant, activates the user immediately, assigns a broad tenant Admin role and starts a generic 14-day billing trial. It does not select Reseller/Customer or attach to a default Vendor.
- No authoritative default-Vendor resolver/marker or Vendor provisioning endpoint was found in the inspected core path.
- Direct Vendor → Customer provisioning is absent.
- Generic tenant-admin role assignment exists and prevents assigning permissions beyond the actor's own set, but child creation is still guarded by edition Admin/Owner role rather than the specific per-user action grant; the inspected tenant-admin API has no user create/invite endpoint.
- Portal routing is same-kind-only in `frontend/lib/portal-access.ts`; backend edition dependencies also deny cross-edition access. No server-validated portal context/grant flow was found.
- Vendor dashboard is a placeholder; Reseller and Customer UI foundations are more developed.
- Existing Phase 14 tests cover important isolation paths but do not establish every data surface or the new portal-context behavior.

**Current conclusion:** do not start broad UI changes. The first application slice must define default-Vendor provisioning/ownership and permission/portal authorization contracts, after a deeper data-surface and existing-user migration audit.

## 9. Documentation PR and merge status

- PR #1351 was merged after exact-head Documentation Truth Consistency and CodeQL workflows both completed successfully.
- Merge commit on `main`: `2819cdc651c0a769b653bf3c92cd74e21a62925a`.
- The merged change contains the approved architecture, source-backed gap analysis, documentation index and project handoff/status updates.
- Implementation tracker: [Issue #1350](https://github.com/ijoolaie/AI-Employee/issues/1350).

## 10. Local worktrees and synchronization

### Previous Local Staging worktree

Path: `C:\Users\Ali\AI-Employee\.worktrees\Ai-employee Staging`

- Branch: `docs/multi-vendor-portal-architecture-20261102`.
- Successfully fetched and fast-forwarded to the documentation branch head `57b1505ab89700b2777c8fcefa358ff94965bd1e`; the post-fast-forward `git status` showed local HEAD tracking the matching origin branch.
- `git diff --check` exit 0; only a line-ending warning was emitted for `frontend/tsconfig.json`.
- Pre-existing local staging changes remain: modified `frontend/next-env.d.ts`, `frontend/tsconfig.json`, retention preview/acceptance scripts, compose/wrapper/readme and Celery Beat schedule artifacts. Preserve them; do not stage them in feature work.

### New clean implementation worktree

Path: `C:\Users\Ali\AI-Employee\.worktrees\Ai-employee MultiVendor`

- Branch: `feature/multi-vendor-foundation-20261102`.
- Created from merged `origin/main` at `2819cdc651c0a769b653bf3c92cd74e21a62925a`.
- Verified `git status` clean, branch tracking `origin/main`, and `git diff --check` exit 0.
- Focused backend baseline: `tests/test_edition_boundaries.py` plus `tests/api/test_tenant_admin_role_boundary.py` — 21 passed in 6.64s.
- No application code or database records have been changed in this worktree yet.

### Primary checkout

- `C:\Users\Ali\AI-Employee` remains dirty and must remain untouched. No reset, clean, stash, switch, rebase, pull or fast-forward was performed there.

## 11. Current implementation findings and next action

- Existing `TenantContext` binds a User to its home Tenant and validates JWT `tenant_id` against `User.tenant_id`. It has no separate target portal/resource context. The implementation must retain actor identity/home tenant and separately resolve an authorized context tenant; it must never rewrite the primary identity.
- `has_permission` already evaluates tenant-local role permissions; `require_edition` still relies on Admin/Owner role names. The edition API-key scope contract is separate from bearer-user RBAC.
- `tenant_admin.py` supports tenant-scoped user listing, status updates and permission-subset-checked role assignment, but the inspected API has no user create/invite endpoint.
- `provision_child_tenant` supports Vendor→Reseller and Reseller→Customer, creates an active child and fixed Admin user, and commits internally. It does not support direct Vendor→Customer or per-user operation grants.
- `license_service.issue_license` has its own hierarchy traversal but currently assumes Customer→Reseller→Vendor; direct Vendor→Customer requires an explicit extension. Vendor hierarchy listing also omits direct Customer children.
- Ordinary API services commonly scope by `ctx.tenant_id`; file and knowledge services receive explicit tenant IDs. Context-aware access must be opt-in and preserve default tenant-local behavior. Support escalation participant checks and resource-derived worker tenant scopes should be reused.
- Existing focused tests are baseline regression evidence only; they do not prove the approved portal matrix or sibling-Reseller isolation.

**Next:** finish route/service/repository and background-task scope audit; define a safe migration strategy for existing root Customer tenants without automatic re-parenting; then implement backend action permissions and scoped portal context with negative tests before any UI redesign.

## 12. Safety and release boundaries

- No production deployment, account mutation, payment activation or destructive retention operation is authorized by this work.
- Do not alter the three local test users without an explicit request.
- CI success is not production certification, external customer acceptance or visual QA.
- Keep issue #19 as the external-production tenant isolation/RBAC evidence gate.

## Implementation slice 1 — direct Vendor-owned Customers

Draft PR [#1353](https://github.com/ijoolaie/AI-Employee/pull/1353) is open from `feature/multi-vendor-foundation-20261102` at `b73e03537801824be6ace88b483fae029aacfbb1`.

Implemented in this slice:
- Vendor direct Customer provision/list/suspend/resume/deprovision endpoints.
- Vendor license target listing includes direct Customers.
- Tenant provisioning, direct-child access and entitlement delegation support Vendor→Customer while preserving Vendor→Reseller→Customer and denying Vendor→grandchild access.
- Commercial license hierarchy supports both direct Vendor Customer and Reseller-owned Customer, with malformed/foreign hierarchy rejection.
- Explicit API-key route scopes and contract docs.

Validation: 36 focused offline tests passed; Ruff passed. Database-backed live API/license tests could not run because dedicated test DB environment variables are absent; no staging DB was substituted. Exact-head CI is pending. PR is Draft and must not merge until PostgreSQL-backed API validation and CI pass.

Not implemented by this slice: per-user action grants, child user invitation/creation, default Vendor provisioning, public signup/payment/Demo lifecycle, server-validated portal context or distinct portal UI. Existing Admin/Owner route gates remain temporarily.

Local branch and GitHub PR head match. Local worktree clean after commit/push. Handoff and Current Status in the implementation branch record this checkpoint.

## Delegated authorization contract — 2026-11-02

- Added `docs/current/MULTI_VENDOR_DELEGATED_AUTHORIZATION_CONTRACT.md`: action-level permission catalogue, tenant-kind + permission checks, delegation ceilings, secure tenant-local invitation lifecycle, server-authorized portal access, negative test matrix and rollout guidance.
- Contract is documentation only; no claim that action-level enforcement or user invitations are already implemented.
- PR #1353 exact-head CI completed with all recorded workflows green; PR remains Draft pending dedicated PostgreSQL-backed API tests and review.
- Next: implement permission dependency enforcement and role authoring, then tenant-local invitation lifecycle. Keep local implementation worktree fast-forwarded with the GitHub branch.

## First delegated action-permission enforcement slice — 2026-11-02

- `POST /edition/reseller/customers` now uses a dedicated dependency requiring Reseller edition boundary plus the explicit tenant-local `reseller.customer.create` permission. Admin role membership or `is_superuser` alone cannot satisfy the action grant.
- API-key scope remains independently enforced. Tests cover allow, missing grant, foreign-tenant permission isolation, superuser non-bypass and API-key scope denial.
- Validation: 26 focused tests passed; Ruff and `git diff --check` passed. Commit `c15e44d1`.
- Scope limitation: this is only the first action-permission endpoint. Vendor provisioning grants, remaining control-plane routes, role delegation ceiling, invitation lifecycle and portal grants remain outstanding. Keep PR #1353 Draft until dedicated PostgreSQL-backed API validation is complete.

## Reseller action coverage expansion — 2026-11-02

- Action dependency factory now protects the Reseller Customer control-plane surface end-to-end: list, create, suspend, resume, deprovision and entitlement delegation each require their own tenant-local action permission.
- API-key route scopes remain independently enforced. Focused tests: 29 passed; Ruff and `git diff --check` passed. Commit `65e4e2af`.
- Remaining work is explicit: Vendor permission bootstrap/enforcement, other edition/license/support operations, tenant-local user invitation, role delegation ceilings, portal grants and dedicated PostgreSQL-backed API tests.

## PostgreSQL CI fixture correction — 2026-11-02

- CI at `48a4c46a` surfaced two expected fixture updates after enforcing `reseller.customer.read`. Updated both PostgreSQL API test fixtures to create and attach that explicit tenant-local permission to their Reseller test role; no production bypass was introduced.
- Commit `708d9300`; 29 focused offline tests and Ruff pass. New exact-head PostgreSQL CI is pending. Shared Staging was not used.

## Vendor control-plane action permission slice — 2026-11-02

- Added tenant-local Vendor action dependencies and enforced them on Vendor direct Customer list/create/suspend/resume/deprovision, Reseller list/create/suspend/resume/deprovision, and Vendor license-target listing.
- Codes: `vendor.tenant.read`, `vendor.reseller.read/create/manage`, `vendor.customer.read/create/manage`. Grants are resolved only from roles owned by the active Vendor tenant. Superuser and foreign-tenant permissions do not bypass. API-key scopes remain an independent gate.
- Focused validation: 38 passed; Ruff and `git diff --check` passed. Commit `8f93e098`.
- Rollout caveat: no canonical Vendor root provisioning/bootstrap path currently grants this permission set to the initial Vendor Admin role. Do not deploy/enforce for existing Vendor tenants until a tested bootstrap/upgrade mechanism is added. Next work: bootstrap and delegation ceiling, then tenant-local invitation.
- Previous SHA `4272164e` had all 22 workflows green; exact-head CI after `8f93e098` is pending.


## Vendor permission PostgreSQL fixture correction — 2026-11-02

- Exact-head CI for `90a7484e656fe41b55b43b06fe3833427e13f5e2` exposed two PostgreSQL API fixture failures: Vendor list-Reseller requests now correctly require the tenant-local `vendor.reseller.read` grant.
- Updated `test_edition_live_api_access.py` and `test_commercial_license_postgres_api.py` to attach that permission to the appropriate Vendor test Admin roles (including the second Vendor fixture used for cross-Vendor isolation). Production authorization was not weakened.
- The same exact-head run had frontend success and all non-CI workflows green; Backend CI failed only in those two PostgreSQL API assertions (1,842 passed, 2 failed). Re-run required after fixture correction.
- Ruff passed for both changed fixtures; `git diff --check` passed. PR #1353 remains Draft; no merge or deployment.

## Exact-head CI fixture follow-up — 2026-11-02

- CI run #4284 on `c38f3adf` passed all workflows except Backend CI. Backend had `1 failed, 1843 passed, 1 deselected`; the single failure was `test_license_http_hierarchy_revocation_and_audit` inserting duplicate globally unique `Permission` rows for `vendor.reseller.read` across two Vendor roles (and a duplicate assignment in one role fixture).
- Fixed the test fixture to query or create the `vendor.reseller.read` Permission row once and attach the same row to both Vendor Admin roles. Production authorization remains unchanged and strict.
- Commit `550afd293ec61ab2e9c0dfa071848b21ab1f9b5f` is pushed to PR #1353. Ruff and `git diff --check` pass. The local PostgreSQL test was blocked because `COMMERCIAL_LICENSE_TEST_DATABASE_URL` is not configured; the test failed closed before connecting. No Staging database was used.
- Exact-head CI run #4285 is running on `550afd29`; Documentation Truth Consistency passed, and other workflows were queued/in progress at last inspection. Keep PR #1353 Draft until Backend/PostgreSQL CI and all required checks pass.
- The isolated MultiVendor worktree was fetched and fast-forwarded from `3375bde4` to `c38f3adf`, then the fixture correction was committed and pushed. The current status file records the same checkpoint. Reverify final HEAD/status after docs commit. The dirty primary checkout and Staging/Production environments were not modified.

## 2026-11-03 — exact-head CI green; Vendor bootstrap gap confirmed

- Current PR #1353 HEAD: `841ca8072cd04de45d2d80411c60ee9df5867c1b`; isolated local MultiVendor worktree is clean and matches `origin/feature/multi-vendor-foundation-20261102` at the same SHA.
- Exact-head GitHub Actions: **22/22 successful, 0 failed**. Backend CI #4286, CodeQL, Runtime Isolation/RBAC, DAST, Security Privacy Compliance, Architecture Guard, Observability, recovery and infrastructure workflows all completed successfully.
- PR #1353 remains open and Draft. Dedicated local PostgreSQL API validation remains unavailable because `COMMERCIAL_LICENSE_TEST_DATABASE_URL` is not configured. Do not substitute shared Staging. No merge or deployment.
- Source audit: `Tenant.tenant_kind` defaults to `customer`; `auth_service.register_tenant_and_user` creates a standalone root tenant and applies only `DEFAULT_TENANT_ADMIN_PERMISSIONS`. There is no configured default-Vendor resolver or canonical Vendor-root bootstrap path. Existing migration `20260820_edition_runtime_boundaries.py` identified historical Vendor roots by `users.is_platform_admin=true`; `p5_vendor_identity_backfill.py` backfills release identity only, not Vendor action grants.
- Vendor action dependencies strictly require tenant-local grants: `vendor.tenant.read`, `vendor.reseller.read/create/manage`, `vendor.customer.read/create/manage`. `is_superuser` does not bypass these checks. This is correct least-privilege behavior; deploying without bootstrap/backfill risks locking out existing Vendor Admins.
- No application code or migration changed during this investigation. Next bounded implementation: add a reusable idempotent permission-catalogue/role bootstrap for Vendor roots; create a safe deterministic backfill for eligible existing Vendor Admin roles with audit evidence; route public registration to the configured default Vendor as a child Customer (no public Vendor creation; fail closed for absent/ambiguous default Vendor); add isolated PostgreSQL tests for idempotency, preservation of custom role grants, exclusion of non-Vendor tenants, ambiguous/missing root, and cross-Vendor isolation. Reconcile migration heads before authoring the Alembic revision.
- Preserve the primary checkout (dirty) and all Staging/Production environments; none were changed. Keep PR Draft until bootstrap, signup routing and PostgreSQL acceptance gates are implemented and verified.

## 2026-11-03 — Vendor Admin permission backfill migration drafted

- Added Alembic revision `w29_vendor_admin_perms` in `backend/alembic/versions/w29_vendor_admin_action_permissions.py`, based on `w28_customer_slot_expiry_index`. It idempotently seeds the seven Vendor action permissions and attaches them only to tenant-local Admin/Owner/Tenant_Admin roles linked to an `is_platform_admin` user in a root Vendor tenant. Child tenants and arbitrary Vendor roles/users are excluded. Downgrade is intentionally non-destructive and retains grants.
- Added `backend/tests/test_vendor_permission_backfill_migration.py`; it validates permission catalogue rows, idempotency clauses, strict root-Vendor/platform-admin eligibility, allowed role names, and non-destructive downgrade. Focused test after final revision-ID shortening: 2 passed. Ruff passed on the final migration and test. `alembic heads` returns exactly one head: `w29_vendor_admin_perms`.
- This is a drafted migration, not an applied migration. It has not been run against any database; execute upgrade/rollback contract checks only on a dedicated disposable PostgreSQL database. Do not use Staging/Production.
- The migration backfills only legacy Vendor roots whose Admin/Owner role is already associated with a platform-admin user. It does not create a missing root, establish a fresh default Vendor, route public signup to that Vendor, or create audit-ledger events. Those remain explicit follow-ups before deployment; do not infer full bootstrap completion from this migration.
- Exact PR head before this uncommitted code work was `0cebc69e816196b6910f7712700b97bccc1a6905`; documentation-only push had no associated workflow runs at last check. The current working tree now contains the migration, its focused contract test, and updated status/handoff; rerun local tests, Ruff, diff checks, Alembic heads, then commit/push and wait for exact-head CI. PR remains Draft.


## Default Vendor bootstrap + public signup routing — 2026-11-03 (implementation in progress)

- Exact-head CI for 12784da030af6c7dcf9ea3e9b8380958433b4785 completed **24/24 workflows successfully, zero failures** (CI #4290 plus all associated E2E/security workflows). This green result applies to that commit, not yet to the current uncommitted signup/bootstrap changes.
- Public registration now resolves DEFAULT_VENDOR_TENANT_SLUG to exactly one active root Vendor. Missing configuration or no eligible root Vendor returns HTTP 503 (fail-closed); the public endpoint never creates a Vendor.
- Registration creates a customer child tenant under that Vendor, inherits vendor_release_tag and delivery_revision, records control_plane_parent, and creates a non-superuser/non-platform-admin Customer Admin with the normal Core grants plus the Customer edition permission set. Audit events are recorded in both the Customer and Vendor ledger scopes.
- Added operator-only backend/scripts/bootstrap_default_vendor.py. It requires the configured Vendor slug plus DEFAULT_VENDOR_BOOTSTRAP_ADMIN_EMAIL; a password of at least 12 characters and tenant name are required only when creating missing records. A PostgreSQL advisory transaction lock serializes reruns. It refuses a conflicting slug, non-root/non-Vendor tenant, inactive Vendor, or inactive/privileged existing Admin. It adds the seven explicit Vendor action grants without removing custom grants and never sets is_superuser or is_platform_admin.
- Added unit coverage for missing/missing-or-ambiguous default Vendor, release/parent inheritance, unique-slug race handling and bootstrap fail-closed behavior. Added isolated PostgreSQL acceptance coverage for bootstrap idempotency/least privilege and extended the PostgreSQL live API test to verify public signup creates a Customer under the configured root Vendor and seeds Customer edition grants.
- Local validation so far: **27 focused tests passed**; Ruff passed on all changed Python files; git diff --check passed; Python compile check passed. The new PostgreSQL acceptance tests have not been run locally because SUPPORT_TEST_DATABASE_URL is not configured; they fail closed and no Staging/Production database was substituted.
- Current code/docs changes are still uncommitted at this checkpoint. Next: run the full focused suite again, inspect the bootstrap script and test fixture carefully, commit/push, then wait for exact-head CI including the two isolated PostgreSQL acceptance tests. Do not claim this implementation CI-green until the new commit's full workflow matrix completes.
- PR #1353 remains Draft. No migration was applied, no Vendor was provisioned, no Staging/Production settings or databases were changed, and no merge/deployment occurred.


## CI follow-up — seed disposable Vendor fixtures and preserve audit immutability (2026-11-03)

- Exact-head CI #4291 on 628e96a0 exposed seven E2E workflows that still expected public signup to create a standalone tenant. The API correctly failed closed with HTTP 503 because those disposable stacks had not configured/bootstrapped a default Vendor. Corrected the workflow setup for Public Widget, W21, W16 Skill API, W16 Third-Party Publishing, W3, Runtime Isolation/RBAC and Workforce Semantic: each now configures a test-only default Vendor and invokes the operator bootstrap against its isolated database after migrations. Docker Compose passes the configured slug and test bootstrap values only into the E2E API service; production compose passes only the configured slug, with bootstrap credentials supplied only to the one-off ephemeral validation command.
- The same CI backend run found the new bootstrap PostgreSQL acceptance test attempted to delete its audit rows during cleanup. PostgreSQL correctly rejected that operation because the audit ledger is immutable. The test now retains its random-slug bootstrap evidence and relies on the disposable CI support database being reset per workflow run; production ledger immutability is unchanged.
- Production Infrastructure Validation's dependency check was a single immediate probe after intentional PostgreSQL/Redis restarts and returned HTTP 503 during reconnection. Changed it to a bounded retry loop with API/PostgreSQL/Redis diagnostics on exhaustion; no health gate was weakened.
- Local validation after these corrections: 27 focused unit/contract tests passed; Ruff and Python compile checks passed; all 69 workflow/compose YAML files parsed; docker compose config passed; bash -n passed for the infrastructure validation script; git diff --check passed. The PostgreSQL bootstrap/live API acceptance tests remain unrun locally because SUPPORT_TEST_DATABASE_URL is not configured. They are wired into CI's disposable PostgreSQL database. No Staging/Production database was used.
- These CI setup and audit-test corrections are a follow-up commit still awaiting push/exact-head CI at this checkpoint. Previous exact-head 24/24 success applies to 12784da0 only; CI #4291 on 628e96a0 is not green. Keep PR #1353 Draft and unmerged until a fresh exact-head matrix is fully green.


## Follow-up pushed — CI fixture provisioning corrections (2026-11-03)

- Follow-up commit `cd4ef18a62a923b71a5e458a56511b77c7c9af47` is pushed to the PR branch. It bootstraps a disposable root Vendor in each affected E2E stack (Public Widget, W21, W16 Skill API, W16 publishing, W3, Runtime Isolation/RBAC and Workforce Semantic) after migrations, using a test-only slug and Admin credentials. This preserves the production rule that public signup never creates a Vendor or silently falls back to a root Customer.
- The bootstrap PostgreSQL acceptance test no longer attempts to delete immutable audit-ledger rows. It asserts that creation, Admin assignment and permission-grant events are each recorded exactly once across two idempotent bootstrap invocations. Random fixture identities remain in the disposable support database, which is reset per workflow run.
- Production Infrastructure Validation now retries the dependency-readiness probe for a bounded 60 seconds after deliberate database/Redis restarts and prints API/PostgreSQL/Redis logs if readiness never returns.
- CI #4291 on prior head `628e96a0` completed with 9 failures: seven E2E stacks lacked the required default Vendor fixture; one bootstrap PostgreSQL test attempted forbidden audit-ledger deletion; one production infrastructure check hit a transient 503 immediately after dependency restarts. These are the specific corrections included in `cd4ef18a`; the new exact-head workflow matrix is pending and no green result is claimed yet.
- Local checks after the corrections: 27 focused unit/contract tests passed, Ruff passed, compileall passed, all 69 workflow/compose YAML files parsed, docker compose config passed, `bash -n` passed, and `git diff --check` passed. Dedicated local PostgreSQL acceptance remains blocked by missing `SUPPORT_TEST_DATABASE_URL`; no shared database was used.
- PR #1353 remains Draft and unmerged. Staging/Production databases and settings were not changed.


### Additional E2E registration consumers covered

- A repository-wide audit found additional real-stack scripts that call the public registration endpoint. Added the same isolated Vendor bootstrap setup to W1 Control Plane, W17 Career Reputation, W18 Meeting Rooms, W20 Employee Marketplace, and the W16 Cross-Tenant Skill Purchase API workflow. These are test-only bootstrap fixtures; the API's fail-closed behavior remains unchanged.
- The next exact-head CI matrix must verify these additional workflows as well as the seven fixes above. No claim is made that the new workflow setup has passed until that matrix completes.


### Bootstrap script import-path correction — 2026-11-03

- Exact-head CI #4293 found W21's standalone bootstrap invocation could not import the backend app package because Python set sys.path to the script directory. Added an explicit backend-root path derived from the script's own file location before application imports; this is independent of the caller's working directory and also hardens compose-based E2E invocations.
- Local direct invocation from repository root now imports successfully and stops at the intended fail-closed guard when DEFAULT_VENDOR_TENANT_SLUG is unset; it does not connect to or mutate a database. Ruff passed, compileall passed, and the 27 focused unit/contract tests passed again. Exact-head CI after this path correction is pending.


### Customer marketplace purchase grant correction — 2026-11-03

- W16 Cross-Tenant Purchase API reached the actual purchase endpoint after successful Vendor bootstrap and public signup, then received HTTP 403 because the Customer edition Admin grant set did not include the explicit skill_marketplace.purchase permission. The endpoint's permission gate is correct; the Customer role's default grant set was incomplete for the documented purchase flow.
- Added skill_marketplace.purchase only to CUSTOMER_PERMISSIONS and extended both the focused permission contract and PostgreSQL live-registration assertions. Vendor/Reseller grants and API-key scopes were not broadened.
- Local validation: **28 focused tests passed**, Ruff passed, compileall passed. Dedicated PostgreSQL acceptance remains delegated to CI because SUPPORT_TEST_DATABASE_URL is not configured locally. New exact-head CI is pending after push.


### Manual certification workflow parity

- Added the same disposable Vendor bootstrap to the manually dispatched Production Certification and Release Certification workflows after their isolated application-stack migrations. Their product gates exercise multiple /auth/register consumers; these workflows now receive a test-only Vendor fixture and retain the fail-closed signup contract. These workflows are certification-only and were not run as part of the current PR matrix; no real production or staging environment was targeted.


### Celery/Kombu/Redis worker compatibility correction — 2026-11-03

- Public Widget E2E now completes migration, Vendor bootstrap and API fixture provisioning, then its Celery worker fails before consuming tasks. The exact runtime error is Kombu Redis transport requiring redis-py >=6.1.0 while the installed dependency set supplies redis-py 5.2.0. This is a dependency compatibility issue, not an API signup or authorization failure.
- Aligned all backend dependency declarations: Celery is bounded below 5.6, Kombu is bounded below 5.6 and pinned to 5.5.4 in the direct lock, and redis-py remains on the compatible 5.x line. This avoids Kombu 5.6's newer Redis transport requirement without broadening or changing the application runtime contract.
- The same direct lock is used by Docker-based workers, so this correction covers the other E2E worker stacks as well as the standalone Public Widget worker. The new CI matrix must confirm clean worker startup and task execution before this is considered resolved.


### Marketplace purchase permission parity across new Admin roles

- The historical W16 migration grants skill_marketplace.purchase to existing Admin roles across editions. To keep newly provisioned roles consistent with that migration, the explicit permission is now included in the common tenant Admin permission tuple, Reseller and Customer edition permission sets, and the operator-created Vendor bootstrap Admin set. It remains a tenant-local role grant; no superuser or API-key-scope bypass was introduced.
- Local validation after the parity change: **28 focused tests passed**, Ruff passed and compileall passed. The exact-head PostgreSQL API/bootstrap tests remain CI-gated because the local dedicated SUPPORT_TEST_DATABASE_URL is absent.


### Employee Marketplace Admin permission parity — 2026-11-03

- W20's 403 was at POST /employee-marketplace/packages and required employee_marketplace.publish. The corresponding W20 migration, like the W16 marketplace migrations, grants explicit marketplace actions to existing Admin roles. Newly provisioned edition Admin roles must receive the equivalent grants through their role permission sets.
- Added marketplace.install and employee_marketplace.publish/install/revoke to the common Admin, Reseller and Customer permission sets. The operator-created Vendor bootstrap Admin also receives these specific marketplace actions alongside its Vendor control-plane grants. The grants remain tenant-local and are not superuser/API-key bypasses.
- Extended the public-signup permission contract, live PostgreSQL registration assertions, and bootstrap least-privilege acceptance assertions. Local focused suite and exact-head CI must be rerun after this change; no pass is claimed yet.

## Security and final code review follow-up — 2026-11-03

- Historical dependency findings were reconciled: sharp is now 0.35.5 in both main and this branch; the former sharp 0.35.3 tracker is closed. GitHub withdrew the braces GHSA/CVE on 2026-10-23; no speculative override, downgrade, suppression, or major framework migration was made.
- Fresh npm registry audit found follow-redirects 1.16.1 as a new high-severity production dependency finding (GHSA-mrwp-f3q8-3g9p / CVE-2026-116689; patched in 1.16.2). Updated only frontend/package-lock.json to 1.16.2, preserving package.json and the rest of the lock metadata. The production-only audit is now clean (0 vulnerabilities). Full audit has 16 moderate records, all in the development ESLint/minimatch toolchain; the audit's proposed broad remediation is a breaking major change, so it was not forced.
- Security review found the legacy Vendor permission backfill granted permissions to a shared Role if any member was platform-admin. Since every member inherits Role grants, this could overgrant ordinary users. Migration now excludes a Role if any same-tenant member is not platform-admin. Added SQL-contract assertions. Focused migration test: 2 passed; Ruff and git diff --check passed.
- Exact-head CI for `2746e7fd30abd98b628644444e17f19871d7e8c7` completed **41/41 workflows successfully, zero failures**. The backend suite passed on isolated CI PostgreSQL services: 1,854 passed, 1 deselected, 20 warnings; includes Vendor bootstrap and permission migration coverage. Frontend browser regressions, Security/Privacy, DAST, W20 real-stack and all other gates are green. Frontend local checks: npm ci passed, 145 contract/governance assertions passed, ESLint exit 0 with five existing warnings, Next.js 16.4.2 build passed (82 static pages). Production-only npm audit is clean (0 vulnerabilities); full audit retains 16 moderate records from the development ESLint/minimatch graph. Installed tree confirms axios 1.20.0 → follow-redirects 1.16.2.
- PR #1353 remains Draft and unmerged. No staging/production databases, configuration, or deployments were touched.

## 2026-11-03 - PR #1353 merge and lifecycle/RBAC handoff

- PR #1353 merged to main at 817a196fdc6c733ae3da29885c652b6e12508d74. Latest PR-head CI completed 39/39 successfully; isolated PostgreSQL backend suite: 1,854 passed, 1 deselected. The merge includes follow-redirects 1.16.2.
- Active worktree: feature/multi-vendor-account-lifecycle-20261103, based on merged main. Primary checkout and Staging/Production were not modified.
- Lifecycle gap: child provisioning accepts an initial admin password and activates the user immediately; public registration activates the Customer user and creates an automatic 14-day trialing subscription. Policy requires approved payment or an explicitly granted Demo entitlement before membership activation. Trialing is neither proof of payment nor Demo authorization.
- RBAC hardening commit 18b5998b9f577517f965bf4a32b65bac43a855f0 removes the is_superuser bypass from tenant-admin routes and role delegation. A superuser must have a tenant-local Admin/Owner/Tenant_Admin role and may delegate only permissions explicitly held in that tenant. Local validation: 65 focused tests passed; Ruff and git diff --check passed. PR #1354 remains Draft pending exact-head CI.
- Next: implement provider-authoritative payment approval and explicit audited Demo entitlement; implement tenant-bound, hashed, single-use invitation tokens with expiry; then gate child provisioning and public signup on entitlement and invitation. Add PostgreSQL race, expiry, replay and cross-tenant tests. No migration has been applied to a persistent shared database.
- GitHub Issue #1350 checkpoint comment ID: 6608629214. No Staging/Production resources were changed.

## Edition portal administrator boundary follow-up

- A second legacy `is_superuser` bypass was found in `edition_service.require_edition`: it allowed a superuser without a tenant-local Admin/Owner/Tenant_Admin role to enter the matching edition portal. This is distinct from the cross-edition kind check.
- Removed that bypass. Edition portal access now requires both the correct tenant kind and a tenant-local administrator role for every identity, including superusers. Added a regression test covering all three editions.
- Combined focused validation now passes 45 tests across portal access, tenant-admin role boundaries and edition action permissions; Ruff and `git diff --check` pass.

## Core RBAC and worker permission ceiling follow-up

- Extended the no-superuser-bypass correction to the shared `has_permission` dependency, API-key scope delegation, `/auth/me` permission projection, and worker-side Run tool authorization.
- A superuser with no explicit tenant role now has no ordinary operational permissions. Worker tool permissions are resolved only from roles attached to the Run tenant. API keys cannot receive ordinary or edition scopes beyond the creator's explicit tenant-local authority; superusers must provide explicit scopes and do not receive an authority exemption.
- Added regression coverage for superuser-without-grants, API-key over-delegation, and worker tool permissions. Combined focused suite: 65 passed; Ruff and `git diff --check` passed.

## Repository-wide superuser bypass audit

- A complete `backend/app` search found remaining authorization shortcuts outside the edition control plane: the shared `has_permission` dependency, API-key scope delegation, `/auth/me` wildcard permission projection, and worker-side Run tool permission resolution.
- Removed those shortcuts. `is_superuser` no longer grants operational permissions, broad API-key delegation, wildcard permissions in `/auth/me`, or wildcard worker tool access. Explicit tenant-local role grants and API-key route scopes remain the authority sources.
- The only remaining application use of `is_superuser` is requiring explicit scopes when a superuser creates an API key; it is not an authorization grant. Model field and user constructors remain for compatibility, but no longer elevate tenant operations.
- Focused regression suite: 65 passed; Ruff and `git diff --check` passed. Documentation truth validator passed.

## Public signup account-kind slice — 2026-11-05

- New isolated branch `feature/public-signup-pending-20261105` starts from exact `main` SHA `c98e4c0d43a0a53e630945d8448da60231ca87ed`.
- Public registration now accepts only `customer` or `reseller` (`customer` remains the backwards-compatible default); Vendor creation remains prohibited by schema validation.
- Both public account kinds are created as direct children of the configured active root Vendor, inherit its release identity, and require an explicit paid/Demo entitlement before workspace APIs are accessible.
- Reseller signup receives the tenant-local Reseller permission set, not Vendor permissions. Audit action and metadata record the selected child kind.
- Registration UI exposes Customer/Reseller selection and explicitly states Vendor accounts are provisioned separately.
- Added schema tests and expanded the PostgreSQL-backed edition API acceptance to cover public Reseller signup, default-Vendor ownership, pending billing/access, and Reseller-only permissions.
- Local checks: 26 focused backend unit/contract tests passed; Ruff, Python compile and `git diff --check` passed.
- Not run locally: PostgreSQL HTTP integration test (no approved `SUPPORT_TEST_DATABASE_URL` is configured) and frontend lint/build (frontend `node_modules` is absent; `eslint` is unavailable). Exact-head CI is required before merge.
- No DB migration, staging/production change, payment activation, or account mutation was performed.

## Tenant-admin last-active-administrator protection � 2026-11-11

- Found a missing defensive guard in `POST /api/v1/tenant-admin/users/{user_id}/status`: unlike the reseller-managed Customer user route, the direct tenant-admin route did not explicitly reject deactivation when the target was the last active tenant-local Admin/Owner/Tenant_Admin.
- Added tenant-row `FOR UPDATE` serialization before locking the target user and counting active tenant-local administrator memberships. The endpoint now returns HTTP 409 if the database state contains only one active administrator. The existing self-deactivation prohibition remains in force.
- Added unit regressions for last-admin rejection and the two-admin allowed-deactivation case, plus a PostgreSQL 16 + authenticated FastAPI ASGI acceptance test exercising concurrent deactivation requests and self-deactivation.
- Validation on the disposable local `support_test` PostgreSQL database (port 15433; tmpfs; migrated to `w33_tenant_action_grants`): focused suite **3 passed**; concurrent HTTP acceptance repeated **3/3 passed**. Ruff, compileall and `git diff --check` passed. Python 3.10 required the repository test shim `enum.StrEnum = enum.Enum` for the current dependency imports.
- No persistent database, Staging, Production, payment, deployment, or migration target was touched. This is still an uncommitted local change in the PR #1434 worktree pending final diff review and push.
