

## Reseller-to-Customer file lifecycle follow-up - 2026-11-19

- Expanded the live delegated Portal scenario for a Reseller acting in its direct Customer context: upload, tenant-owned metadata read, streamed download/content verification, soft-delete, post-delete 404, and `file.uploaded`/`file.deleted` audit attribution to the Reseller actor under the effective Customer tenant.
- Added sibling-Reseller Customer file get/download/delete denial (404). The file storage backend is in-memory for this scenario; the uploaded object is explicitly deleted after assertions and the backend is discarded with the test.
- Focused PostgreSQL live API scenario: **1 passed in 30.68s** on disposable PostgreSQL 16 tmpfs. Container stopped and auto-removed.



## User lifecycle follow-up - 2026-11-19 (accepted invitation and status)

- Expanded the Reseller-to-direct-Customer live API scenario beyond invite/revoke: a second invitation is accepted through `/auth/invitations/accept`, the user appears in the tenant-scoped list with the fixed `Reseller Managed Member` role, status is deactivated/reactivated, and both Customer-tenant and Reseller-tenant audit rows are verified with the Reseller actor and target Customer metadata.
- Focused PostgreSQL live API test: **1 passed in 31.43s** on a dedicated tmpfs PostgreSQL 16 database; all invitation/user/role/audit fixtures are removed by the existing scenario cleanup. Container stopped and auto-removed.
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
# Multi-Vendor acceptance matrix audit — 2026-11-08

**Scope:** source/documentation/test audit against the approved architecture and delegated authorization contract.  
**Baseline:** `main` at `c92a9bdeb026ff488a8be5a1cb8764d6fcbbe5ce` (PR #1429 merge).  
**Tracker:** [Issue #1350](https://github.com/ijoolaie/AI-Employee/issues/1350).  
**Conclusion:** core tenant hierarchy, delegated portal context, several high-risk cross-tenant surfaces, and entitlement denial have meaningful merged test evidence. The complete acceptance matrix is **not yet demonstrated**. PR #1425 and #1429 expand complete authenticated file lifecycle coverage to Vendor→Reseller and Vendor→direct-Customer delegated contexts respectively; they do not yet prove every Reseller→Customer/sibling topology. This document records repository evidence, not production certification or a claim that every runtime path was manually exercised.

## Evidence classification

- **Covered:** an identifiable merged test or CI workflow asserts the relevant positive/negative boundary.
- **Partial:** some paths or topologies are tested, but the full actor/resource/action combinations or underlying storage/runtime boundary are not.
- **Not evidenced:** no dedicated test or source evidence was found in this audit for the required acceptance condition. This is a test-evidence gap, not proof of a vulnerability.

## Matrix

| Domain | Current evidence | Status | Remaining acceptance |
|---|---|---|---|
| Primary identity and portal-kind ceiling | `backend/tests/test_portal_access_contract.py`, `frontend/lib/portal-access.test.ts`, `frontend/e2e/portal-login.spec.ts`; #1409 and #1416 | **Covered for portal-kind routing/context rules** | Real browser acceptance with real authenticated Vendor/Reseller/Customer accounts and delegated target switching, beyond mocked login routing. |
| Vendor A/B independent roots | #1389–#1393; `backend/tests/test_portal_access_live_api.py` seeds two Vendor roots and verifies Vendor B cannot read Vendor A resources, audit rows, files, exports, invoices and dead letters | **Covered for tested surfaces** | Expand the same cross-root negative assertions to every resource family and every API operation, not just sampled endpoints. |
| Vendor → direct Reseller and direct Customer grants | `backend/tests/test_portal_access_live_api.py`; #1416–#1418 | **Covered for grant activation, user-bound listing, effective tenant context, revocation and entitlement denial** | Complete direct-child lifecycle and portal resource matrix for all actions. |
| Reseller → direct Customer grants | `backend/tests/test_portal_access_live_api.py`; #1416–#1418 | **Covered for grant activation, context, revocation and unentitled denial** | Expand all resource/action cases under multiple independent Reseller roots and sibling Customers. |
| Reseller-to-Reseller, Customer-to-parent, Vendor-to-grandchild escalation | `backend/tests/test_portal_access_live_api.py`; #1394–#1400 | **Covered for key negative portal/action-grant paths** | Add systematic ID enumeration, search, export and resource-level denial across every sibling/descendant combination. |
| Child provisioning and action-grant delegation | `backend/tests/test_tenant_action_grants_live_api.py`, `backend/tests/test_edition_action_permissions.py`; #1407/#1408 | **Partial-to-covered** | The live action-grant integration test exercises Vendor direct Customer provisioning and revocation; add symmetric Reseller direct Customer and Vendor direct Reseller grant/revoke/unauthorized-user scenarios under PostgreSQL. |
| Role creation/update/assignment delegation ceiling | `backend/app/api/v1/tenant_admin.py` exposes tenant role listing and user-role assignment; `_assert_roles_within_authority` protects assignment. No tenant-facing role create/update endpoint was found in the current tenant-admin, admin or edition-control routers. #1407 and `backend/tests/api/test_tenant_admin_role_boundary.py` cover assignment subset and Vendor-control-plane denial. | **Partial; role create/update not implemented in tenant-facing API** | Decide whether tenant-managed role CRUD is in the approved scope. If yes, add explicit create/update action permissions and apply the same permission-subset/delegation ceiling to both operations; test Vendor/Reseller/Customer boundaries, platform/global permissions and scope wildcards. |
| Tenant user lifecycle | #1395-#1398, #1407; live portal scenario exercises Reseller actor invite/revoke/accept/list/status/reactivation for its direct Customer, verifies dual-tenant audit attribution, and rejects a sibling Reseller's Customer. | **Covered for Reseller -> direct Customer; Vendor parent -> child user administration is not implemented** | No Vendor -> direct Customer or Vendor -> direct Reseller child-user routes exist. Decide parent-admin authority vs child-admin identity before implementation; retain exact-head CI evidence for the existing Reseller -> Customer scenario. |
| Files API and portal-context scoping | `backend/tests/test_portal_access_live_api.py`; `backend/scripts/e2e_tenant_rbac_verify.py`; #1403-#1406; #1420; #1425; #1429 | **Covered for upload/create, get, streamed download and soft-delete in Vendor -> Reseller, Vendor -> direct Customer and Reseller -> direct Customer delegated contexts; sibling Reseller Customer get/download/delete denied; foreign-tenant and revoked-context denial** | Retain exact-head CI and complete remaining hierarchy permutations only where a concrete actor/resource case remains missing. Current storage uses the configured local-disk abstraction; no presigned/direct object URL path exists. |
| Knowledge search and indexing | backend/scripts/e2e_tenant_rbac_verify.py and backend/tests/test_portal_access_live_api.py cover direct Customer and Vendor-to-Reseller contexts, tenant-owned indexing, sibling-file rejection, effective-tenant result filtering and immediate revoked-context denial; RAG filters Chunk, Document and active FileObject by tenant. | **Covered for tested contexts** | Complete remaining hierarchy permutations (Vendor A/B, multiple sibling Resellers, direct vs nested Customers) and exact-head CI. The API exposes bounded top_k rather than page pagination/arbitrary filters; no search result cache exists, so do not invent these features. |
| Privacy exports | `backend/tests/test_portal_access_live_api.py`; #1390 and #1391 | **Covered for sampled Vendor B and Customer portal own-vs-foreign export paths** | Extend to all export types, nested topology, async export jobs, artifact retrieval/download and revoked-context access. |
| Reports, invoices, usage, Test Center and operations | backend/tests/test_portal_access_live_api.py covers Vendor-to-Reseller and Reseller-to-Customer usage summary, invoices/detail/summary, owned invoice PDF export/download, report FileObject persistence/download, Test Center verification/artifacts and operations/dead-letter replay; added sibling Customer invoice PDF export denial assertion. Added delegated-context HTTP 200 assertions for /usage/optimization and /usage/cost-forecast in the same live-API scenario. | **Covered for sampled actions; CI pending** | Execute the expanded live API scenario on isolated CI and retain remaining actor/topology permutations. |
| Audit views | Portal live API verifies tenant-owned rows; Reseller Customer invitation and status scenarios verify actor/tenant attribution; file lifecycle verifies `file.uploaded`/`file.deleted` attribution; Lifecycle verifies parent/child deprovision metadata. | **Covered for sampled delegated read/write events** | Decide whether Outbox dispatch and AssignmentCommand terminal transitions need immutable ledger rows; separately define privacy/transaction semantics for denied authentication/permission/portal-context requests. Do not add speculative failure logging. |
| Notifications and outbox | test_customer_handoff_notification_outbox.py plus new tenant-settings lookup assertion; test_email_outbox_crash_safety.py; test_whatsapp_worker.py; Outbox claim/replay/replay-lock tests. Email/WhatsApp now revalidate commercial entitlement before provider I/O. | **Partial-to-covered for recipient, delivery fence and replay contracts** | Run exact-head isolated CI; complete remaining Vendor/Reseller/Customer recipient/content permutations and revoked portal-context cases across every delivery kind. |
| Background jobs and worker ownership | #1410?#1412; #1421; Run/Workflow/Outbox/AssignmentCommand worker contracts; Test Center now revalidates commercial entitlement from durable TestRun.tenant_id before QUEUED to RUNNING. | **Partial-to-covered for reviewed worker classes** | Exact-head isolated CI must execute the new Test Center suspended-tenant case and PostgreSQL lock races; finish delayed/revoked-context evidence for remaining worker classes without duplicating already-proven tenant bindings. |
| WebSocket/realtime | No WebSocket router exists; workflow event management uses HTTP/webhooks. Realtime is not an explicit requirement in Issue #1350's approved scope. | **Separate follow-on architecture decision; not an Issue #1350 acceptance blocker** | Do not implement in this track. If product scope is later extended, obtain a separate transport decision and define cross-tenant subscription/revocation acceptance. |
| Cache isolation | #1413?#1415 cover frontend identity transitions, QueryClient clearing and stale auth refresh protection. Backend scan found no response/data cache or cache decorator; Redis is used for IP rate limiting, tenant resource leases and fair scheduling. | **Not applicable to current backend source baseline** | Retain a future guard: if response/data caching is introduced, keys and invalidation must include effective tenant/context, portal switch, role/grant revocation and account switch. No cache subsystem/test is in scope now. |
| Entitlement and stale grant denial | #1417/#1418 portal grant activation/denial; tenant access tests for expired paid/Demo grants, paused subscription and existing portal-grant denial; outbound Email/WhatsApp now use the billing execution-entitlement guard; Test Center worker checks entitlement before start. | **Partial-to-covered for request and selected delayed-worker boundaries** | Execute isolated PostgreSQL concurrency evidence for Subscription-to-Tenant provider-window locking, Demo grant revocation/expiry and delayed Test Center execution; reconcile any other in-flight operation that can cross the entitlement boundary. |
| Legacy permission backfill | `backend/tests/test_vendor_permission_backfill_migration.py`; #1423 adds `backend/tests/test_vendor_permission_backfill_postgres.py`, executing the actual migration SQL against PostgreSQL TEMP tables in a rolled-back transaction | **Covered for migration SQL selection/idempotency semantics; partial for legacy-data rehearsal** | Reconcile a representative, isolated legacy snapshot including real role-sharing and historical tenant variants; record before/after grants and rollback evidence. No staging/production backfill without separate explicit review. |
| Portal UX and human acceptance | Login routing Playwright tests and frontend contract tests; #1416 portal shell implementation | **Partial** | Capture authenticated desktop/mobile journeys for Vendor, Reseller and Customer, delegated switch/return, empty/error/expired states and accessibility; require human visual/product approval. |

## Prioritized remaining work

1. **P0 ? Actor x Resource x Action completion:** close one documented missing route/action/topology at a time, prioritizing tenant-admin lifecycle, direct/nested Customer ownership and sibling-Reseller negative cases. Reuse the existing portal live-API matrix; no broad duplicate suite.
2. **P1 ? Exact-head isolated CI evidence:** execute the new Outbox entitlement/provider fence, Test Center suspended-tenant case, sibling invoice export denial and existing PostgreSQL race tests on the authorized isolated CI path.
3. **P1 ? Remaining report/analytics endpoints:** add delegated-context assertions for usage optimization and cost forecast only if source review confirms a gap; preserve tenant_id filters and report artifact ownership.
4. **P1 ? Audit attribution:** portal/action-grant create/revoke, delegated invitation create/revoke, portal-context activation, Test Center and workflow approval worker events are source-backed; verify denied-request audit policy (currently no failure event in auth/permission dependencies), remaining worker tenant/resource attribution and filtered audit views on isolated CI.
5. **Separate follow-on ? Realtime/WebSocket:** not in the approved Issue #1350 scope. Do not implement in this track; if scope is extended later, obtain a separate architecture decision.
6. **Gated ? Legacy migration rehearsal:** reconcile a representative isolated legacy snapshot and review resulting grants; no staging/production backfill without separate approval.
7. **Gated ? Human UX acceptance:** authenticated desktop/mobile journeys and explicit visual/product sign-off require separate approval.
8. **Future-only ? External object storage/cache:** no presigned URL or server response cache exists in the current source baseline. Add provider/cache-specific tests only if those capabilities are introduced.

## Safety and release boundary

- Keep [Issue #1350](https://github.com/ijoolaie/AI-Employee/issues/1350) OPEN until the matrix above is completed and evidence is attached.
- CI and synthetic/integration fixtures are not production certification or customer acceptance.
- Do not perform production/staging deployment, permission backfill, schema migration, persistent account mutation or payment activation without separate explicit approval.
- PostgreSQL integration tests may run without additional per-run approval only against a dedicated ephemeral database, isolated from Staging/Production and cleaned up after execution.

## Verified continuation checkpoint — 2026-11-18

- Active local branch and PR #1434 exact head match at fed62f56a75dd0f6de09c41e14a00506593d14c5. PR #1434 remains OPEN/unmerged. On this exact SHA, 20 GitHub Actions suites and one GitHub Advanced Security suite succeeded; Freebuff Web suite 117539141336 is queued and combined commit status is pending. Do not merge.
- PR #1433, the 2026-11-08 master handoff, remains OPEN/unmerged at 6c4dfe33fb84077553dc7b777379d9303aca7090. PR #1447 remains Draft and stacked on #1434. Issue #1350 remains OPEN.
- The local worktree had 71 changed paths before this documentation refresh (53 tracked, 18 untracked). This checkpoint adds five documentation paths: four tracked documentation updates (status, priorities, roadmap and this audit) and one new master handoff. Current total is 76 changed paths (57 tracked, 19 untracked). Preserve all; the implementation changes are not part of PR #1434's committed test-only scope.
- The acceptance matrix remains incomplete. Current source-backed priorities remain: notification/Outbox recipient and retry/dead-letter tenant isolation; worker enqueue, delayed execution and revocation; entitlement lifecycle against existing grants and in-flight work; then selected uncovered Actor × Resource × Action cases. Reuse existing implementation and evidence before adding tests.
- WebSocket/SSE remains not implemented and requires a separate architecture decision. Legacy permission backfill, human visual acceptance, persistent database changes, deployment and release promotion remain separately gated.
- Detailed current execution order and constraints: docs/current/AI_EMPLOYEE_MASTER_HANDOFF_2026-11-18.md. Current priorities and roadmap are reconciled in docs/00_START_HERE/CURRENT_PRIORITIES.md and docs/current/PRODUCTIZATION_ROADMAP.md.

### Focused local change reconciliation — 2026-11-18

The pre-existing local changes are not a single acceptance feature. Outbox/notification changes map to the partial Notifications and Outbox row; AssignmentCommand changes map conditionally to worker tenant provenance/idempotency; Agent/Run/Workflow fencing maps to delegated authority and execution-time worker validation; billing/edition lifecycle changes map to entitlement expiry/suspension; tenant-admin/invitation changes map partially to user lifecycle and delegation ceilings. General workforce/template/rollback/execution changes have no independent acceptance credit unless a specific matrix case is named. Preserve all existing edits; do not broaden this workstream.

Notification evidence already present:
- Handoff destination is queried from Tenant.settings using the conversation's tenant ID; enqueue carries the same tenant ID and a conversation-scoped dedupe key.
- Existing focused tests cover enqueue destination/dedupe, email dispatch, row serialization/uncertain provider outcomes, cross-tenant Agent proof rejection and delegated Agent revocation before SMTP; WhatsApp worker tests cover governance-proof failure and provider-boundary retry behavior.
- Current local Outbox changes address claim-time recovery lease, dead-letter replay retry budget/terminal metadata, tenant-scoped replay row lock, and AssignmentCommand outbox tenant binding.
- Remaining narrow evidence gap: directly assert the Tenant.settings query predicate uses the conversation-owning tenant. The broader matrix remains partial across all portal topologies and delivery kinds; this slice will not claim it complete.

## Evidence update — notification recipient ownership — 2026-11-18

- Added one focused test: test_handoff_notification_destination_lookup_is_scoped_to_conversation_tenant.
- The test calls the real Tenant.settings lookup, compiles the SQLAlchemy statement for PostgreSQL, and asserts the predicate targets tenants.id with the supplied conversation tenant UUID; it also verifies the configured destination returned by the lookup.
- Focused execution: 1 passed, 2 deselected. No database was used.
- This closes only the narrow recipient-lookup evidence gap. The broader Notifications/Outbox matrix remains PARTIAL because every Vendor/Reseller/Customer topology and delivery kind has not been demonstrated.
- No application behavior was changed in this slice.
- Next ordered domain: entitlement expiry/suspension for existing portal grants and already-enqueued/in-flight work. Existing tenant_access_service tests already cover expired paid periods, expired Demo grants, existing portal-grant denial after commercial access expires, and paused subscription denial; inspect these contracts and only address the remaining in-flight/background boundary.

## Next bounded acceptance gap — entitlement at irreversible worker side effects — 2026-11-18

Source inspection found a specific remaining gap in the Entitlement and stale-grant row: portal-context requests revalidate current commercial entitlement, and Run/Workflow admission revalidates entitlement, but the Email and WhatsApp workers currently revalidate only Tenant.status before the provider call. Their already-queued, in-flight outbox rows can therefore pass the lifecycle-status fence even after a paid period/Demo grant becomes invalid, unless the Agent-specific policy happens to reject them for another reason.

Bounded correction: reuse the existing billing execution-entitlement guard at the provider boundary, before the irreversible SMTP/WhatsApp call, while preserving the established Subscription → Tenant lock order and the existing uncertain-outcome behavior. Map a deterministic inactive commercial entitlement to the existing fail-closed TenantInactiveError path so the outbox row is dead-lettered before provider I/O. No new entitlement model or migration is in scope.

Verification is limited to the new helper contract and one focused worker-path contract. PostgreSQL lock-race verification remains on authorized isolated CI only; no local DB route will be used.

## Evidence update — commercial entitlement at outbound provider boundary — 2026-11-18

- Updated assert_tenant_active_for_side_effect to invoke the existing assert_run_execution_entitlement guard before locking Tenant for the provider window. This reuses the existing Subscription → Tenant admission order and does not add schema or new entitlement rules.
- ConflictError/NotFoundError from current commercial entitlement/admission are converted to TenantInactiveError. Existing Email and WhatsApp worker paths already treat TenantInactiveError as a deterministic pre-provider denial and dead-letter the row; no provider call is made.
- Preserved the pre-existing pending-public-signup invitation exclusion hunk in tenant_access_service.py while applying this change.
- Focused test: test_external_side_effect_fails_closed_when_current_entitlement_is_inactive — 1 passed, 13 deselected. git diff --check passed. No PostgreSQL test or persistent DB operation.
- Acceptance status: code path now fails closed for entitlement at outbound delivery time; PostgreSQL concurrency/lock serialization still requires the authorized isolated CI evidence. This does not complete the full Entitlement or Worker matrix.
- Next: inventory the remaining Celery/async task entry points against explicit tenant provenance and execution-time authority; select only the next documented uncovered worker class.

## Worker inventory finding — Test Center delayed execution — 2026-11-18

The Celery inventory shows most workflow/run/outbox tasks derive tenant ownership from a durable tenant-scoped row or receive tenant_id explicitly. Test Center execute_run is a specific exception worth closing: its task accepts only run_id, then correctly binds TestDefinition.tenant_id to TestRun.tenant_id, but it does not revalidate the tenant's current active/commercial entitlement before transitioning QUEUED → RUNNING. A task queued before suspension/expiry can therefore begin afterward.

Bounded correction: after resolving the TestRun and tenant-bound enabled definition, call the existing billing_service.assert_run_execution_entitlement with the TestRun's authoritative tenant_id before start_run. Do not trust caller-supplied tenant metadata, change the task signature, or alter the Test Center ownership model. Add one PostgreSQL integration assertion for suspended-tenant delayed execution; do not run it locally due the database safety boundary.

## Evidence update — Test Center delayed execution — 2026-11-18

- Test Center worker now calls the existing billing execution-entitlement guard using the TestRun's durable tenant_id after validating the enabled TestDefinition belongs to that same tenant and before transitioning the run to RUNNING.
- Added one PostgreSQL integration case: a queued TestRun for a suspended tenant must remain QUEUED and must not receive started_at.
- Focused Ruff check passed for the touched tenant-access, Test Center, and notification files; git diff --check passed.
- The new PostgreSQL integration case was intentionally not run locally. It must run in the authorized isolated CI database path. No DB migration or persistent data operation occurred.
- Worker inventory status: explicit tenant arguments or durable row-derived tenant ownership were found for the Celery tasks reviewed; event/schedule/Run/Workflow tasks already use tenant-scoped durable rows and existing admission/dispatch guards. Test Center delayed execution was the identified missing active/commercial admission check and is now corrected locally. The full worker matrix still needs exact-head CI evidence.
- Next: continue with the source-backed Cache isolation and Reports/Exports gaps; do not expand into unrelated workforce/template task behavior.

## Cache isolation source verification — 2026-11-18

A targeted backend source inventory found no tenant-scoped server response/data cache implementation, cache decorator, cachetools/aiocache/fastapi-cache integration, or Redis GET/SET response cache. Current Redis usage is for IP-bucket rate limiting, tenant resource concurrency leases and tenant-fair scheduling; these are coordination/rate-limit structures, not cached tenant response data. Frontend QueryClient identity clearing is already evidenced by #1413–#1415.

Decision: do not invent a cache invalidation subsystem or add cache tests for a cache that does not exist. Keep a release guard: if server response/data caching is introduced, keys must include actor/effective tenant/context and invalidation must cover portal switch, grant revocation, role change and account switch. For the current source baseline, the backend cache-isolation item is NOT APPLICABLE (no server data cache found); frontend identity-transition coverage remains covered by existing PR evidence. Move to the remaining report/export artifact topology gaps.

## Report/export matrix refinement — 2026-11-18

Source review of the existing portal live-API acceptance test confirms meaningful evidence already exists for:
- Vendor → Reseller context: tenant-scoped usage summary, invoice list/detail/summary, Test Center verification record and artifacts, operations metrics/dead letters/replay, privacy export, and report artifacts saved as tenant-owned FileObjects and downloaded through the Files API.
- Reseller → Customer context: invoice list/detail/PDF export and download, privacy export, report artifact ownership/download, run artifact list/download, and denial after grant revocation.
- Sibling/cross-Vendor negative cases: invoice detail, Test Center verification, operations/dead-letter replay, privacy exports, report source-file access and file/artifact retrieval.

One concrete missing assertion in the Reseller → Customer path: a sibling Customer invoice PDF export is not explicitly denied (sibling invoice detail is denied; the export route is separately exercised for the owned Customer and after grant revocation). Add that one negative action assertion only. Do not duplicate the existing report/usage/operations coverage or expand into another broad live API test.

## Evidence update — sibling invoice PDF export denial — 2026-11-18

- Added one negative assertion to the existing PostgreSQL portal acceptance scenario: a Reseller-to-Customer portal context cannot export a sibling Customer invoice PDF (expected 404), complementing the existing sibling invoice detail denial.
- Focused Ruff check passed for the modified portal acceptance test and the recently changed entitlement worker/service files; git diff --check passed.
- PostgreSQL integration scenario intentionally not run locally. Exact-head isolated CI is required to convert this source/test change into executed acceptance evidence.
- No production or persistent database was accessed.

## Knowledge search/indexing source reconciliation - 2026-11-18

Existing portal live-API acceptance covers direct Customer and Vendor-to-Reseller contexts: tenant-owned indexing, sibling file rejection, search results excluding sibling/foreign tenant markers, and 403 after grant revocation. RAG search filters KnowledgeChunk, KnowledgeDocument and active FileObject by effective tenant. API supports bounded top_k (1..20), not page pagination or arbitrary filters; no result cache exists. Do not invent tests for nonexistent features. Search/index isolation is covered for the exercised contexts; the full Actor x Resource x Action matrix remains partial pending remaining hierarchy permutations and authorized CI evidence.

## Worktree status refresh - 2026-11-18

Current worktree is 80 changed paths (61 tracked, 19 untracked), with no staged changes. Four additional tracked paths were changed in the entitlement and report/export slices since the 76-path checkpoint. Preserve all existing edits. Branch remains test/knowledge-revoked-portal-context-20261108 at fed62f56a75dd0f6de09c41e14a00506593d14c5. No commit/push/merge/deploy or database mutation; local changes are not part of PR #1434.

## Next actor/resource/action gap — Reseller-managed Customer users — 2026-11-18

The tenant user lifecycle source review found a specific acceptance gap: reseller_customer_users.py exposes direct-Customer user list/invite/revoke/status operations with direct-child checks, a fixed least-privilege Customer Member role, accepted-invitation activation and audit attribution. Unit tests cover direct-child/inactive-child boundaries and the shared invitation service covers token hashing, acceptance, replay/revoke/expiry. The existing portal live-API matrix does not execute these routes with a real Reseller actor against its own Customer or a sibling Reseller's Customer.

Bounded acceptance addition: in the existing portal live-API scenario, grant the Reseller fixture only the required reseller.customer.manage action, invite a user into its direct Customer, verify a request against a sibling Reseller's Customer is denied, and revoke the owned invitation. Reuse the existing fixture and invitation service; no new service behavior or broad test suite.


## Evidence update ? Reseller-managed Customer user lifecycle ? 2026-11-18

- Extended the existing portal live-API fixture with a Customer owned by a sibling Reseller and granted the Reseller Admin only the explicit reseller.customer.manage action used by the user-management route.
- Added a positive invitation and revoke flow for the Reseller's own direct Customer, plus a negative invitation attempt against the sibling Reseller's Customer (expected 403).
- Reused the existing invitation service; no application behavior or schema changed. Focused Ruff and git diff --check passed.
- PostgreSQL live API scenario was not run locally; isolated CI execution remains required.

## Extension of the same user-lifecycle acceptance case — audit attribution

Extend the existing Reseller Customer invitation scenario (not a separate test) to verify the created/revoked audit rows retain the Reseller actor tenant and actor user while recording the target Customer tenant in metadata. This is the smallest evidence addition for the audit-attribution row; no general audit export/filter suite is added here.


## Evidence update ? delegated audit attribution ? 2026-11-18

The Reseller-managed Customer user lifecycle scenario now checks both invitation-created and invitation-revoked audit rows. Assertions require the Reseller actor tenant and actor user on the audit envelope and the target Customer tenant in metadata. Ruff passed; the PostgreSQL scenario remains CI-only.

## Worker audit-attribution source reconciliation - 2026-11-19

Reviewed the current worktree source for run_worker, run_recovery_worker, outbox_worker, assignment_command_worker, workflow_trigger_worker, and test_center_worker, including their directly invoked services and durable models.

| Worker/path | Source-backed evidence | Attribution fields / status |
|---|---|---|
| Run execution | run_service.py records run.created, knowledge.retrieved, memory.retrieved, tool.call, run.completed, and run.failed; run_execution_fence.py records run.execution_entitlement_denied. run_recovery.py records run.execution_recovered. | Tenant and Run resource are recorded; service-level user/system actor semantics are used. Worker logs are operational telemetry, not the audit source. |
| Run recovery sweep | run_recovery.py::recover_stale_run_execution writes run.execution_recovered in the same DB session as the terminal recovery transition. | actor_type=system, tenant_id, resource_type=run, resource_id, request_id, failure status and bounded recovery metadata. |
| Outbox dispatch | outbox_worker.py claims, dispatches, retries and dead-letters OutboxMessage; metrics/spans/logs expose kind/status/attempts. | Durable Outbox row carries tenant_id, kind, payload and lifecycle state, but no actor identity and no AuditLog write in this worker/service path. This is operational dispatch evidence, not immutable audit attribution. |
| Assignment command | assignment_command_worker.py validates Tenant, Run provenance, active actor, Agent, delegation and WorkItem before execution. AssignmentCommand persists tenant_id, run_id, actor_user_id, agent_instance_id, delegation_id, work_item_id, request hash and command lifecycle/result. | Strong durable command provenance exists, but no independent AuditLog event for command success/failure was found in the worker path. This is a separate command record, not the hash-chained audit ledger. |
| Workflow trigger / approval sweeps | workflow_trigger_worker.py records workflow.approval.expired and workflow.run.timed_out. Schedule/event dispatch creates tenant-bound WorkflowRuns and Outbox rows. | Expiry/timeout entries use actor_type=system, tenant_id and approval/WorkflowRun resource IDs. Dispatch itself is represented by WorkflowRun/Outbox state, not a separate AuditLog event in this file. |
| Test Center | test_center_worker.py records test_run.expired, test_run.started, and test_run.passed. | actor_type=system, actor_id=None, tenant_id, TestRun resource ID and source/correlation metadata. |

Decision: do not add speculative AuditLog writes to Outbox or AssignmentCommand in this pass. Both already have durable operational state, while the required distinction between operational event history and immutable audit events, actor attribution, failure semantics, and transaction coupling has not been specified. This is a product/security policy decision, not evidence that tenant isolation is absent.

No worker production code was changed in this source-reconciliation slice. Failure-audit policy for authorization/portal-context denials remains separately open. Exact-head PostgreSQL CI and full acceptance evidence remain pending; no local PostgreSQL tests were run.

## Audit read-surface source reconciliation - 2026-11-19

The read paths were checked separately from audit-write attribution:

- GET /operations/audit-logs requires AuditReadContext (audit.read) and passes ctx.tenant_id to audit_service.list_logs. The service always filters AuditLog.tenant_id, supports action/status filters, and clamps the requested limit to 1..200.
- Portal-context policy explicitly permits /api/v1/operations/audit-logs. Existing portal live-API assertions for Vendor-to-Reseller delegated contexts prove the effective target tenant's seeded audit action is returned while sibling/foreign tenant markers are absent. The live PostgreSQL test remains unexecuted locally; this is source plus authored test evidence, not executed CI evidence.
- GET /runs/{run_id}/artifacts first verifies Run ownership and then filters tool.call audit rows by both tenant_id and Run resource identity.
- GET /work-items/{work_item_id}/history requires audit.read, verifies WorkItem ownership, and filters by tenant_id plus WorkItem resource identity.
- These paths provide source-backed tenant/resource scoping for the exercised read surfaces. Do not generalize this to every actor/topology or claim exact-head CI completion. No audit read code change is indicated by this review.

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

## Reseller action-grant positive-path gap confirmation - 2026-11-19

- Rechecked `tenant_action_grants.py`, `tenant_action_grant_service.py`, `edition_control.py`, `edition_deps.py`, `test_tenant_action_grants_live_api.py`, `test_edition_action_permissions.py` and the live portal API scenario.
- The API implements Vendor and Reseller create/list/revoke routes. The shared service locks the granting Tenant, enforces the edition-specific allowlist, requires the grantor to hold the action directly in a tenant-local role, locks and validates an active target user in that same tenant, and tenant-scopes grant revocation.
- Existing PostgreSQL live positive-path test proves only Vendor `vendor.customer.create` grant -> direct Customer provisioning -> revoke -> denial. Existing unit tests cover Reseller permission dependency semantics, and live portal test covers Customer denial against both grant APIs; neither is a positive Reseller grant lifecycle.
- Confirmed bounded acceptance gap: no PostgreSQL live test currently demonstrates a Reseller administrator granting `reseller.customer.create` to a same-tenant member, that member provisioning only a direct Customer, revocation denying subsequent provisioning, and rejection of a target user belonging to a different Reseller. Vendor-to-Reseller positive grant/provision/revoke is also not demonstrated.
- No implementation defect was established in the shared service or route definitions. Do not alter production code for a test-evidence gap. Next bounded step: extend the existing dedicated `support_test` live-API acceptance with the Reseller positive/negative sequence, then separately add the Vendor-to-Reseller symmetry if still required by the approved matrix. Execution remains gated; do not run the PostgreSQL test without explicit authorization.

## Reseller action-grant positive lifecycle scenario authored - 2026-11-19

`backend/tests/test_tenant_action_grants_live_api.py` now includes a PostgreSQL-backed API scenario proving (when executed) same-tenant Reseller member grant, direct Customer provisioning under that Reseller, grant revocation and subsequent denial, plus sibling-Reseller target rejection. This closes the test-definition gap only; it is not runtime evidence until the isolated PostgreSQL test executes successfully. Vendor-to-Reseller positive grant/provision/revoke remains separately unproven.

## Vendor action-grant positive lifecycle scenario authored - 2026-11-19

`backend/tests/test_tenant_action_grants_live_api.py` now includes the Vendor-to-direct-Reseller lifecycle: same-tenant member grant of `vendor.reseller.create`, direct Reseller creation under the granting Vendor, revoke and subsequent denial, plus rejection of a sibling-Vendor target user. The existing Vendor-to-Customer and newly authored Reseller-to-Customer paths remain distinct. This is test-definition coverage only; execution is still gated. No application code changed.

## Suspend/Resume/Deprovision acceptance matrix audit - 2026-11-19

| Actor | Resource boundary | Actions | Role/action permission | API-key scope | Live API lifecycle evidence |
|---|---|---|---|---|---|
| Vendor | Direct Reseller only | Suspend / Resume / Deprovision | `vendor.reseller.manage` | `edition.vendor.resellers.manage` | Not found in reviewed live API tests |
| Vendor | Direct Customer only | Suspend / Resume / Deprovision | `vendor.customer.manage` | `edition.vendor.customers.manage` | Not found in reviewed live API tests |
| Reseller | Direct Customer only | Suspend / Resume / Deprovision | `reseller.customer.manage` | `edition.reseller.customers.manage` | Not found in reviewed live API tests |

Source review confirms parent-first locking, child row locking, direct-child + kind revalidation, parent-active requirement for resume, terminal deprovision, rejection of parent deprovision while children remain active/suspended, user deactivation, retained tenant data, and parent-attributed audit. No hard-delete/archive Edition route was identified. Existing unit/source-contract coverage is not equivalent to executed live API acceptance.

**Disposition:** no Production defect established and no Production change made. Add focused PostgreSQL live-API coverage for positive transitions, invalid transitions, active-child parent deprovision rejection, and sibling/wrong-kind denial. Tests have not run; exact-head isolated PostgreSQL CI remains behind explicit authorization.


## Lifecycle live API scenario authored - 2026-11-19

`backend/tests/test_edition_live_api_access.py::test_vendor_reseller_lifecycle_routes_enforce_direct_child_boundaries` now defines a PostgreSQL-backed API scenario covering all three Actor x Resource paths (Vendor->direct Reseller, Vendor->direct Customer, Reseller->direct Customer), positive suspend/resume/deprovision, wrong-kind and sibling-child rejection, active-child parent-deprovision rejection, terminal reactivation rejection, and deprovision user deactivation. This upgrades the matrix from source/unit-only coverage to authored live-test coverage, not executed runtime evidence. Execution remains gated by explicit authorization for isolated PostgreSQL CI.


### Child tenant lifecycle API-key scope contract - 2026-11-19

- Verified all nine suspend/resume/deprovision route templates map to their intended Vendor or Reseller manage scope and that each scope is allowlisted for the correct tenant kind.
- Added parameterized contract coverage for matching-scope acceptance and wrong-scope 403 rejection across Vendor→Reseller, Vendor→Customer, and Reseller→Customer routes; added explicit Bearer-context bypass coverage.
- Test authored only; not executed. Existing PostgreSQL-backed lifecycle scenario remains authored but unexecuted. No Production code changed.

### Lifecycle negative-state coverage - 2026-11-19

- Extended the PostgreSQL-backed live API scenario to suspend a Reseller parent while its Customer child is suspended, assert child resume is rejected with 409, then resume the parent and verify child resume succeeds.
- This directly exercises the service's parent-active guard through the route; test remains authored but unexecuted. No Production code changed.

### Deprovision audit attribution evidence - 2026-11-19

- Extended the live lifecycle scenario to verify deprovision audit rows are attributed to the managing parent tenant and authenticated actor for both Reseller→Customer and Vendor→Reseller transitions, including child_tenant_id metadata.
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
- Ran DB-free acceptance contracts against the repository's dependency-complete Python 3.12 container with the backend mount read-only: `test_edition_api_key_scope_contract.py` and `test_vendor_permission_backfill_migration.py` — **17 passed**. Pytest emitted only a cache warning because the source mount was intentionally read-only; test results were successful and no repository artifacts were written by the runner.
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
### Vendor delegated user-management resolver — implementation checkpoint (2026-11-20)
- Added `backend/app/services/tenant_user_management_service.py` with a DB-backed resolver that loads actor, target, parent, and (for nested Customer targets) grandparent from persisted `tenants` rows. It rejects inactive tenants, non-root Vendor actors, malformed Reseller ancestry, non-Customer actors, self-targeting, sibling/foreign ancestry, and unsupported hierarchy edges.
- The resolver is intentionally separate from `edition_service.assert_can_access`; no global edition access policy was widened.
- Added `backend/tests/test_tenant_user_management_service.py`; focused pure-policy tests: **8 passed**. `git diff --check` passed.
- Not yet integrated into HTTP routes; no invitation/list/revoke/status/role API behavior changed. No PostgreSQL resolver integration test has run yet.
- An attempted combined run with `test_edition_boundaries.py` had 18 passes and one environment/import failure because the local interpreter is Python 3.10 and an existing module imports `enum.StrEnum` (Python 3.11+); this is not evidence of a product regression. The first attempt also exposed an incorrect test expectation (a Reseller is allowed to manage all its own direct Customers); the test was corrected to use a Customer under a different Reseller.

### Vendor descendant user read APIs — implementation checkpoint (2026-11-20)
- Added `backend/app/api/v1/vendor_tenant_users.py` with target-tenant-scoped GET endpoints for tenant-local users and assignable roles, using the DB-backed ancestry resolver. The route only exposes users whose `User.tenant_id` matches the resolved target; role listing is limited to target-tenant roles and system roles.
- Registered the router and added a dedicated API-key scope `edition.vendor.users.read` with explicit route-template mappings for both GET routes. The API-key scope contract remains fail-closed for unmapped routes.
- Authorization requires the Vendor administrator context plus the target-kind read permission (`vendor.reseller.read` or `vendor.customer.read`). The resolver enforces active target and persisted Vendor subtree ancestry.
- Validation: Python compileall succeeded for changed runtime modules; focused resolver + API-key scope tests: **23 passed**.
- Write operations (invite/revoke/status/role assignment) are not yet exposed for Vendor; no DB-backed live API test has run for these new endpoints. No PostgreSQL or persistent database was touched.

### Validation correction (2026-11-20)
- After adding the new Vendor users read scope to the Vendor API-key allowlist, the final focused run completed with **25 passed** across `test_tenant_user_management_service.py` and `test_edition_api_key_scope_contract.py`; compileall and `git diff --check` also succeeded.

## 2026-11-20 - Vendor delegated user-write evidence
| Capability | Evidence/status |
|---|---|
| Vendor list users/roles in own subtree | Implemented; resolver + scope tests previously passed |
| Vendor invite child-tenant user | Implemented; shared secure invitation service; live PostgreSQL route test pending |
| Vendor revoke child-tenant invitation | Implemented; tenant-scoped shared service; live PostgreSQL route test pending |
| Vendor activate/deactivate child-tenant user | Implemented; last-admin/entitlement/token-version controls; live PostgreSQL route test pending |
| Vendor assign/remove child-tenant roles | Open; role delegation ceiling/system-role policy needs source-contract reconciliation |
| API-key isolation | Dedicated `edition.vendor.users.manage`; focused contract suite included in 28-pass run |

## 2026-11-20 - Vendor delegated role write evidence
| Capability | Evidence/status |
|---|---|
| Vendor assign/remove target-local roles | Implemented as role-set replacement; target-local and system roles only; last-admin protection; live PostgreSQL acceptance pending |
| Permission ceiling | Reuses `_assert_roles_within_authority`; rejects any permission outside actor's explicit authority |
| Platform/Vendor privilege escalation | Explicitly rejects `platform.*`, `vendor.*`, Platform Admin, and Superuser role grants; policy tests included in 74-pass run |
| API-key role-write scope | Exact POST route mapped to `edition.vendor.users.manage`; contract test included in 74-pass run |

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
- Focused DB-free contracts passed on Python 3.12: AssignmentCommand service/worker contracts, Outbox lease/replay contracts, WorkItem locking, and workflow timeout reconciliation — **30 passed in 1.70s**. Full backend Ruff (`app` + `tests`) passed. `git diff --check` passed (only pre-existing LF/CRLF warnings).
- PostgreSQL race/recovery tests in this slice are explicitly CI-only and were not locally executed; their CI guards require `CI=true` and a dedicated loopback `support_test` database. No guard was bypassed. The only running Docker services remain the pre-existing Staging PostgreSQL/Redis containers on ports 15434/16379.
- Remaining acceptance gates are unchanged: approved immutable-audit/failure-event policy; sanitized historical Vendor permission-backfill snapshot; human visual acceptance of the distinct portals; and completion of the documented Actor x Resource x Action gaps. The Vendor descendant user-administration slice remains separately accepted by its disposable PostgreSQL live test and exact-head CI evidence; this does not close Issue #1350.
## 2026-11-20 - Notification destination tenant-predicate evidence

- Revisited the exact remaining narrow gap named by the acceptance matrix: tenant handoff notification destination lookup must read `Tenant.settings` for the conversation-owning tenant, not an actor/portal-context or caller-selected tenant.
- Executed the existing focused regression `tests/services/test_customer_handoff_notification_outbox.py`: **3 passed in 0.89s** on Python 3.12. The specific query-contract case compiles the SQL with the PostgreSQL dialect and asserts the `tenants.id` predicate and the conversation tenant UUID are bound in the statement.
- This closes the narrow query-predicate evidence gap for the inspected handoff destination lookup only. It does not complete the broader Notifications/Outbox actor × hierarchy × delivery-kind matrix. The test and related Outbox implementation remain part of the preserved local in-progress worktree; they were not included in the documentation-only GitHub commit.
- No production code was changed in this verification step, and no database was used. Continue only with the next documented uncovered notification/worker case; do not infer full matrix acceptance from this focused contract.
## 2026-11-20 - Notification and Outbox delivery-contract verification

- Continued the documented Notifications/Outbox actor × hierarchy × delivery-kind review with the existing focused delivery contracts; no production code or test definitions were changed in this verification slice.
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
## 2026-11-20 - Test Center worker tenant binding / Report Employee attribution

- Test Center API now dispatches both Run ID and validated tenant ID; worker requires both UUIDs and queries by `(TestRun.id, TestRun.tenant_id)`. Wrong-tenant dispatch is 404/fail-closed and does not transition the Run; matching tenant completes successfully.
- PostgreSQL 16 disposable tmpfs, Alembic `w33_tenant_action_grants`: full Test Center integration module **5 passed in 3.74s**. Focused worker guards + Report Employee actor propagation **4 passed in 2.79s**. Ruff and `git diff --check` passed.
- ToolRegistry `analyze_dataset` now forwards its Run actor ID to report generation; focused test verifies tenant/actor/file propagation. `analyze_document` remains unchanged.
- Remaining gaps: complete Test Center task/sweeper lifecycle and persisted Agent Run/outbox/worker delegated portal acceptance remain open.
