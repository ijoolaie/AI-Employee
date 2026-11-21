

## Reseller-to-Customer file lifecycle follow-up - 2026-11-19

- Expanded the live delegated Portal scenario for a Reseller acting in its direct Customer context: upload, tenant-owned metadata read, streamed download/content verification, soft-delete, post-delete 404, and `file.uploaded`/`file.deleted` audit attribution to the Reseller actor under the effective Customer tenant.
- Added sibling-Reseller Customer file get/download/delete denial (404). The file storage backend is in-memory for this scenario; the uploaded object is explicitly deleted after assertions and the backend is discarded with the test.
- Focused PostgreSQL live API scenario: **1 passed in 30.68s** on disposable PostgreSQL 16 tmpfs. Container stopped and auto-removed.



## User lifecycle follow-up - 2026-11-19 (accepted invitation and status)

- Expanded the Reseller-to-direct-Customer live API scenario beyond invite/revoke: a second invitation is accepted through `/auth/invitations/accept`, the user appears in the tenant-scoped list with the fixed `Reseller Managed Member` role, status is deactivated/reactivated, and both Customer-tenant and Reseller-tenant audit rows are verified with the Reseller actor and target Customer metadata.
- Focused PostgreSQL live API test: **1 passed in 31.43s** on a dedicated tmpfs PostgreSQL 16 database; DB-free `test_reseller_customer_users.py`: **5 passed in 0.70s**; all invitation/user/role/audit fixtures are removed by the existing scenario cleanup. Container stopped and auto-removed.
- Source inventory found only `reseller_customer_users.py`, which exposes Reseller -> direct Customer list/invite/revoke/status. No Vendor -> direct Customer or Vendor -> direct Reseller child-user management routes exist in the current API. Do not invent parent-admin endpoints: whether Vendor may manage child-tenant users or must act through a child-admin identity is a product/security contract decision.

## Latest verified checkpoint - 2026-11-19 (Outbox, Test Center and delegated reporting)

- PostgreSQL acceptance ran only on a disposable PostgreSQL 16 container with tmpfs storage, localhost-only port 15435 and database `ai_employee_lifecycle_test`. The container was stopped and auto-removed; no Staging/Production database was used.
- Outbox: **8 passed**. Coverage includes Email/WhatsApp denial before provider I/O for an active but commercially unentitled Customer, tenant suspension fencing, provider-window lifecycle locking, and a two-session subscription-revocation race proving the Subscription row lock remains held until the provider transaction commits. Tests remove their Tenant, Subscription, License, Plan and Outbox fixtures.
- Test Center: **5 passed**. The suspended-tenant delayed-worker test now seeds a valid active Subscription and CommercialLicense so it reaches the tenant lifecycle guard; fixture cleanup removes related commercial records.
- Portal/reporting: **21 passed** (20 route-policy cases plus the live PostgreSQL portal scenario). The live scenario verifies delegated `/usage/optimization` and `/usage/cost-forecast` HTTP 200 and sibling invoice PDF export denial. Two read-only usage routes are now exact-path exceptions to the portal denylist; the rest of `/usage` remains denied. The Vendor reader fixture has the invoice-export permission needed to exercise resource-scope denial.
- Test contract corrections: sibling Customer invitation is intentionally anti-enumerating (404); reserved `.test` email domains were replaced with `example.com` in the live test fixture.
- Ruff lint passed for the changed Python files. Full Ruff formatting check still reports pre-existing style drift in two long PostgreSQL integration test files; no broad reformat was applied. Full CI has not been run.
- No commit, push, merge, deployment or Issue #1350 closure. Issue #1350 remains OPEN.

## Latest verified checkpoint - 2026-11-19 (Lifecycle concurrency and audit)

- Approved PostgreSQL policy: tests may run without per-run approval only against a dedicated ephemeral database, isolated from Staging/Production and with no persistent data mutation. Persistent DB migrations/mutations and external environment tests remain gated.
- PostgreSQL 16 ran in an auto-removed Docker container with its data directory on tmpfs, bound to localhost port 15435 and database `ai_employee_lifecycle_test`. Alembic was applied only to that ephemeral database.
- Added `test_child_deprovision_serializes_before_parent_deprovision` to `backend/tests/test_tenant_lifecycle_concurrency.py`. Two independent sessions prove that a child deprovision holding the parent lock commits before a concurrent parent deprovision; final parent and child states are deprovisioned. Its URL guard requires the dedicated database and port.
- Executed the focused concurrency file and live Lifecycle API scenario together: **5 passed in 76.36s**. API checks align with authorization-first 403 behavior for wrong-kind/sibling/parent-unavailable contexts and 409 for terminal child reactivation.
- Runtime execution exposed and fixed a real Audit metadata defect: `edition_service.record_audit` passed `metadata` instead of the mapped `AuditLog.metadata_` field. Live API assertions now verify parent tenant, actor, child identity/kind and previous/target status metadata on all three deprovision edges.
- The concurrency and live API tests clean up their generated records. Ruff check passed for all three changed Python files; the new concurrency test is Ruff-formatted. Full CI was not run.
- No commit, push, merge, deployment or Issue #1350 closure. Issue #1350 remains OPEN.
# AI-Employee Master Handoff ╬ô├ç├╢ 2026-11-18

Repository: ijoolaie/AI-Employee
Active track: Multi-Vendor tenant ownership, delegated authorization and portal acceptance
Tracker: https://github.com/ijoolaie/AI-Employee/issues/1350
Worktree: .worktrees/AI-Employee-attachment-race-check/.worktrees/multi-vendor-next-audit-20261108
Branch: test/knowledge-revoked-portal-context-20261108
HEAD: fed62f56a75dd0f6de09c41e14a00506593d14c5

## 1. Project decision and scope

The only active engineering path for this continuation is completion of the Multi-Vendor acceptance track tracked by Issue #1350. Do not start unrelated product, World Mode, release, commercial, or infrastructure work while this track is active.

The accepted architecture remains:
- Vendor, Reseller and Customer ownership boundaries are explicit.
- Delegated portal access is user-bound, scoped, revocable and revalidated.
- Resellers cannot access sibling Resellers or their Customers.
- Every resource/action and asynchronous execution path must enforce the effective tenant and actor authority.
- Issue #1350 remains open until the acceptance matrix and evidence review are complete.

## 2. Git and PR facts observed on 2026-11-18

- The active local branch and PR #1434 head match exactly at fed62f56a75dd0f6de09c41e14a00506593d14c5.
- PR #1434 is OPEN, not Draft, base main at d943ec2cffd75ea88daebdf02c7b6df413d3f2f6, and GitHub reports merge state CLEAN.
- On the exact PR head, 20 GitHub Actions check suites and one GitHub Advanced Security suite are completed successfully. Freebuff Web suite 117539141336 is still queued; the commit combined status is pending. Required CodeQL checks are green. Do not treat queued or missing checks as success and do not merge.
- PR #1433, the 2026-11-08 master handoff document, remains OPEN and unmerged at 6c4dfe33fb84077553dc7b777379d9303aca7090. Its document is not yet the merged repository truth.
- PR #1447 is Draft and stacked on PR #1434; it remains separate from #1434 and must not be folded into it.
- PR #1452 is a separate open, non-Draft PR. Do not merge it as part of this workstream.
- Issue #1350's latest recorded synchronization refresh (2026-11-17) says the 13 tracked PRs #1428, #1431╬ô├ç├┤#1434 and #1447╬ô├ç├┤#1454 remain open; visible Actions/CodeQL checks passed on their recorded exact heads, while Freebuff Web remained queued on each. Drafts were #1447╬ô├ç├┤#1451, #1453 and #1454. Refresh exact heads/checks before any later merge decision.

## 3. Local worktree preservation boundary

- The worktree has 76 changed paths after this documentation refresh: 57 tracked modifications and 19 untracked files. Before the documentation refresh, the implementation worktree contained 71 paths (53 tracked and 18 untracked). No staged changes were present at inspection.
- These local edits are not part of PR #1434's committed head. PR #1434 describes a test-only acceptance change; the current uncommitted work spans application services, workers, migrations, models and tests.
- Preserve all 71 paths. Do not reset, clean, stash, restore, delete, stage, commit, push, merge, rebase or move them as part of this checkpoint.
- Do not add the broader local implementation to PR #1434. First classify it against the ordered acceptance gaps and keep any later change in the smallest reviewable scope.

## 4. Acceptance roadmap ╬ô├ç├╢ source-backed order

The current source-backed gap register is docs/current/MULTI_VENDOR_ACCEPTANCE_MATRIX_AUDIT_2026-11-08.md; the tracker is Issue #1350. The matrix remains incomplete.

1. Current gate ╬ô├ç├╢ reconcile local changes with the acceptance matrix. Classify the existing Outbox/worker, authorization, Run/Workflow recovery and AssignmentCommand changes against a specific open gap. Do not create another implementation slice until this classification is documented. Preserve unrelated changes.
2. Notifications and Outbox tenant isolation. Close only the remaining evidence gaps for recipient resolution, dispatch, retry/dead-letter ownership, delegated context and revocation. Reuse existing implementation/tests where they already prove the contract; add only the smallest missing assertion.
3. Worker enqueue and execution-time authorization. Verify tenant provenance, forged metadata rejection, delayed work and authority revocation at execution. Avoid duplicate tests for already-proven boundaries.
4. Entitlement lifecycle. Cover expiry/suspension and already-issued portal grants, plus in-flight/background work where the matrix still marks it missing. Keep request-time denial distinct from cancellation of work already executing.
5. Remaining Actor Γö£├╣ Resource Γö£├╣ Action matrix. Select the next concrete uncovered resource/action/topology from the audit; do not expand into a broad test sweep.
6. Cache, reports and exports. Continue only where the audit still says partial/not evidenced, including tenant-scoped server cache invalidation and revoked-context artifact access.
7. Legacy permission migration rehearsal. Remains a separate review gate; no staging/production backfill or persistent migration without explicit approval.
8. Human portal UX acceptance. Remains blocked pending separate explicit approval for visual/browser acceptance.
9. Realtime transport. The audit identifies WebSocket/SSE as not implemented. This is an architecture decision gate, not an implementation task in this continuation. Do not add WebSocket/SSE without a separate approved architecture decision.

## 5. Work and verification policy

- Before each implementation step, update this handoff, CURRENT_STATUS.md, CURRENT_PRIORITIES.md, the acceptance audit and Issue #1350 as applicable. Record exact SHA, scope, evidence and remaining gap.
- Execute only the focused verification required by the selected gap. No broad regression sweep, repeated test matrix or alternate implementation experiments unless a concrete failure requires it.
- PostgreSQL tests are permitted without another per-run approval only on a dedicated ephemeral database, isolated from Staging/Production and with automatic fixture/container cleanup.
- No migration against persistent databases, Staging or Production. Do not stop or mutate Staging PostgreSQL.
- No commit, push, PR merge, deploy, release promotion or data mutation without separate explicit authorization.
- Do not enter or test the game/World environment. Do not perform visual Desktop/Mobile acceptance without separate approval.

## 6. Definition of the next step

Next step is documentation-led classification of the existing 71 local changes against the acceptance matrix, beginning with the already-touched Notifications/Outbox and worker-ownership gaps. Produce one bounded scope decision and update the tracker before further code edits. If a change does not close a documented gap, it is out of scope for this continuation.

## 7. Evidence limits

This checkpoint is based on local Git metadata, local documentation, GitHub PR/check-suite data and the latest Issue #1350 comments available at inspection. It is not a merge approval, production certification, deployment claim, database acceptance result or customer sign-off.

## Scope reconciliation of pre-existing implementation ╬ô├ç├╢ 2026-11-18

The 71 pre-documentation implementation paths were reviewed against the acceptance matrix. They are classified by acceptance purpose, not treated as one feature branch or as evidence that every matrix row is complete.

| Local change group | Acceptance relationship | Decision |
|---|---|---|
| customer_channel_service.py handoff behavior (existing source/test baseline), outbox_service.py, outbox_worker.py, operations.py, email/WhatsApp worker contracts | Notifications/outbox tenant ownership, dedupe, replay, delivery uncertainty, recipient ownership and revocation | In-scope. Existing implementation already provides tenant-keyed dedupe, tenant-specific handoff destination lookup, durable tenant row binding, worker authority checks, and provider uncertainty handling. Current local additions improve claim lease timing, dead-letter replay budget/state reset, replay row lock/tenant scope, and assignment dispatch binding. |
| assignment_command migration/model/service/worker plus related tests | Background job tenant provenance, idempotent delivery and worker execution fencing | Conditionally in-scope. These changes establish a tenant-bound asynchronous command path; they do not by themselves close the complete Celery inventory or prove portal-grant revocation for every worker. |
| agent_policy_engine, agent_delegation_service, agent_run_governance_bootstrap, run_execution_fence, run_worker, run_recovery_worker, workflow_service, workflow_trigger_worker, workflow_approvals, and their tests | Delegated authority, worker execution-time revalidation, lease fencing, approval/timeout/cancellation consistency | In-scope cross-cutting evidence. Keep only where a test/source contract maps to a matrix gap; do not expand into unrelated Run/Workflow hardening. |
| billing_service, edition_lifecycle_service, quota/subscription/tenant lifecycle tests | Entitlement expiry/suspension, already-issued grants and in-flight execution | In-scope. This is the next acceptance domain after notifications/worker evidence is reconciled. |
| tenant_admin.py, tenant_invitation_service.py, tenant_access_service.py, workforce/agent templates and related tests | Tenant user lifecycle, role/authority ceilings, tenant boundary enforcement | Partially in-scope. Retain only the direct mapping to a remaining Issue #1350 acceptance row; unrelated workforce/template behavior is not a reason to broaden this track. |
| team_execution.py, unified_execution.py, agent_rollback.py, agent_workforce_manager.py, agent_workforce_replacement_service.py and their tests | General execution/governance behavior | Not independently accepted by the Multi-Vendor matrix. Preserve existing edits, but do not add further work here unless a specific actor/resource/action gap is documented. |
| Four documentation files plus the new 2026-11-18 handoff | Current source of execution truth | In-scope governance. These define the only ordered continuation path. |

### Notification/outbox evidence reconciliation

- Recipient selection is sourced from Tenant.settings by conversation.tenant_id; the handoff enqueue stores that same tenant ID and uses a conversation-specific dedupe key.
- Existing test_customer_handoff_notification_outbox.py verifies the tenant ID, destination, message body and dedupe key at enqueue time.
- Existing test_email_outbox_crash_safety.py verifies stable delivery identity, row serialization, uncertainty fencing, configured handoff recipient, cross-tenant Agent proof rejection and delegated Agent authority revocation before SMTP.
- Existing test_whatsapp_worker.py verifies fail-closed governance proof and no retry after the provider boundary.
- Current local Outbox changes cover processing lease start time, replay retry-budget reset/terminal metadata clearing, tenant-scoped replay locking and AssignmentCommand tenant binding/ambiguous broker delivery.
- Still not fully evidenced: the concrete Tenant.settings lookup predicate itself is not directly asserted by the handoff test (the helper is mocked there); the broader notification matrix across every Vendor/Reseller/Customer topology and all delivery kinds is not complete. A focused assertion of the tenant lookup is the only code/test action in this slice. No broad notification test sweep is authorized.

### Scope boundary after reconciliation

Do not add new AssignmentCommand, Run/Workflow, workforce, template or other worker features in this slice. Preserve their existing local changes. The next bounded action is to prove that handoff recipient configuration is selected only from the conversation-owning tenant, then record the exact evidence. After that, continue to the already prioritized entitlement lifecycle gap, one concrete missing condition at a time.

## Evidence update ╬ô├ç├╢ notification recipient ownership ╬ô├ç├╢ 2026-11-18

- Added one focused test: test_handoff_notification_destination_lookup_is_scoped_to_conversation_tenant.
- The test calls the real Tenant.settings lookup, compiles the SQLAlchemy statement for PostgreSQL, and asserts the predicate targets tenants.id with the supplied conversation tenant UUID; it also verifies the configured destination returned by the lookup.
- Focused execution: 1 passed, 2 deselected. No database was used.
- This closes only the narrow recipient-lookup evidence gap. The broader Notifications/Outbox matrix remains PARTIAL because every Vendor/Reseller/Customer topology and delivery kind has not been demonstrated.
- No application behavior was changed in this slice.
- Next ordered domain: entitlement expiry/suspension for existing portal grants and already-enqueued/in-flight work. Existing tenant_access_service tests already cover expired paid periods, expired Demo grants, existing portal-grant denial after commercial access expires, and paused subscription denial; inspect these contracts and only address the remaining in-flight/background boundary.

## Next bounded acceptance gap ╬ô├ç├╢ entitlement at irreversible worker side effects ╬ô├ç├╢ 2026-11-18

Source inspection found a specific remaining gap in the Entitlement and stale-grant row: portal-context requests revalidate current commercial entitlement, and Run/Workflow admission revalidates entitlement, but the Email and WhatsApp workers currently revalidate only Tenant.status before the provider call. Their already-queued, in-flight outbox rows can therefore pass the lifecycle-status fence even after a paid period/Demo grant becomes invalid, unless the Agent-specific policy happens to reject them for another reason.

Bounded correction: reuse the existing billing execution-entitlement guard at the provider boundary, before the irreversible SMTP/WhatsApp call, while preserving the established Subscription ╬ô├Ñ├å Tenant lock order and the existing uncertain-outcome behavior. Map a deterministic inactive commercial entitlement to the existing fail-closed TenantInactiveError path so the outbox row is dead-lettered before provider I/O. No new entitlement model or migration is in scope.

Verification is limited to the new helper contract and one focused worker-path contract. PostgreSQL lock-race verification follows the approved ephemeral-database policy; do not use persistent databases.

## Evidence update ╬ô├ç├╢ commercial entitlement at outbound provider boundary ╬ô├ç├╢ 2026-11-18

- Updated assert_tenant_active_for_side_effect to invoke the existing assert_run_execution_entitlement guard before locking Tenant for the provider window. This reuses the existing Subscription ╬ô├Ñ├å Tenant admission order and does not add schema or new entitlement rules.
- ConflictError/NotFoundError from current commercial entitlement/admission are converted to TenantInactiveError. Existing Email and WhatsApp worker paths already treat TenantInactiveError as a deterministic pre-provider denial and dead-letter the row; no provider call is made.
- Preserved the pre-existing pending-public-signup invitation exclusion hunk in tenant_access_service.py while applying this change.
- Focused test: test_external_side_effect_fails_closed_when_current_entitlement_is_inactive ╬ô├ç├╢ 1 passed, 13 deselected. git diff --check passed. No PostgreSQL test or persistent DB operation.
- Acceptance status: code path now fails closed for entitlement at outbound delivery time; PostgreSQL concurrency/lock serialization still requires the authorized isolated CI evidence. This does not complete the full Entitlement or Worker matrix.
- Next: inventory the remaining Celery/async task entry points against explicit tenant provenance and execution-time authority; select only the next documented uncovered worker class.

## Worker inventory finding ╬ô├ç├╢ Test Center delayed execution ╬ô├ç├╢ 2026-11-18

The Celery inventory shows most workflow/run/outbox tasks derive tenant ownership from a durable tenant-scoped row or receive tenant_id explicitly. Test Center execute_run is a specific exception worth closing: its task accepts only run_id, then correctly binds TestDefinition.tenant_id to TestRun.tenant_id, but it does not revalidate the tenant's current active/commercial entitlement before transitioning QUEUED ╬ô├Ñ├å RUNNING. A task queued before suspension/expiry can therefore begin afterward.

Bounded correction: after resolving the TestRun and tenant-bound enabled definition, call the existing billing_service.assert_run_execution_entitlement with the TestRun's authoritative tenant_id before start_run. Do not trust caller-supplied tenant metadata, change the task signature, or alter the Test Center ownership model. Add one PostgreSQL integration assertion for suspended-tenant delayed execution; do not run it locally due the database safety boundary.

## Evidence update ╬ô├ç├╢ Test Center delayed execution ╬ô├ç├╢ 2026-11-18

- Test Center worker now calls the existing billing execution-entitlement guard using the TestRun's durable tenant_id after validating the enabled TestDefinition belongs to that same tenant and before transitioning the run to RUNNING.
- Added one PostgreSQL integration case: a queued TestRun for a suspended tenant must remain QUEUED and must not receive started_at.
- Focused Ruff check passed for the touched tenant-access, Test Center, and notification files; git diff --check passed.
- The new PostgreSQL integration case was intentionally not run locally. It must run in the authorized isolated CI database path. No DB migration or persistent data operation occurred.
- Worker inventory status: explicit tenant arguments or durable row-derived tenant ownership were found for the Celery tasks reviewed; event/schedule/Run/Workflow tasks already use tenant-scoped durable rows and existing admission/dispatch guards. Test Center delayed execution was the identified missing active/commercial admission check and is now corrected locally. The full worker matrix still needs exact-head CI evidence.
- Next: continue with the source-backed Cache isolation and Reports/Exports gaps; do not expand into unrelated workforce/template task behavior.

## Cache isolation source verification ╬ô├ç├╢ 2026-11-18

A targeted backend source inventory found no tenant-scoped server response/data cache implementation, cache decorator, cachetools/aiocache/fastapi-cache integration, or Redis GET/SET response cache. Current Redis usage is for IP-bucket rate limiting, tenant resource concurrency leases and tenant-fair scheduling; these are coordination/rate-limit structures, not cached tenant response data. Frontend QueryClient identity clearing is already evidenced by #1413╬ô├ç├┤#1415.

Decision: do not invent a cache invalidation subsystem or add cache tests for a cache that does not exist. Keep a release guard: if server response/data caching is introduced, keys must include actor/effective tenant/context and invalidation must cover portal switch, grant revocation, role change and account switch. For the current source baseline, the backend cache-isolation item is NOT APPLICABLE (no server data cache found); frontend identity-transition coverage remains covered by existing PR evidence. Move to the remaining report/export artifact topology gaps.

## Report/export matrix refinement ╬ô├ç├╢ 2026-11-18

Source review of the existing portal live-API acceptance test confirms meaningful evidence already exists for:
- Vendor ╬ô├Ñ├å Reseller context: tenant-scoped usage summary, invoice list/detail/summary, Test Center verification record and artifacts, operations metrics/dead letters/replay, privacy export, and report artifacts saved as tenant-owned FileObjects and downloaded through the Files API.
- Reseller ╬ô├Ñ├å Customer context: invoice list/detail/PDF export and download, privacy export, report artifact ownership/download, run artifact list/download, and denial after grant revocation.
- Sibling/cross-Vendor negative cases: invoice detail, Test Center verification, operations/dead-letter replay, privacy exports, report source-file access and file/artifact retrieval.

One concrete missing assertion in the Reseller ╬ô├Ñ├å Customer path: a sibling Customer invoice PDF export is not explicitly denied (sibling invoice detail is denied; the export route is separately exercised for the owned Customer and after grant revocation). Add that one negative action assertion only. Do not duplicate the existing report/usage/operations coverage or expand into another broad live API test.

## Evidence update ╬ô├ç├╢ sibling invoice PDF export denial ╬ô├ç├╢ 2026-11-18

- Added one negative assertion to the existing PostgreSQL portal acceptance scenario: a Reseller-to-Customer portal context cannot export a sibling Customer invoice PDF (expected 404), complementing the existing sibling invoice detail denial.
- Focused Ruff check passed for the modified portal acceptance test and the recently changed entitlement worker/service files; git diff --check passed.
- PostgreSQL integration scenario intentionally not run locally. Exact-head isolated CI is required to convert this source/test change into executed acceptance evidence.
- No production or persistent database was accessed.

## Knowledge search/indexing source reconciliation - 2026-11-18

Existing portal live-API acceptance covers direct Customer and Vendor-to-Reseller contexts: tenant-owned indexing, sibling file rejection, search results excluding sibling/foreign tenant markers, and 403 after grant revocation. RAG search filters KnowledgeChunk, KnowledgeDocument and active FileObject by effective tenant. API supports bounded top_k (1..20), not page pagination or arbitrary filters; no result cache exists. Do not invent tests for nonexistent features. Search/index isolation is covered for the exercised contexts; the full Actor x Resource x Action matrix remains partial pending remaining hierarchy permutations and authorized CI evidence.

## Worktree status refresh - 2026-11-18

- Current local worktree: 80 changed paths, comprising 61 tracked modifications and 19 untracked files; staged diff is empty.
- Compared with the 76-path checkpoint, four additional tracked paths are now changed by the focused entitlement and report/export acceptance slices. All prior paths remain preserved.
- Active branch remains test/knowledge-revoked-portal-context-20261108 at fed62f56a75dd0f6de09c41e14a00506593d14c5. No commit, push, merge, deploy or database mutation.
- The local code/test changes remain unpushed and are not included in PR #1434. Do not merge this broader worktree into its test-only scope.

## Next actor/resource/action gap ╬ô├ç├╢ Reseller-managed Customer users ╬ô├ç├╢ 2026-11-18

The tenant user lifecycle source review found a specific acceptance gap: reseller_customer_users.py exposes direct-Customer user list/invite/revoke/status operations with direct-child checks, a fixed least-privilege Customer Member role, accepted-invitation activation and audit attribution. Unit tests cover direct-child/inactive-child boundaries and the shared invitation service covers token hashing, acceptance, replay/revoke/expiry. The existing portal live-API matrix does not execute these routes with a real Reseller actor against its own Customer or a sibling Reseller's Customer.

Bounded acceptance addition: in the existing portal live-API scenario, grant the Reseller fixture only the required reseller.customer.manage action, invite a user into its direct Customer, verify a request against a sibling Reseller's Customer is denied, and revoke the owned invitation. Reuse the existing fixture and invitation service; no new service behavior or broad test suite.

## Reseller Customer user lifecycle evidence - 2026-11-18

Added a live portal acceptance scenario for Reseller-owned Customer user management: invite/revoke in its direct Customer and deny invitation into a sibling Reseller's Customer. Ruff and diff check passed; PostgreSQL scenario not run locally. Isolated CI evidence is pending.

## Extension of the same user-lifecycle acceptance case ╬ô├ç├╢ audit attribution

Extend the existing Reseller Customer invitation scenario (not a separate test) to verify the created/revoked audit rows retain the Reseller actor tenant and actor user while recording the target Customer tenant in metadata. This is the smallest evidence addition for the audit-attribution row; no general audit export/filter suite is added here.

## Scope clarification - realtime is not an Issue #1350 blocker

Issue #1350's approved scope explicitly names APIs, search, reports, files, exports, background jobs and dashboards, but does not require WebSocket/SSE. Realtime remains a separate product/architecture follow-on and must not be implemented in this continuation. It does not block Issue #1350 acceptance unless the product owner formally extends the approved scope.

## Current execution gate - 2026-11-18

The Reseller-managed Customer user live-API scenario now includes invite, revoke, sibling-Reseller denial and actor/target audit metadata assertions. Ruff and diff check passed; it remains an unexecuted PostgreSQL acceptance scenario until authorized isolated CI.

Next ordered action is not more local test expansion: reconcile and package the focused acceptance changes into a reviewable PR only after explicit publication authorization, then use exact-head CI for the new PostgreSQL cases. PR #1434 remains test-only and must not receive the broader implementation diff. Issue #1350 remains OPEN.

## Delegated usage analytics source gap closed locally - 2026-11-19

Source review confirmed /usage/optimization and /usage/cost-forecast both derive tenant context from AuditReadContext.tenant_id and call tenant-scoped services. Added HTTP 200 acceptance assertions for both endpoints to the existing delegated Reseller portal live-API scenario; no production endpoint changes. Also corrected the new audit assertion to compare AuditLog.resource_id (String(100)) with str(invitation_id). Ruff on the six focused source/test files and git diff --check pass. PostgreSQL live-API test remains unexecuted locally; exact-head isolated CI evidence is pending. No publication or database action performed.
## Audit attribution source reconciliation - 2026-11-19

Focused source review found portal grant create/revoke audit events in portal_access_service, tenant action-grant create/revoke events in tenant_action_grant_service, delegated Customer invitation create/revoke events in reseller_customer_users, portal-context activation in portal_access.py, and tenant-scoped system-actor events in Test Center and workflow approval workers. The portal-access and action-grant services already persist actor and target identifiers in tenant-scoped ledger rows; no duplicate production audit writes were added.

A concrete remaining gap is narrower: get_current_context and require_permission in backend/app/core/deps.py reject invalid portal context, tenant mismatch, inactive identity and missing permission with HTTP errors, but do not emit corresponding failure audit events. This is not safe to patch by indiscriminate exception logging: failure audit needs a defined transaction/commit policy and privacy contract, especially when request transactions roll back. Kept as a product/security design decision and isolated-CI verification item. No code change to authentication failure handling.
## Worker audit-attribution reconciliation - 2026-11-19

Source review covered Run execution/recovery, Outbox dispatch, AssignmentCommand execution, Workflow trigger/approval sweeps, and Test Center workers.

- Run execution audit is implemented in service paths, not directly in run_worker: run.created, knowledge.retrieved, memory.retrieved, tool.call, run.completed, run.failed, plus run.execution_entitlement_denied in the execution fence. Stale recovery writes run.execution_recovered with system actor, tenant, Run resource, request ID and recovery metadata.
- Workflow approval expiry and WorkflowRun timeout write system-attributed tenant/resource audit entries. Test Center expiry/start/pass also write system-attributed tenant/TestRun entries.
- Outbox dispatch/retry/dead-letter is represented by tenant-scoped OutboxMessage lifecycle fields plus metrics/spans/logs. No independent AuditLog event or actor identity was found in the dispatcher path.
- AssignmentCommand persists tenant, originating user, Run, Agent, delegation, WorkItem and command lifecycle/result, but the worker does not currently emit an independent AuditLog event for command success/failure.
- Do not conflate durable operational records with the immutable hash-chained AuditLog. Do not add duplicate or speculative audit writes until the product/security policy defines which Outbox and AssignmentCommand transitions require ledger entries, actor attribution, failure semantics and transaction coupling.
- No production code changed in this slice. No PostgreSQL test was run. Exact-head isolated CI remains pending for the previously authored acceptance cases.
- Next bounded decision: settle whether Outbox dispatch and AssignmentCommand terminal transitions require immutable audit entries; keep auth/permission/portal-context failure-audit transaction/privacy policy as a separate decision. Then continue with exact-head CI only when explicitly authorized.

## Audit read-surface reconciliation - 2026-11-19

- Operations audit listing is guarded by AuditReadContext (audit.read); the route supplies the effective context tenant to audit_service.list_logs. The service enforces tenant_id, optional action/status filters and a 1..200 result cap.
- Portal-context routing explicitly permits the audit-log read endpoint. Existing Vendor-to-Reseller delegated live-API assertions verify the effective target ledger is visible while sibling/foreign tenant marker actions are excluded. PostgreSQL execution remains pending isolated CI.
- Run artifact reads verify Run ownership and filter audit rows by tenant plus Run resource. WorkItem history requires audit.read, verifies WorkItem ownership, and filters by tenant plus WorkItem resource.
- Source review found no change required in these read paths. Evidence covers the exercised contexts only; it does not establish every portal hierarchy permutation or exact-head CI completion.

## Local focused-test runtime check - 2026-11-19

Attempted only the DB-free AssignmentCommand/Outbox contract group:
- Python 3.10: collection blocked because enum.StrEnum is unavailable (project source requires Python >=3.11).
- Python 3.11: pytest is not installed in that interpreter.
- Python 3.14 (Miniconda): pytest is not installed in that interpreter.
No test body executed and no dependency installation/environment mutation was attempted. This is an execution-environment limitation, not a test failure. Run this focused group in the repository's supported, dependency-complete CI/runtime after the existing publication/CI authorization gate; do not use a PostgreSQL target for this DB-free group.

## Supported focused-test runtime reconciliation - 2026-11-19

- The repository's canonical backend CI job in .github/workflows/ci.yml pins actions/setup-python to Python 3.12, installs backend/requirements.lock, then installs the backend package with pip install -e . --no-deps.
- backend/pyproject.toml declares requires-python = ">=3.11" and the dev extra includes pytest, pytest-asyncio and Ruff. The CI lock file is the reproducible dependency source for the canonical CI job.
- The local Windows Python launcher exposes only 3.10, 3.11 and 3.14; no 3.12 interpreter or repository virtual environment was found. Python 3.10 is below the project's declared minimum; Python 3.11/3.14 currently lack pytest in this host.
- Therefore the prior focused test attempt was not run in the repository's canonical runtime. Do not install dependencies, provision another interpreter, or substitute Docker/local DB execution without authorization. The next valid execution target is the existing exact-head isolated CI path after its explicit authorization gate.
- No CI run was triggered, no package/environment was changed, and no test body ran in this reconciliation.

## Runtime inventory correction - 2026-11-19

- A fresh `py -0p` check found Python 3.12.10 at the Windows launcher path; the earlier statement that this host had no Python 3.12 was incorrect and is superseded.
- `py -3.12 --version` succeeds, but `py -3.12 -m pytest --version` and `py -3.12 -m ruff --version` both fail because those modules are not installed. The alternate Python 3.12 path listed by the launcher is not present on disk.
- No test body ran, no dependencies were installed, and no environment was modified. The focused test group remains unexecuted; use the canonical dependency-complete exact-head CI path after its explicit authorization gate.
## Read-only source syntax review - 2026-11-19

- Parsed all 75 changed/new Python files with the installed Python 3.12.10 AST parser after UTF-8-SIG decoding: 0 syntax errors.
- Three new test files contain a UTF-8 BOM; BOM-aware parsing succeeds. No source files were modified by this syntax check.
- This is syntax validation only. Pytest/Ruff are unavailable in the local Python 3.12.10 environment, so no test cases or lint checks were executed.
## Billing, Run admission and Agent governance source audit - 2026-11-19

- Read-only review covered `billing_service.py`, `run_execution_fence.py`, `agent_run_governance_bootstrap.py`, `agent_delegation_service.py` and `agent_template_service.py`, plus their focused source-contract/unit/PostgreSQL test definitions.
- Billing: subscription lifecycle reads/writes are tenant-keyed; subscription creation and provider-event ingestion use unique-constraint savepoint recovery; execution and quota admission revalidate current commercial access after acquiring Subscription then Tenant locks. Quota counters are tenant-filtered, and the quota services document retaining the Tenant fence through the caller's resource insert.
- Run admission: the fence checks entitlement before WorkItem-lineage and Run locking; denied admission uses the canonical failed-state/audit path. Agent Run preparation checks expected tenant provenance, revalidates entitlement, locks WorkItem lineage before authority checks, and finally locks/re-reads the tenant-bound Run scope.
- Delegation: source/chain WorkItems and AgentDelegations are tenant-filtered; validation discovers the chain without retained locks, then locks the WorkItem set before parent-to-child delegation rows and rechecks current status, expiry, identity, review and scope. Creation binds the delegation and child WorkItem in one nested transaction with tenant idempotency and audit attribution.
- Agent templates: definitions/templates/instances are tenant-scoped; publication requires tenant-owned approver and evaluation evidence; provisioning cannot directly activate an instance; generic lifecycle transitions reject ENABLED and lock/refresh the tenant-owned instance before transition validation.
- Focused test definitions exist for quota lock order, PostgreSQL quota races, Run fence/governance preparation, delegation lock order and chain revocation, and template activation/lifecycle boundaries. These tests were inspected but not executed in this pass.
- No reproducible source defect was established by this bounded review; no speculative production change was made. This is not runtime proof: pytest/Ruff are unavailable in the local Python 3.12.10 interpreter, and the PostgreSQL race/CI evidence remains pending explicit authorization.
- Next: continue the documented Actor x Resource x Action gap register and exact-head isolated CI evidence path; do not expand into unrelated Agent or billing features.

## Reseller action-grant acceptance scenario authored - 2026-11-19

Added a focused PostgreSQL live-API test for the missing Reseller action-grant lifecycle: same-tenant member grant, direct Customer provisioning with parent/kind assertions, revocation, post-revocation 403, and rejection of a sibling-Reseller target user. The change is limited to the acceptance test; production code is unchanged. The test is not executed and requires the authorized isolated PostgreSQL CI gate. Vendor-to-Reseller grant/provision/revoke symmetry remains open and is tracked separately.

## Vendor action-grant acceptance scenario authored - 2026-11-19

Added a PostgreSQL live-API scenario proving, when executed, same-tenant Vendor member grant of `vendor.reseller.create`, direct Reseller provisioning with parent/kind assertions, revocation and subsequent 403, plus sibling-Vendor target rejection. Together with the Reseller-to-Customer scenario this defines both direct-child provisioning lifecycles; it is not runtime evidence until isolated PostgreSQL CI succeeds. No Production code changed.

## Vendor/Reseller lifecycle Actor x Resource x Action audit - 2026-11-19

Reviewed `edition_control.py`, `edition_deps.py`, `edition_lifecycle_service.py`, `test_edition_boundaries.py`, `test_tenant_lifecycle_concurrency.py`, `test_edition_action_permissions.py`, and Edition/portal live-API tests.

- Vendor direct Reseller lifecycle actions require tenant-local `vendor.reseller.manage` and API-key scope `edition.vendor.resellers.manage`; Vendor direct Customer actions require `vendor.customer.manage` and `edition.vendor.customers.manage`; Reseller direct Customer actions require `reseller.customer.manage` and `edition.reseller.customers.manage`.
- All routes use `set_child_tenant_status` with authenticated parent context and expected child kind. The service serializes changes with parent-first row locks, revalidates direct parent + kind, rejects child resume unless parent is active, makes deprovision terminal, and blocks parent deprovision until every child is deprovisioned. Deprovision disables tenant users, retains data, and emits an audit event attributed to the parent.
- No hard-delete/archive Edition route was found; deprovision is explicitly non-destructive.
- Existing tests cover hierarchy/transition rules, lock-order source contracts, and API-key scopes. The reviewed live API tests do not exercise lifecycle endpoints with Vendor/Reseller actors, sibling/wrong-kind targets, or the full transition sequence. Missing live acceptance evidence is established; a Production defect is not.
- No application/test code changed in this audit. No pytest, PostgreSQL test, CI, migration, or deployment was run. Next: add narrowly scoped PostgreSQL live-API coverage; execution remains behind explicit authorization.


## Lifecycle live API acceptance scenario authored - 2026-11-19

Added `test_vendor_reseller_lifecycle_routes_enforce_direct_child_boundaries` to `backend/tests/test_edition_live_api_access.py`. The PostgreSQL-backed scenario uses real Vendor and Reseller role permissions and bearer tokens and exercises Vendor->direct Reseller, Vendor->direct Customer, and Reseller->direct Customer lifecycle routes. It asserts positive suspend/resume/deprovision, wrong-kind and sibling-child authorization denials (403 at the authorization dependency), active-child parent deprovision rejection, terminal reactivation rejection, and persisted user deactivation.

The test is authored but not executed. No Production code changed; no pytest, PostgreSQL test, CI, migration, or deployment was run. The next acceptance step is explicit authorization to run the exact-head isolated PostgreSQL CI workflow.


### Child tenant lifecycle API-key scope contract - 2026-11-19

- Verified all nine suspend/resume/deprovision route templates map to their intended Vendor or Reseller manage scope and that each scope is allowlisted for the correct tenant kind.
- Added parameterized contract coverage for matching-scope acceptance and wrong-scope 403 rejection across Vendor╬ô├Ñ├åReseller, Vendor╬ô├Ñ├åCustomer, and Reseller╬ô├Ñ├åCustomer routes; added explicit Bearer-context bypass coverage.
- Test authored only; not executed. Existing PostgreSQL-backed lifecycle scenario remains authored but unexecuted. No Production code changed.

### Lifecycle negative-state coverage - 2026-11-19

- Extended the PostgreSQL-backed live API scenario to suspend a Reseller parent while its Customer child is suspended, assert child resume is denied with 403 by the parent-availability authorization dependency, then resume the parent and verify child resume succeeds.
- This directly exercises the route-level parent-availability guard (403); the service-level guard returns 409 when reached directly; test remains authored but unexecuted. No Production code changed.

### Deprovision audit attribution evidence - 2026-11-19

- Extended the live lifecycle scenario to verify deprovision audit rows are attributed to the managing parent tenant and authenticated actor for both Reseller╬ô├Ñ├åCustomer and Vendor╬ô├Ñ├åReseller transitions, including child_tenant_id metadata.
- Expanded the same PostgreSQL-backed live scenario to cover all three deprovision edges: Reseller?Customer, Vendor?Reseller, and Vendor?direct Customer. Each edge now asserts parent-tenant audit attribution, authenticated actor, child tenant/kind, previous status, and target status. Persisted user deactivation is asserted for the Reseller admin, Reseller Customer user, and direct Customer user. Test authored only; not executed. No Production code changed.
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
- Ran DB-free acceptance contracts against the repository's dependency-complete Python 3.12 container with the backend mount read-only: `test_edition_api_key_scope_contract.py` and `test_vendor_permission_backfill_migration.py` ╬ô├ç├╢ **17 passed**. Pytest emitted only a cache warning because the source mount was intentionally read-only; test results were successful and no repository artifacts were written by the runner.
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
### Vendor delegated user-management resolver ╬ô├ç├╢ implementation checkpoint (2026-11-20)
- Added `backend/app/services/tenant_user_management_service.py` with a DB-backed resolver that loads actor, target, parent, and (for nested Customer targets) grandparent from persisted `tenants` rows. It rejects inactive tenants, non-root Vendor actors, malformed Reseller ancestry, non-Customer actors, self-targeting, sibling/foreign ancestry, and unsupported hierarchy edges.
- The resolver is intentionally separate from `edition_service.assert_can_access`; no global edition access policy was widened.
- Added `backend/tests/test_tenant_user_management_service.py`; focused pure-policy tests: **8 passed**. `git diff --check` passed.
- Not yet integrated into HTTP routes; no invitation/list/revoke/status/role API behavior changed. No PostgreSQL resolver integration test has run yet.
- An attempted combined run with `test_edition_boundaries.py` had 18 passes and one environment/import failure because the local interpreter is Python 3.10 and an existing module imports `enum.StrEnum` (Python 3.11+); this is not evidence of a product regression. The first attempt also exposed an incorrect test expectation (a Reseller is allowed to manage all its own direct Customers); the test was corrected to use a Customer under a different Reseller.

### Vendor descendant user read APIs ╬ô├ç├╢ implementation checkpoint (2026-11-20)
- Added `backend/app/api/v1/vendor_tenant_users.py` with target-tenant-scoped GET endpoints for tenant-local users and assignable roles, using the DB-backed ancestry resolver. The route only exposes users whose `User.tenant_id` matches the resolved target; role listing is limited to target-tenant roles and system roles.
- Registered the router and added a dedicated API-key scope `edition.vendor.users.read` with explicit route-template mappings for both GET routes. The API-key scope contract remains fail-closed for unmapped routes.
- Authorization requires the Vendor administrator context plus the target-kind read permission (`vendor.reseller.read` or `vendor.customer.read`). The resolver enforces active target and persisted Vendor subtree ancestry.
- Validation: Python compileall succeeded for changed runtime modules; focused resolver + API-key scope tests: **23 passed**.
- Write operations (invite/revoke/status/role assignment) are not yet exposed for Vendor; no DB-backed live API test has run for these new endpoints. No PostgreSQL or persistent database was touched.

### Validation correction (2026-11-20)
- After adding the new Vendor users read scope to the Vendor API-key allowlist, the final focused run completed with **25 passed** across `test_tenant_user_management_service.py` and `test_edition_api_key_scope_contract.py`; compileall and `git diff --check` also succeeded.

## 2026-11-20 - Vendor child-user write implementation checkpoint
Vendor child-user API now has invitation create/revoke and activate/deactivate operations, reusing the tenant invitation service, entitlement gate, last-admin safeguards, token-version invalidation, persisted ancestry resolution, and dual-scope success audit records. API-key write calls require `edition.vendor.users.manage`. Focused local tests: 28 passed. Role assignment/removal and PostgreSQL live API acceptance remain open; no publication actions performed.

## 2026-11-20 - Vendor descendant role administration added
Added target-tenant role replacement API. Only target-local or system roles can be selected; role permission sets must be subsets of the Vendor actor's explicit effective permissions. `vendor.*`, `platform.*`, Platform Admin, and Superuser grants are rejected. Last active target-tenant admin protection and dual-tenant audit are applied. API-key scope remains `edition.vendor.users.manage`. Focused suite: 74 passed. PostgreSQL live route acceptance remains open.

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

### Final Vendor role-boundary exact-head CI confirmation - 2026-11-20
- The role-boundary extension is published in commit `a175f107bf69d7cd3c00df9180df55305c9cb97e` on PR #1434. Fresh PostgreSQL 16.15 live acceptance passed **1/1 in 5.74s**, including global Platform Admin denial (403), foreign tenant role rejection (400), and target role-list read (200).
- PR #1434 exact-head check rollup for `a175f107bf69d7cd3c00df9180df55305c9cb97e`: **35 SUCCESS, 0 failures, 0 pending**. Includes Backend, Frontend, Security/Privacy, CodeQL (Python and JS/TS), Architecture, Runtime Isolation/RBAC, DAST, Recovery, Infrastructure, and real-stack E2E suites.
- The branch is synchronized with origin. The remaining 81 local dirty/untracked paths are unrelated ongoing Agent/Outbox/AssignmentCommand work; they have not been staged, reset, cleaned, or bundled into PR #1434.
- This confirms the current Vendor user-administration slice, not final Issue #1350 acceptance. Issue #1350 remains OPEN; human portal UX acceptance and the separately tracked historical migration/audit-policy items remain open.

## 2026-11-20 - Outbox and AssignmentCommand focused verification checkpoint

- Reconciled the active branch against GitHub: local HEAD and `origin/test/knowledge-revoked-portal-context-20261108` are both `02d150c8fb548ad331a9e3cfc52fe42a80b3f059`; PR #1434 is OPEN (not draft), and all **35/35** displayed PR checks pass on that exact head. PR #1447 remains OPEN + Draft on its separate stacked head `425d40d081c56b0b66a26727772d900062cd9868`. Issue #1350 remains OPEN.
- Preserved the 81 pre-existing modified/untracked worktree paths. No reset, clean, staging, code edit, commit, merge, deployment, or persistent database operation was performed in this verification slice.
- Source review of `outbox_service.py`, `outbox_worker.py`, `assignment_command_service.py`, `assignment_command.py`, and `assignment_command_worker.py` confirms operational state transitions and durable retry/lease/recovery behavior, but no immutable AuditLog transition writes in these paths. Do not add audit writes until the unresolved event semantics, actor attribution, failure policy, privacy, and transaction/commit coupling are approved; generic exception logging is not a substitute.
- Focused DB-free contracts passed on Python 3.12: AssignmentCommand service/worker contracts, Outbox lease/replay contracts, WorkItem locking, and workflow timeout reconciliation ╬ô├ç├╢ **30 passed in 1.70s**. Full backend Ruff (`app` + `tests`) passed. `git diff --check` passed (only pre-existing LF/CRLF warnings).
- PostgreSQL race/recovery tests in this slice are explicitly CI-only and were not locally executed; their CI guards require `CI=true` and a dedicated loopback `support_test` database. No guard was bypassed. The only running Docker services remain the pre-existing Staging PostgreSQL/Redis containers on ports 15434/16379.
- Remaining acceptance gates are unchanged: approved immutable-audit/failure-event policy; sanitized historical Vendor permission-backfill snapshot; human visual acceptance of the distinct portals; and completion of the documented Actor x Resource x Action gaps. The Vendor descendant user-administration slice remains separately accepted by its disposable PostgreSQL live test and exact-head CI evidence; this does not close Issue #1350.
## 2026-11-20 - Notification destination tenant-predicate evidence

- Revisited the exact remaining narrow gap named by the acceptance matrix: tenant handoff notification destination lookup must read `Tenant.settings` for the conversation-owning tenant, not an actor/portal-context or caller-selected tenant.
- Executed the existing focused regression `tests/services/test_customer_handoff_notification_outbox.py`: **3 passed in 0.89s** on Python 3.12. The specific query-contract case compiles the SQL with the PostgreSQL dialect and asserts the `tenants.id` predicate and the conversation tenant UUID are bound in the statement.
- This closes the narrow query-predicate evidence gap for the inspected handoff destination lookup only. It does not complete the broader Notifications/Outbox actor Γö£├╣ hierarchy Γö£├╣ delivery-kind matrix. The test and related Outbox implementation remain part of the preserved local in-progress worktree; they were not included in the documentation-only GitHub commit.
- No production code was changed in this verification step, and no database was used. Continue only with the next documented uncovered notification/worker case; do not infer full matrix acceptance from this focused contract.
## 2026-11-20 - Notification and Outbox delivery-contract verification

- Continued the documented Notifications/Outbox actor Γö£├╣ hierarchy Γö£├╣ delivery-kind review with the existing focused delivery contracts; no production code or test definitions were changed in this verification slice.
- Python 3.12 focused run across email Outbox crash safety, worker crash safety, WhatsApp worker behavior, enqueue-race handling, tenant-scoped deduplication, approval-resume enqueue, run-creation enqueue, Outbox hardening, and tenant handoff notification destination: **36 passed in 2.04s**.
- Targeted Ruff over the inspected notification/Outbox services, workers, and test files: **All checks passed**. `git diff --check` passed; existing LF/CRLF warnings relate to preserved unrelated dirty files.
- These tests establish the listed local contracts only. They do not substitute for PostgreSQL race tests whose fixtures require CI-only `support_test`, nor do they prove the complete actor/hierarchy/delivery-kind matrix or immutable AuditLog coverage. No PostgreSQL, Staging, or Production database was accessed.
- Existing Outbox/AssignmentCommand and Agent worktree changes remain untouched and unstaged. Issue #1350 remains OPEN; unresolved audit/failure-event policy, historical migration snapshot review, human portal UX acceptance, and remaining matrix cells remain acceptance gates.
## 2026-11-20 - Entitlement and execution-fence regression verification

- Followed the roadmap after the bounded Notifications/Outbox verification and revalidated the existing commercial-entitlement and execution-fence contracts; no production code or test definitions were changed.
- Python 3.12 focused suite across `test_tenant_access_service.py`, `test_run_execution_fence.py`, `test_subscription_state_creation_fence.py`, and `test_quota_race_fencing.py`: **32 passed in 1.39s**.
- Targeted Ruff for the entitlement service, billing guard, execution fence, and four test modules: **All checks passed**. `git diff --check` passed; only existing LF/CRLF warnings from preserved worktree files remain.
- This confirms the listed DB-free contracts, including current entitlement denial, already-issued portal access expiry, paused subscription denial, run execution admission, and quota lock-order contracts. It does not replace the isolated PostgreSQL provider-window/revocation race tests or prove the complete worker matrix. No PostgreSQL, Staging, or Production database was accessed.
- Existing 81 modified/untracked Agent, Outbox, and AssignmentCommand paths remain preserved and unstaged. Continue with the next exact worker/entitlement acceptance gap from the matrix; do not add speculative audit writes while event semantics and failure policy remain unresolved. Issue #1350 remains OPEN.

## 2026-11-20 - Run and workflow worker recovery contract verification

- Continued the documented execution/worker acceptance path using the existing DB-free recovery and tenant-boundary contracts; no production code or test definitions changed.
- Python 3.12 focused run: `test_run_recovery.py`, `test_run_recovery_worker.py`, `workers/test_run_worker.py`, `test_workflow_worker_tenant_boundary.py`, `test_workflow_worker_retry_safety.py`, `test_workflow_child_execution_cancellation_boundary.py`, and `test_workflow_execution_concurrency_safety.py`: **28 passed in 4.09s**.
- Targeted Ruff over the corresponding recovery/run/workflow worker source and test files: **All checks passed**. `git diff --check` passed; pre-existing LF/CRLF warnings remain on preserved dirty files.
- This verifies the selected local contracts for stale-run recovery, tenant-scoped recovery lookup, durable failure projection, run worker tenant/authority checks, workflow tenant binding, cancellation boundary, and retry/recovery lease safety. It does not replace PostgreSQL multi-tenant recovery/lock-order tests or the CI-only provider/revocation races. No database was accessed.
- An initial command referenced a non-existent test path (`tests/test_run_worker.py`); corrected path is `tests/workers/test_run_worker.py`. A Ruff invocation likewise named a non-existent service path and was rerun against the actual worker source files; the corrected Ruff run passed. No files were changed by either unsuccessful invocation.
- Existing 81 modified/untracked paths remain preserved and unstaged. Issue #1350 remains OPEN; the audit/failure policy, sanitized historical permission-backfill snapshot, human portal UX acceptance, and remaining matrix cells are still open.

## 2026-11-20 - Exact-head GitHub acceptance verification

- Rechecked PR #1434 after the Run/Workflow recovery documentation push. Its head is exactly `70dfc96196f89e0039b3b4fdf87e349bc23ca15e`, the PR remains OPEN and non-Draft, and all **35** reported checks on that head are successful, including Backend CI, PostgreSQL real-stack suites, Recovery, Tenant hierarchy/RBAC, Security/Privacy, Architecture, DAST, CodeQL, and Documentation Truth Consistency. CI run: https://github.com/ijoolaie/AI-Employee/actions/runs/44710735331.
- PR #1447 remains a separate OPEN Draft on `425d40d081c56b0b66a26727772d900062cd9868`; it was not modified or merged.
- Reconciled the audit acceptance boundary against the current matrix: Outbox dispatch has durable tenant-bound operational state but no actor identity or immutable ledger event; AssignmentCommand stores actor/tenant/command provenance but no independent immutable ledger event. The decision to add those events, their actor semantics, failure policy, privacy bounds, and transaction coupling remains unresolved. No speculative audit writes were introduced.
- The green exact-head CI confirms the committed branch state only; it does not resolve the historical permission-backfill snapshot review, human portal UX acceptance, or remaining actor/resource/action cells. Issue #1350 remains OPEN.
- The 81 pre-existing modified/untracked Agent, Outbox, and AssignmentCommand paths remain untouched and unstaged. No local, Staging, or Production database was accessed in this verification.

## 2026-11-20 - PR #1434 exact-head CI completion

- Re-polled GitHub checks after the documentation-only exact-head commit. PR #1434 remains OPEN and non-Draft at `d45918c8e5b5b3ee35062f26b5735781b7e53c91`; all **35/35** displayed checks are `pass`, with **0 failed, 0 pending, 0 skipped** in the check list. This includes Backend, Frontend, CodeQL Python and JavaScript/TypeScript, Tenant hierarchy/RBAC, Security/Privacy, DAST, Architecture, Recovery, Semantic E2E, W4/W5/W16/W20 real-stack, and remaining listed checks.
- PR #1447 remains OPEN + Draft at `425d40d081c56b0b66a26727772d900062cd9868`. Issue #1350 remains OPEN. No merge, deployment, or database operation was performed.
- The exact-head CI result confirms the currently committed PR branch only. It does not close the remaining acceptance gates: immutable Outbox/AssignmentCommand audit event semantics and failure/privacy/transaction policy; sanitized historical Vendor permission-backfill snapshot review; human visual portal acceptance; and any remaining Actor x Resource x Action matrix cells.
- Preserved all **81** pre-existing modified/untracked worktree paths without staging, resetting, cleaning, or altering them. The next implementation step must continue from the documented acceptance matrix; do not add speculative audit writes or use a shared/persistent test database.

## 2026-11-20 - Assignment recovery and worker lock-order PostgreSQL proof

- Continued the documented worker/transaction-race acceptance path on a fresh PostgreSQL 16 disposable database. Applied the complete Alembic chain through `w35_assignment_recovery_claims` using a dedicated Docker network and tmpfs-backed data directory.
- Executed the existing PostgreSQL lock/recovery tests for approval-worker Run/Approval lock order, AssignmentCommand WorkItem/Run lock order, AssignmentCommand recovery claim/retry/release fencing, quota Subscription/Tenant lock order, and tenant invitation reissue/activation lock order: **8 passed in 5.54s**.
- The first run exposed one test-harness defect: the exact-token recovery-claim release test did not redirect the worker's `worker_db_session` to its isolated test engine. Added the same test-local session fixture pattern already used by adjacent tests; no production code was changed. The complete focused PostgreSQL set then passed.
- Targeted Ruff passed for all five PostgreSQL test modules; Python 3.12 compileall passed for the adjusted recovery test; `git diff --check` passed. Existing unrelated LF/CRLF working-copy warnings remain.
- Removed only the temporary container `ai-emp-lockproof-20261120` and its dedicated network. The tmpfs database was destroyed. Pre-existing Staging PostgreSQL and Redis containers remained untouched; no persistent, Staging, or Production database was accessed.
- All pre-existing Agent/Outbox/AssignmentCommand worktree paths remain preserved. This is bounded PostgreSQL concurrency/recovery evidence, not completion of the full actor/resource/action matrix or final Issue #1350 acceptance. Immutable Outbox/AssignmentCommand audit semantics, historical permission snapshot review, and human portal UX acceptance remain open.
## 2026-11-20 - Vendor/Reseller child lifecycle live PostgreSQL acceptance

- Executed `backend/tests/test_edition_live_api_access.py::test_vendor_reseller_lifecycle_routes_enforce_direct_child_boundaries` against a fresh PostgreSQL 16 disposable database, with a dedicated Docker network and tmpfs-backed database storage. The full Alembic graph migrated successfully through `w35_assignment_recovery_claims`.
- Live HTTP lifecycle acceptance: **1 passed in 76.13s**. The scenario covers Vendor -> direct Reseller, Vendor -> direct Customer, and Reseller -> direct Customer; suspend/resume/deprovision transitions; invalid transition and terminal-state rejection; sibling/wrong-kind denial; parent deprovision guard when children remain; persisted user deactivation; and parent-tenant/authenticated-actor audit attribution with child metadata.
- The test ran unchanged; no application or test source was modified in this slice. This supplies execution evidence for the previously authored lifecycle matrix, not proof of the entire Issue #1350 acceptance surface.
- The uniquely named container and dedicated network were removed in a `finally` cleanup. The database used tmpfs only. No persistent, Staging, or Production database/service was accessed or modified.
- Remaining acceptance gates: immutable Outbox/AssignmentCommand audit event semantics and failure/privacy/transaction policy; sanitized historical Vendor permission-backfill snapshot review; human visual portal acceptance; and any remaining Actor x Resource x Action matrix cells. Issue #1350 remains OPEN.
## 2026-11-20 - Extended Agent, Email, WhatsApp, and Assignment Outbox contract verification

- Reconciled the Outbox/AssignmentCommand actor and delivery-kind evidence against the existing worker implementations. The dispatcher validates durable tenant binding for Agent Run and AssignmentCommand messages; Email revalidates deferred Agent authority before SMTP and again at the side-effect boundary; WhatsApp requires a persisted Agent governance proof, checks exact tool/tenant/run/approval-call binding, and reauthorizes before provider delivery. Dedicated Email/WhatsApp workers own their external-side-effect uncertain boundary rather than the generic dispatcher.
- Ran the combined Python 3.12 focused suite covering Agent Outbox governance, generic dispatcher crash/retry/tenant-binding behavior, WhatsApp governance and uncertain delivery, Email crash/authorization/uncertain delivery, AssignmentCommand provenance/lease/recovery contracts, approval-resume and Run-creation enqueue contracts, and tenant-bound handoff notification destination: **56 passed in 2.02s**.
- Targeted Ruff across the corresponding production services/workers and test modules: **All checks passed**. `git diff --check` passed. No production or test source was changed in this verification slice; no database or provider was contacted.
- This extends the bounded worker/delivery evidence. It does not close the full actor x hierarchy x delivery-kind matrix, prove immutable AuditLog transition coverage, or settle the unresolved failure/error privacy and transaction-coupling policy. Do not add speculative audit writes or change error persistence until that policy is approved.
- The 81 pre-existing local worktree paths remain preserved and unstaged. Issue #1350 remains OPEN. Remaining gates include the audit/failure policy, sanitized historical Vendor permission-backfill snapshot review, human visual Portal acceptance, and remaining matrix cells.
## 2026-11-20 - Reseller-to-Customer sibling file isolation acceptance

- Compared the outstanding file-portal PRs #1428 and #1432 against current `main` (`8829373a092c1fb446c747822e4097985c171f68`). The current live API test already exercises Vendor-to-direct-Customer file upload/get/download/delete and Reseller-to-Customer upload/get/download/delete, including home-tenant isolation and post-delete 404. PR #1428's lifecycle scenarios are therefore already represented; do not duplicate them.
- Added the one uncovered sibling-Customer file boundary to `backend/tests/test_portal_access_live_api.py`: a distinct unentitled Customer under the same Reseller owns a seeded file; the granted Customer portal must omit that file from listing and receive 404 for get, download, and delete. Existing direct/nested lifecycle assertions were retained.
- Validation: PostgreSQL 16 disposable tmpfs database on dedicated Docker network, Alembic migrated to `w33_tenant_action_grants`; live HTTP test `test_portal_grant_activates_context_and_revocation_invalidates_it`: **1 passed in 34.24s**. Ruff for the changed test file passed; `git diff --check` passed.
- Test isolation: only the uniquely named temporary PostgreSQL container/network were used. Staging PostgreSQL (`15434`) and Redis (`16379`) were not touched. Python 3.10 is below the project's runtime requirement for `enum.StrEnum`; the test was correctly rerun and passed under Python 3.12. The initial Python 3.10 invocation did not execute the test body.
- The consolidated sibling-isolation change is prepared on a clean branch based on current `main`; exact-head GitHub CI is still required before merge. PR #1428 is redundant against current main; PR #1432's missing sibling assertions are represented by this focused addition. Issue #1350 remains OPEN.

## 2026-11-20 - PR #1448 WhatsApp outbox merge

- PR #1448 (`fix: register and route WhatsApp outbox delivery`) completed all **16/16** exact-head checks successfully on `33d12bd12dc6cbb4b49d4f335885d8342eb3f2cb`, based on `8829373a092c1fb446c747822e4097985c171f68`, and was merged using a merge commit.
- Merge commit and resulting `main` head: `d1a8a794d4bd4474c03ce436c735d552586c44b4`. The PR state was verified as MERGED.
- This does not close Issue #1350 or resolve the separate audit-policy, historical migration snapshot, human UX, and remaining matrix gates.

## 2026-11-20 - Tenant notification and action-grant PR merges

- PR #1449 (`test: verify customer handoff notification tenant scoping`) completed all **12/12** exact-head checks successfully on `874afda1c9318c852a204d008668eb2aa33f3397`, based on `6e17d8a611e4194b684daff4341098455c76d5a7`; merged commit `8829373a092c1fb446c747822e4097985c171f68`.
- PR #1453 (`test: cover symmetric tenant action grant delegation`) completed all **12/12** exact-head checks successfully on rebased head `e9d34899aad5035c938330b90f14d65c664c8d8e`, based on `d1a8a794d4bd4474c03ce436c735d552586c44b4`; merged commit `b82a5f0b368bf532c21e2aba07e9995aef4ad6f8`.
- Both PR states were verified MERGED and `main` advanced to `b82a5f0b368bf532c21e2aba07e9995aef4ad6f8`. Issue #1350 remains OPEN; these merges do not resolve the outstanding audit-policy, historical migration snapshot, human UX, or remaining matrix gates.
## 2026-11-20 - Hierarchical handoff recipient PostgreSQL proof

- Ported the non-conflicting acceptance case from stale PR #1454 onto current `main` without rebasing or replacing the existing test module. The test creates a Vendor, two sibling Resellers, Customers beneath both, and an unconfigured Customer beneath the configured Reseller.
- It asserts the resolver returns each Vendor/Reseller/Customer's own configured `customer_handoff_notification_email`, never a sibling's value, and returns `None` for an unconfigured child rather than falling back to a parent setting.
- Validation on PostgreSQL 16 disposable tmpfs + dedicated Docker network, Alembic head `w33_tenant_action_grants`: `test_handoff_notification_recipient_is_exact_tenant_in_hierarchy` **1 passed in 1.45s**. Targeted Ruff and `git diff --check` passed.
- The temporary container/network were removed after the run. Staging PostgreSQL/Redis were untouched. This proves exact-tenant destination resolution only; end-to-end dispatch, stale/revoked grant transitions, retry/dead-letter delivery and notification-content isolation remain partial. Issue #1350 remains OPEN.
- Consolidated in PR #1456; exact-head CI is rerunning after synchronization with current main.
## 2026-11-20 - PR #1456 hierarchical handoff proof merged

- PR #1456 completed all **13/13** exact-head checks on `9285dc487a99f2a347f546fd9fd6309087c1df0d`, based on `b08f436cb15dd1422a752a941a021c4dd7d1c814`; merge commit `0799dcf95d9ba161237b56506b0d3e5498deb71f`.
- The PostgreSQL-backed exact-tenant notification destination test is now on main. The matrix remains partial for end-to-end dispatch/retry/revocation and content-isolation cases.

## 2026-11-20 - Test Center worker tenant binding and Report Employee actor attribution

- Reconciled the stale Test Center worker changes from PR #1451 against current main. The current Test Center API dispatched only `run_id`, and its Celery worker selected `TestRun` by ID alone. Updated the API to dispatch the validated `ctx.tenant_id`, made the task require/parse both UUIDs, and constrained the worker's initial Run lookup by both `TestRun.id` and `TestRun.tenant_id`.
- Added a PostgreSQL integration case proving a wrong dispatched tenant receives `test run not found` and leaves the Run queued, while the matching tenant executes and persists PASSED. Updated the existing mismatched-definition test for the explicit tenant argument. Added focused unit guards for the SQL tenant predicate, invalid tenant UUID, and API dispatch argument.
- Reconciled Report Employee attribution: `ToolRegistry.execute(analyze_dataset)` now forwards the Run actor ID instead of `None`; a focused regression asserts the exact actor/tenant/file IDs passed to the report service. `analyze_document` behavior was deliberately left unchanged.
- Validation: disposable PostgreSQL 16 tmpfs + dedicated Docker network, Alembic head `w33_tenant_action_grants`; full `tests/test_test_center_integration.py`: **5 passed in 3.74s**. Worker guard + Report Employee actor tests: **4 passed in 2.79s**. Targeted Ruff and `git diff --check` passed.
- Temporary PostgreSQL container/network removed. Staging PostgreSQL/Redis were untouched. This proves the Test Center worker's tenant-qualified lookup and handler-level Report Employee actor forwarding; it does not prove all Test Center lifecycle/background sweeper paths or full persisted Agent Run/worker delegated portal execution. Issue #1350 remains OPEN.

## 2026-11-20 - Delegated Usage Optimization and Cost Forecast portal context

- Reconciled PR #1451's Usage API delta against current main. `/api/v1/usage/optimization` and `/api/v1/usage/cost-forecast` use `AuditReadContext` and tenant-scoped services, but the portal-context route guard denied them because only `/usage/summary` was explicitly exempted from the `/usage` denied prefix. Added only these two read endpoints to the portal allowlist; other unknown `/usage/*` paths remain denied by default.
- Added route-policy allowlist regression assertions and extended the authenticated PostgreSQL portal test to call both endpoints through Vendor A→Reseller, Vendor B→Reseller, and Reseller→Customer grants. Stubbed service functions capture the effective tenant ID; every call must match the delegated resource tenant, not the actor's home tenant or sibling.
- Added `audit.read` to the Reseller test role because both endpoints require `AuditReadContext`. Existing Vendor B and Customer grant revocation assertions remain after the new active-grant checks; no revocation behavior was weakened.
- Validation: route-policy module **20 passed in 0.67s**; live PostgreSQL 16 portal HTTP test **1 passed in 30.89s** on disposable tmpfs + dedicated Docker network, Alembic head `w33_tenant_action_grants`; targeted Ruff and `git diff --check` passed.
- Temporary PostgreSQL container/network removed. Staging PostgreSQL/Redis untouched. This proves the two read endpoints' delegated tenant context across the three portal topologies; it does not complete the entire usage/finance matrix or persisted Run/worker execution. Included in PR #1457; exact-head CI will rerun after push.

## 2026-11-20 - Global worker sweeper tenant attribution

- Ported the bounded tenant-attribution regression cases from stale PR #1451 onto current main without changing worker runtime code: Test Center global expiration sweep audits each transitioned Run with that Run's tenant/resource ID; Workflow timeout sweep audits each timed-out Run with its own tenant; Run stale recovery audit uses the locked Run tenant; Workflow approval expiry audit uses the approval tenant/resource and does not mutate the unrelated cross-tenant Run/Step.
- Validation: `test_worker_sweeper_tenant_attribution.py`, `test_run_recovery.py`, and `test_workflow_approval_expiry_tenant_boundary.py`: **9 passed in 1.61s**. Targeted Ruff and `git diff --check` passed. These are deterministic fake-session/unit proofs; no database or provider was contacted.
- This does not complete every worker/dispatch/retry path or the delegated Run actor/grant provenance lifecycle. Included in PR #1457; exact-head CI required.

## 2026-11-20 - Delegated invoice PDF and Report Employee artifact ownership

- Extended the live portal PostgreSQL test to assert generated invoice PDF `FileObject` rows are owned by the resolved resource tenant and uploaded by the effective actor for Vendor A→Reseller, Vendor B→Reseller, and Reseller→Customer contexts. Added negative checks that a Vendor A portal cannot export a Vendor B invoice and a revoked Vendor portal cannot export its former target invoice.
- Report Employee `analyze_dataset` artifact rows are now asserted to use the Customer tenant and the Customer actor who invoked the tool; this complements the focused ToolRegistry actor-forwarding test.
- Validation: updated live PostgreSQL 16 portal HTTP test completed successfully (**1 passed**) on disposable tmpfs + dedicated Docker network, Alembic `w33_tenant_action_grants`; targeted Ruff and `git diff --check` passed. Temporary DB container/network removed.
- Included in PR #1457; exact-head CI reruns after this test-only extension.

## 2026-11-20 - Acceptance matrix reconciliation after merged PRs

- PR #1434's Vendor descendant user-management implementation is accepted for its tested subtree: PostgreSQL live HTTP lifecycle 1 passed and exact-head CI 35/35. This covers Vendor invite/revoke, activate/deactivate, descendant role assignment/removal, permission-subset ceiling and last-admin protections across tested direct/nested descendants.
- PR #1453 symmetric action-grant delegation merged after 12/12 exact-head checks; PR #1455 sibling Customer file isolation merged after 13/13; PR #1456 hierarchical notification destination proof merged after 13/13.
- The acceptance matrix was reconciled to those exact outcomes. PR #1457 carries the next bounded local evidence for delegated usage/invoice/report ownership, Test Center worker tenant binding, and sweeper audit attribution; exact-head CI remains pending.
- Remaining gates are unchanged: immutable audit/failure-event policy, sanitized historical permission-backfill snapshot, human UX acceptance, tenant-managed role CRUD scope, and remaining concrete actor/resource/action cells. Issue #1350 remains OPEN.

## 2026-11-20 - PR #1457 merge and acceptance matrix correction

- PR #1457 merged at `e4dd59109eae6c4c56bf23921dcca4b9f1cc1aba` after 33/33 exact-head CI checks. It integrates tenant-qualified Test Center dispatch/worker lookup, Report Employee actor propagation, delegated Usage Optimization/Cost Forecast route context, worker-sweeper tenant attribution, and Vendor A/Vendor B/Reseller→Customer invoice PDF and Report Employee artifact ownership checks.
- File lifecycle/sibling-isolation status was reconciled against merged main: direct Vendor→Customer and nested Reseller→Customer upload/get/download/delete, plus sibling Customer list/get/download/delete denial, are already present and PostgreSQL live-tested. The previous progress note claiming these were still missing was stale; no duplicate test or old conflicting PR cherry-pick is needed.
- PR #1448, #1449, #1453, #1455, #1456 and #1457 are merged. Issue #1350 remains OPEN.
- Remaining gates: end-to-end Notifications/Outbox dispatch/retry/dead-letter and revoked-context/content isolation; delayed worker/provider-boundary permutations; broader asynchronous export/report actor/topology coverage; representative sanitized historical permission-backfill snapshot review; human portal UX acceptance; and explicit policy decisions for immutable Outbox/AssignmentCommand audit events, actor semantics, failure/privacy handling and transaction coupling. Tenant-managed role CRUD scope also remains undecided.
- Primary worktree remains untouched at 81 dirty paths and HEAD `818e5a8308615b491b56e82951da745339312756`.
## 2026-11-20 - Handoff notification content minimization and cross-tenant isolation

- Extended the PostgreSQL-backed Customer handoff test with distinct synthetic customer names, email addresses and phone numbers for two independent tenants. The persisted notification payload must equal the minimal routing template (conversation/channel/owning-tenant IDs and authenticated workspace instruction); it must not contain customer name/contact details or the customer's message text.
- The second tenant's notification body must contain only its own tenant/conversation/channel identifiers and must not contain the first tenant's identifiers. Existing exact recipient/dedupe assertions remain.
- Disposable PostgreSQL 16 tmpfs + dedicated Docker network, Alembic head: `test_customer_channel_handoff_postgres.py` **3 passed in 4.57s**. Ruff and `git diff --check` passed. Temporary DB container/network removed; staging services untouched.
- This closes the focused handoff-email payload minimization/cross-tenant-content assertion. It does not complete all Notifications/Outbox delivery-kind, retry/dead-letter worker, stale/revoked delegated-context or provider-boundary permutations.

## 2026-11-20 - Test Center delayed execution entitlement fence

- Found and corrected a source/documentation mismatch: Test Center's API request path checked tenant access, but the queued worker did not revalidate entitlement immediately before starting. It now calls the shared `assert_run_execution_entitlement` guard after tenant/run/definition binding checks and before the state transition.
- PostgreSQL 16 disposable integration: `test_test_center_integration.py` **5 passed in 4.08s**; wrong tenant is rejected before entitlement evaluation, inactive entitlement leaves the run queued, and restored entitlement allows the correct tenant to complete. Ruff/diff check passed; disposable container/network removed.
- PR #1459 exact-head CI pending. This proves worker delegation to the shared commercial execution guard, not the entire delayed worker/provider matrix. Issue #1350 remains OPEN.

## 2026-11-20 - Email Outbox delivery-kind fence

- Source audit found email_worker._send loaded an Outbox row by ID and checked delivery status, but did not verify kind == "email.send" before entering the SMTP path. The dedicated WhatsApp worker already rejects rows of any other kind.
- Added a fail-closed delivery-kind check before authorization, uncertain-state commit, or SMTP. Added a regression test that invokes the email task with a whatsapp.send_text row and proves SMTP is not reached and the row remains unchanged. Existing email fixtures now declare their persisted delivery kind explicitly.
- Red/green evidence: the new regression failed before the production guard because SMTP was reached; after the guard, focused Outbox worker/email/WhatsApp tests: **19 passed in 0.88s**. Additional Agent governance, handoff enqueue, and legacy Outbox contract tests: **11 passed in 2.02s**. Targeted Ruff and git diff --check passed.
- Change is isolated on fix/email-outbox-kind-fence-20261120, based on main 0b5456c425e3108764445e76bcf77d628c8872d9; exact-head GitHub CI is required before merge. This closes only the email task-to-row delivery-kind mismatch; the full actor ? hierarchy ? delivery-kind retry/dead-letter/revocation matrix remains partial. Issue #1350 remains OPEN.

## 2026-11-20 - Outbox claim lease and concurrent dead-letter replay

- `outbox_service.claim` now resets `available_at` when a row enters `processing`, so the five-minute stale-processing recovery interval starts at claim time rather than an earlier pending due time. This prevents a long-waiting pending row from being immediately reclaimed after dispatch.
- Dead-letter replay now selects by both message ID and authenticated tenant ID under `FOR UPDATE`, then checks the locked row's current status. A competing replay waits for the first transaction and observes `pending`, returning HTTP 409 rather than resetting or dispatching the same message twice.
- Replay resets the retry budget (`attempts=0`) and clears terminal delivery metadata (`dispatched_at`, `last_error`, `dead_at`) while setting one consistent `available_at`/`replayed_at` timestamp.
- Focused suite on disposable PostgreSQL 16 tmpfs + dedicated Docker network, Alembic head: **4 passed in 1.98s**. The PostgreSQL integration asserts one concurrent replay succeeds, the second receives HTTP 409, and only one persisted replay transition occurs. Targeted Ruff and `git diff --check` passed. Temporary DB container/network removed; staging services untouched.
- This closes the claim-time lease and concurrent replay serialization contracts only. It does not complete the full actor × hierarchy × delivery-kind retry/dead-letter/revocation/provider matrix or settle immutable audit event policy. Issue #1350 remains OPEN; exact-head CI is required before merge.
## 2026-11-21 - Celery/Kombu/Redis compatibility and PR #1440 merge

- PR #1440 was refreshed onto main at d76429e25f7f4f3d79fb7fead372b0a18881938f. Its W10 real-stack failure was traced to Kombu Redis transport rejecting redis-py 5.3.1 (Redis transport requires redis-py versions 6.1.0 or later); Celery 5.7 requires the newer 6.x Redis client line.
- Aligned both backend manifests: celery[redis]>=5.4.0,<5.8.0, kombu>=5.5.4,<5.8.0, and redis>=6.4.0,<7.1.0.
- Exact PR head 10e2c1df6e2857474aa6e2860af5b5d771f6c586 passed all 13 required checks, including both W10 real-stack runs. PR #1440 merged as 4ed51137ff7fe0afbcd34d7d5714b829f779fb95; source branch retained. main now points to this merge commit.
- Rechecked PRs #1442 and #1443: their old checks are green, but both are behind their respective bases and report mergeable=false, mergeable_state=dirty. They are not eligible for merge; resolve/synchronize conflicts and rerun exact-head checks before reconsideration.
- Issue #1350 remains OPEN. Remaining acceptance gates: full Notifications/Outbox actor x hierarchy x delivery-kind lifecycle matrix; explicit immutable Audit Ledger/Failure Audit Policy decisions; sanitized historical Vendor permission-backfill snapshot review; human UX acceptance for #1452; remaining Actor x Resource x Action cells; and broader asynchronous export/report actor/topology coverage. No staging/prod migration, deployment, or UX acceptance is claimed.


## 2026-11-21 - Outbound Email/WhatsApp commercial entitlement correction

- Main checkpoint reviewed: dbca8059cec2f074da8cf75398d44e75abea0b73 (after PR #1462). A fresh source inspection found a gap that earlier entitlement notes had not actually closed in the dedicated Email/WhatsApp workers: they held the Tenant lifecycle lock but did not call the commercial entitlement guard.
- Corrected on isolated branch fix/outbox-commercial-entitlement-20261121: billing_service.assert_outbound_delivery_entitlement delegates to the existing assert_run_execution_entitlement, translating deterministic entitlement denials into TenantInactiveError. Email and WhatsApp call it after the durable uncertain fence and hold its Subscription/Tenant transaction locks through provider delivery and final Outbox commit.
- Focused tests now prove both delivery kinds dead-letter before provider I/O when entitlement is inactive; shared-guard exception translation is also covered. Python 3.12: 17 passed; targeted Ruff and git diff --check passed.
- The existing PostgreSQL outbound-suspension module was invoked but all 5 cases skipped because its dedicated disposable database URL was not configured. No PostgreSQL, Staging, Production, or external provider was accessed. Exact-head CI must run the guarded PostgreSQL race tests before acceptance.
- This is one bounded worker/provider entitlement correction, not completion of the Notifications/Outbox matrix. Retry exhaustion, dead-letter ownership across the actor/hierarchy/delivery-kind matrix, revoked delegated context, content isolation, and provider-window permutations remain open. Immutable audit event/failure policy remains a separate decision gate; no speculative audit writes were added. Issue #1350 remains OPEN.


### PR #1463 Backend CI follow-up - fixture correction

- Initial exact-head Backend CI surfaced five failures in pre-existing PostgreSQL acceptance fixtures: two suspended-tenant assertions expected the old error text, two provider-window cases and the WhatsApp approval case lacked an active Vendor-issued CommercialLicense for their Customer tenant.
- Corrected lifecycle precedence in the shared adapter and amended only those fixtures to seed and remove their own Vendor/Customer/license rows. The worker unit fixtures now stub the outbound adapter; its real denial translation is tested separately.
- Focused Python 3.12 rerun: 17 passed. Targeted Ruff, py_compile for the adjusted PostgreSQL tests, and git diff --check passed. No local PostgreSQL/Provider was used. Exact-head CI must rerun before considering merge.


## 2026-11-21 - Outbox dispatcher ambiguous-acknowledgement protection

- Found and corrected a concurrency gap in the generic dispatcher exception path: after a broker .delay() error it previously reloaded Outbox with unlocked db.get() and unconditionally called mark_retry(). With an ambiguous broker acknowledgement, Email/WhatsApp workers can have already committed dispatched, dead, or uncertain; an unlocked retry could overwrite those terminal states and schedule a duplicate delivery.
- Dispatcher now performs a SELECT OutboxMessage ... FOR UPDATE after rollback and preserves terminal states (dispatched, dead, uncertain). It retains retry/backoff for rows that are still nonterminal; existing workflow broker-failure retry behavior is unchanged.
- Added parameterized Email/WhatsApp terminal-state race tests and a lock assertion. Python 3.12 focused Outbox/Email/WhatsApp suite: 27 passed; Ruff and git diff --check passed. No DB, broker or provider accessed locally.
- This is bounded unit-contract evidence only. Exact-head CI is required; full Notifications/Outbox actor ? hierarchy ? delivery-kind acceptance remains PARTIAL and Issue #1350 remains OPEN.


### PR #1464 merged - 2026-11-21

- The ambiguous broker acknowledgement terminal-state protection merged at b4e57a048dcc22c772552039cb40a2f61bacc1b3 after **17/17 exact-head checks** passed on ed36d567ef86bbf2a29b09e59507e1fbaa33bfb5. Issue #1350 remains OPEN; complete Notifications/Outbox matrix remains PARTIAL.
