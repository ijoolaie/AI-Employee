# AI-Employee Master Handoff — 2026-11-08

**Repository:** `ijoolaie/AI-Employee`
**Snapshot date:** 2026-11-09 (UTC; refreshed acceptance evidence)
**Main baseline observed:** `d943ec2cffd75ea88daebdf02c7b6df413d3f2f6`
**Architecture / acceptance tracker:** [Issue #1350](https://github.com/ijoolaie/AI-Employee/issues/1350)

> This is the current checkpoint, not a release certification. Refresh exact SHAs and live CI before every subsequent handoff or merge decision.

## 2026-11-09 live refresh ? supersedes stale CI and PR #1434 notes below

- PR #1428 exact head ba65814d05dd624d6095d0ce5a8da1be761c0bcf: 9 GitHub Actions suites and GitHub Advanced Security completed successfully; Freebuff suite 115101840461 remains queued.
- PR #1431 exact head c32576fec6c11d0fbd5bd79de98729818a35118d: 9 GitHub Actions suites and GitHub Advanced Security completed successfully; Freebuff suite 115085202766 remains queued.
- PR #1432 exact head 5102b645511ca01083af0bd97db3645d1b3c2f24: 9 GitHub Actions suites and GitHub Advanced Security completed successfully; Freebuff suite 115094879907 remains queued.
- PR #1433 exact head 2be178619e09140e115c582ef90dd027467c55fc: 2 GitHub Actions suites and GitHub Advanced Security completed successfully; Freebuff suite 115294197191 remains queued. PR remains open.
- PR #1434 exact head e0cc44938a39ff5cf8d9d3699bd98d1d717b1190: one GitHub Actions suite succeeded, eight GitHub Actions suites are in progress, and Freebuff suite 115300358193 is queued. Review threads and submitted reviews were empty at the latest inspection. PR remains open.
- PR #1434 Run-artifact delegated portal extension: the PostgreSQL-backed Reseller?Customer integration now seeds Customer, parent-Reseller and sibling-Customer Runs plus tenant-scoped audit pointers and storage objects. Authenticated Customer portal assertions cover own artifact listing and download, parent/sibling Run denial (404), sibling artifact download denial (404), and immediate 403 for list/download after grant revocation. The test storage backend implements tenant-prefix listing and existence checks, so the real authenticated Run artifact API routes are exercised.
- Local PR #1434 verification on the updated worktree: 82 targeted Run-artifact, Report Employee, ToolRegistry and Invoice tests passed; py_compile, Ruff and git diff --check passed. The PostgreSQL-backed portal integration was not run locally because both SUPPORT_TEST_DATABASE_URL and DATABASE_URL are absent; exact-head CI must execute it.
- No PR was merged. No Production/Staging deployment, migration, persistent-data mutation or payment activation occurred. No supported Freebuff dispatch/retry action is available; queued Freebuff suites are blockers, not passes.
- Issue #1350 received progress comment 6733168750. It remains open.
- Further PR #1434 work after the preceding refresh: the customer-handoff PostgreSQL integration now exercises two distinct tenant notification destinations via the real public handoff path and asserts that each tenant's outbox recipient/body identifiers remain tenant-local. The Test Center PostgreSQL integration adds a deliberately cross-tenant Run?TestDefinition reference and verifies the worker rejects it before starting the Run. Commercial license unit coverage now asserts an expired active license is marked expired, returns no active license, and the lookup is tenant-scoped; execution fails closed without an active license. PR #1434 exact head is now 65a941d766ba086ae68fb4da0a43305c529f68fa.
- Local verification for these additions: 15 passed and 2 PostgreSQL tests skipped (handoff/outbox + worker safety); 55 Test Center/worker tests passed; 31 entitlement/subscription/execution-fence tests passed without warnings after isolating the test's tenant-access dependency. py_compile, Ruff and diff checks passed. The newly added PostgreSQL assertions await CI because no dedicated local DB URL is configured.
- Server-cache audit refinement: no generic application cache read/write layer or tenant cache-key API was found under backend/app. Redis use found is rate limiting, tenant fair scheduling, and tenant resource leases; do not describe this as a proven cache-key isolation failure. Realtime/WebSocket subscription isolation remains not implemented/not evidenced.
- Latest exact-head PR #1434 suite snapshot: Freebuff suite 115303403012 queued; nine GitHub Actions suites queued/pending. Latest PR #1433 snapshot at dd2caf2d6218c16c83f28049640a4e24cd0b826d: Freebuff 115301089132 queued; two GitHub Actions suites and GitHub Advanced Security completed successfully. PR #1433 is being updated by this handoff refresh, so its next head and CI must be fetched after push.


## 1. Operating decisions and boundaries

- The user has approved continuing the multi-tenant acceptance work and provided human/UX sign-off recorded on Issue #1350.
- That sign-off is **not** authorization for Production/Staging deployment, persistent database migration, account mutation, payment activation, or destructive operations. Those require separate explicit authorization.
- Keep Issue #1350 open until the complete acceptance matrix and final evidence are complete.
- Preserve the dirty primary checkout; use isolated worktrees for local code work. Do not reset, clean, stash, switch, rebase, or modify the primary checkout.
- Never merge without all required checks green on the exact PR head SHA, no unresolved review threads, and clean review state. Do not bypass required checks.
- If a required external check remains queued and no supported retry/dispatch action is available, record the blocker; do not invent a rerun.
- Do not claim Production readiness from CI or synthetic acceptance evidence.

## 2. Current open acceptance PRs

The acceptance and handoff PRs below were observed open and unmerged against the main baseline above. Exact heads:

| PR | Purpose | Exact head | State at snapshot |
|---|---|---|---|
| [#1428](https://github.com/ijoolaie/AI-Employee/pull/1428) | Direct and nested Customer file lifecycle | `ba65814d05dd624d6095d0ce5a8da1be761c0bcf` | Open; 10 GitHub Actions/security check suites succeeded; Freebuff suite `115101840461` was queued with zero check runs at last detailed suite inspection |
| [#1431](https://github.com/ijoolaie/AI-Employee/pull/1431) | Delegated Reseller→Customer file lifecycle | `c32576fec6c11d0fbd5bd79de98729818a35118d` | Open; 10 suites succeeded; Freebuff suite `115085202766` was queued with zero check runs at last detailed suite inspection |
| [#1432](https://github.com/ijoolaie/AI-Employee/pull/1432) | Sibling Customer file isolation | `5102b645511ca01083af0bd97db3645d1b3c2f24` | Open; 10 suites succeeded; Freebuff suite `115094879907` was queued with zero check runs at last detailed suite inspection |
| [#1433](https://github.com/ijoolaie/AI-Employee/pull/1433) | Refresh dated master handoff | 2be178619e09140e115c582ef90dd027467c55fc | Open; 2 GitHub Actions suites and CodeQL succeeded; Freebuff suite 115294197191 queued |
| [#1434](https://github.com/ijoolaie/AI-Employee/pull/1434) | Delegated Knowledge, Report Employee, Invoice PDF, Run artifact, notification recipient and worker isolation/revocation | 65a941d766ba086ae68fb4da0a43305c529f68fa | Open; 9 GitHub Actions suites queued/pending; Freebuff suite 115303403012 queued; reviews clean |

For each PR, the listed successful checks included Backend/CI, Architecture Guard, CodeQL, DAST, infrastructure validation, recovery validation, semantic E2E, public-widget acceptance, W21 and other applicable workflows. Combined commit status had no legacy status entries. Review threads were empty at the last recorded review-thread inspection. Re-fetch current suite/check-run and review state before acting; this snapshot is not a live status feed.

### Acceptance details

- **#1428:** adds nested Customer upload, metadata GET, successful download with byte-for-byte content assertion, denial from Reseller home context (404), soft-delete, and post-delete download denial (404). Existing stronger direct Vendor→Customer lifecycle coverage from main was retained.
- **#1431:** delegated Reseller→Customer file upload/get/download/delete lifecycle with home-context denial.
- **#1432:** a sibling Customer's file is absent from Customer A's list and GET/download/DELETE all return 404.
- **#1434:** extends the PostgreSQL-backed Vendor-to-Reseller portal grant integration test so Knowledge search returns 403 immediately after grant revocation. It also adds Run-artifact API tests proving cross-tenant Run ownership is denied before artifact lookup on download and an audit pointer from another Run cannot be downloaded (404). Local verification: py_compile, Ruff, and git diff --check origin/main...HEAD passed; the Run-artifact API tests passed (7 tests). Exact-head CI on the prior SHA provisioned isolated PostgreSQL and Redis; the portal revocation integration test and all seven Run-artifact API tests passed; full backend suite: 1,965 passed, 1 deselected, 28 warnings.
- **#1434 Invoice PDF follow-up (baac199f):** adds delegated Reseller-to-Customer invoice isolation to the PostgreSQL portal integration test. Customer invoice listing is restricted to its own invoice; parent Reseller and sibling invoice reads return 404; Customer invoice PDF export and subsequent Files API download succeed; parent invoice export returns 404; an already-issued Customer portal token receives 403 for invoice export immediately after grant revocation. Local py_compile, Ruff and diff checks passed; report/tool/invoice service test group passed (75). New exact-head checks had not yet appeared at refresh; Freebuff suite 115294066243 was queued. PostgreSQL-backed portal integration remains CI-only because no dedicated local DB URL is configured.
- **#1434 Report Employee follow-up (3912126b):** extends the PostgreSQL-backed delegated Reseller-to-Customer portal integration test to execute the real ToolRegistry analyze_dataset handler under the effective Customer tenant. It verifies PDF/Excel/chart FileObjects are Customer-owned, appear in the Customer Files listing, PDF and XLSX download through the authenticated Customer portal token, and analysis rejects parent Reseller and sibling-tenant source files. Entitlement is stubbed at the license-service boundary to isolate tenant ownership; this test does not certify commercial entitlement behavior. Local py_compile, Ruff and diff checks passed; report service/idempotency/tool-registry unit tests passed (59). PostgreSQL portal integration remains CI-only because no dedicated local DB URL is configured. Exact-head GitHub Actions checks are in progress; Freebuff suite 115293104315 is queued.
- **#1434 follow-up (91ef266f):** adds delegated Reseller-to-Customer Knowledge coverage: index the Customer-owned file in Customer portal context; verify search returns Customer content but excludes parent Reseller and sibling-tenant content; verify search returns 403 immediately after the Reseller-to-Customer grant is revoked. Local py_compile, Ruff, and git diff --check passed; RAG foundation/context tests passed (6 passed) with the documented Python 3.10 compatibility shim. The PostgreSQL-backed portal integration remains CI-only because no dedicated local test DB URL is configured. New exact-head CI had not started at the latest refresh; Freebuff suite 115125482288 was queued.
- Local checks previously recorded for #1428: Python compile, Ruff, and `git diff --check origin/main...HEAD` passed. Dedicated local PostgreSQL integration was not run because `SUPPORT_TEST_DATABASE_URL` and `DATABASE_URL` were absent.
- #1432's isolated CI Backend job passed; recorded backend suite result was 1,963 passed, 1 deselected, 28 warnings. The targeted portal grant/revocation integration test passed.
- Do not infer that local PostgreSQL integration passed. CI uses isolated disposable PostgreSQL where stated by the workflow.

**Merge gate (refreshed 2026-11-08):** all acceptance PRs remain unmerged until Freebuff completes successfully on each exact head and all other merge gates are freshly revalidated. #1428, #1431, #1432, #1433 and #1434 remain open/unmerged. For #1428/#1431/#1432/#1433, all visible GitHub Actions and CodeQL suites are successful; Freebuff suites 115101840461, 115085202766, 115094879907 and 115111856312 remain queued. PR #1434 is at exact head baac199fabffe511d4219d99df8d919860726750; new exact-head workflow/check suites had not yet appeared at refresh and Freebuff suite 115294066243 remained queued. #1434 review threads and submitted reviews are empty. No supported Freebuff retry/dispatch action is available in the inspected tool surface.

## 3. Multi-tenant acceptance audit — remaining gaps

The source-backed audit against main `d943ec2cffd75ea88daebdf02c7b6df413d3f2f6` identified the following incomplete or unproven areas:

- **Knowledge:** tenant-scoped indexing/search and Vendor-to-Reseller isolation exist. PR #1434 now covers Vendor-to-Reseller post-revocation denial and delegated Reseller-to-Customer indexing/search, exclusion of parent Reseller and sibling-tenant content, and immediate search denial after Customer grant revocation. Still need a distinct sibling-Customer topology, reindex-after-revoke and stale-context coverage; relational tenant-filtered chunks are evidenced, physical vector-store isolation is not.
- **Employee Reports:** source file, lock, audit and generated/reused artifacts are tenant-scoped. PR #1434 adds delegated Reseller-to-Customer Report Employee generation/list/download coverage and parent/sibling source denial; entitlement is stubbed at the license-service boundary, and revoked-context report-artifact denial remains outstanding.
- **Invoices/PDF:** invoice operations and PDF artifact creation are tenant-scoped; Vendor foreign invoice read denial exists. PR #1434 adds delegated Customer invoice list/PDF export/download, parent/sibling invoice denial and post-revocation export denial.
- **Run artifacts:** Run and audit/storage paths derive from tenant-scoped Run records. PR #1434 adds unit/API-level cross-tenant Run download and foreign-Run audit-pointer denial tests (including 404); full authenticated delegated Reseller-to-Customer portal integration for list/download, parent/sibling topology and revoked grant is now covered on PR #1434 exact head e0cc4493; its PostgreSQL integration execution remains pending exact-head CI.
- **Notifications/outbox:** durable tenant-aware enqueue/dedupe and several consumer-side checks exist. Still need recipient resolution, dispatch, retry/dead-letter and content-isolation matrix across Vendor/Reseller/Customer and delegated/revoked grants.
- **Background workers:** workflow, run, email, WhatsApp, workforce evaluation and test-center source paths were inspected. Need complete Celery/async task inventory, forged/mismatched task metadata and unauthorized enqueue tests, plus delayed/retried work after grant revocation and tenant-safe outputs/audit across all handlers.
- **Cache:** frontend identity-transition clearing exists; no generic backend application cache read/write layer was found in the inspected tree; Redis is used for rate limiting, tenant fair scheduling and tenant resource leases. Therefore a cache-key isolation defect is not evidenced; any future cache feature needs tenant/context-qualified keys and revoke invalidation tests.
- **WebSocket/realtime:** no WebSocket router/subscription surface was found in the inspected API router. Classify as not implemented/not evidenced, not as passed.
- **Entitlements:** test expiry, suspension, paid-to-expired transitions against existing tokens and in-flight/background operations.
- **Portal UX:** authenticated desktop/mobile journeys, delegated switch/return, empty/error/expired states, accessibility and human visual acceptance remain.
- **Legacy permission backfill:** SQL selection/idempotency and representative rehearsal evidence exist; no Production/Staging backfill is authorized.

See the detailed acceptance audit and evidence comments on Issue #1350. Do not convert gaps into claims of implementation without source and test evidence.

## 4. Immediate next actions

1. Refresh exact PR heads, all check suites/check runs (especially Freebuff), combined statuses, review threads and mergeability for #1428/#1431/#1432.
2. Keep all PRs unmerged while any required check is queued, missing or unsuccessful; current Freebuff suites remain queued on all five PRs.
3. Continue the gap-driven source/test audit in this order: notification/outbox recipient and retry isolation; worker enqueue/revocation; entitlement expiry/suspension against existing tokens and in-flight work; portal UX; remaining nested Knowledge and revoked Report artifact cases.
4. Add focused negative tests before changing authorization behavior.
5. Record each verified checkpoint on Issue #1350 and refresh this handoff with exact SHAs and observed evidence.
6. Complete the full multi-tenant acceptance matrix and final evidence review before closing Issue #1350.

## 5. Provenance and non-claims

- Main SHA above is the exact baseline observed during this checkpoint; verify it again before the next code change.
- PR and check-suite states are point-in-time observations from 2026-11-08, not guarantees about later status.
- No Production/Staging deployment, migration, persistent data mutation, payment activation or merge is claimed by this handoff.
- The historical `AI_EMPLOYEE_MASTER_HANDOFF_2026-11-02.md` remains historical; this dated document supersedes it as the current project checkpoint once merged.


## 2026-11-09 live refresh � supersedes stale status snapshots above

Observed at 2026-11-09 14:38 +03:30. This section is the current point-in-time snapshot; older tables and status paragraphs above are historical.

- PR #1428 exact head `ba65814d05dd624d6095d0ce5a8da1be761c0bcf`: open, unmerged, mergeable; 9 GitHub Actions suites and CodeQL succeeded; Freebuff Web suite `115101840461` remains queued. Review threads: 0; submitted reviews: none.
- PR #1431 exact head `c32576fec6c11d0fbd5bd79de98729818a35118d`: open, unmerged, mergeable; 9 GitHub Actions suites and CodeQL succeeded; Freebuff Web suite `115085202766` remains queued. Review threads: 0; submitted reviews: none.
- PR #1432 exact head `5102b645511ca01083af0bd97db3645d1b3c2f24`: open, unmerged, mergeable; 9 GitHub Actions suites and CodeQL succeeded; Freebuff Web suite `115094879907` remains queued. Review threads: 0; submitted reviews: none.
- PR #1433 exact head `f16052ada34c55d4a03167003f2434d2ce1b17f6`: open, unmerged, mergeable; 2 GitHub Actions suites and CodeQL succeeded; Freebuff Web suite `115303559730` remains queued. Review threads: 0; submitted reviews: none.
- PR #1434 exact head `65a941d766ba086ae68fb4da0a43305c529f68fa`: open, unmerged, mergeable; 9 GitHub Actions suites and CodeQL succeeded; Freebuff Web suite `115303403012` remains queued. Review threads: 0; submitted reviews: none.

PR #1434 now extends the authenticated delegated Reseller-to-Customer PostgreSQL portal integration beyond the earlier unit/API regressions. It seeds a Customer-owned completed Run and persisted artifact audit pointer; verifies Customer portal list and download; verifies parent and sibling Run artifact list/download are denied (404); and verifies both list and download are denied after delegated grant revocation (403). The same integration test also covers delegated Knowledge post-revocation denial, Report Employee generated artifact ownership/list/download and parent/sibling source denial, and Invoice PDF export/download with parent/sibling denial and post-revocation denial. Report Employee entitlement remains stubbed at the license-service boundary, so commercial entitlement is not certified by that test.

Local verification on PR #1434 exact head: py_compile passed; Ruff passed; `git diff --check origin/main...HEAD` passed; focused Report/Invoice/ToolRegistry/Run-artifact test group: 82 passed in 6.89s. The Run-artifact test module alone: 7 passed. Python 3.10 compatibility shim was used for StrEnum/UTC. PostgreSQL-backed portal integration remains CI-only because local `SUPPORT_TEST_DATABASE_URL` and `DATABASE_URL` are not configured.

Issue #1350 received progress comment `6738577079` recording this checkpoint. It remains open. No PR merged; no Production/Staging deployment, migration, persistent-data mutation, or payment activation occurred. No supported Freebuff retry/dispatch action is available in the inspected tool surface. Treat all five queued Freebuff suites as merge blockers, not passes.

Next work: continue notification/outbox recipient, dispatch, retry/dead-letter tenant-isolation coverage; then worker enqueue/forged metadata and post-revocation delayed work; then entitlement transitions and portal UX/accessibility. Keep the acceptance issue open until the full matrix and evidence review are complete.


## 2026-11-09 follow-up after the preceding refresh

- PR #1434 advanced to exact head `c607ec128f8e7c16444614023d10a1b3aec66c99`. It adds `test_governed_email_rejects_cross_tenant_row_binding_before_smtp`: a durable email row whose tenant differs from its Agent governance proof is rejected before policy authorization and SMTP; the row remains in the retryable pre-side-effect state. Focused notification/outbox/worker tests: 21 passed in 2.71s; py_compile, Ruff and diff checks passed. The new exact-head check snapshot currently exposes only Freebuff suite `115402938536`, still queued; GitHub Actions/CodeQL suites have not yet provisioned at the time of this note. Issue #1350 progress comment: `6738792891`.
- PR #1433 handoff refresh commit: `2ea9c73c0aee251babf0bef977b627e0c81b02c0`; PR remains open/unmerged. Its newly observed check-suite snapshot exposed Freebuff suite `115399883219` queued; other check suites had not yet provisioned at that instant.
- Do not treat missing/not-yet-provisioned suites as success. Re-fetch exact-head suites and check-runs before any merge decision. All queued Freebuff suites remain blockers.


## 2026-11-09 email revocation race checkpoint

- PR #1434 advanced to exact head `9115e3bcfac4fe156f324367d8b031cacaa39970`. A second email-worker regression simulates delegated Agent authority being revoked between initial authorization and immediate pre-SMTP revalidation after the outbox row is durably marked `uncertain`. It verifies the second authorization is performed, SMTP is not attempted, and the row remains `uncertain` (no blind retry after the side-effect boundary). Focused notification/outbox/worker suite: 22 passed in 2.70s; py_compile, Ruff and diff checks passed. Issue #1350 comment: `6738850124`. This is test-only; no application behavior changed.
- The current PR #1434 head must be re-fetched for CI; the prior head `c607ec128f8e7c16444614023d10a1b3aec66c99` had nine GitHub Actions workflows, most still in progress, and Freebuff `115402938536` queued. Do not carry those statuses forward to the new head.
- Keep Issue #1350 open and all PRs unmerged pending fresh exact-head required-check success, especially Freebuff.


## 2026-11-09 forged outbox governance checkpoint

- PR #1434 exact head: `9793f2109ff648ba920e4c3422ace76d56af9137`.
- Added tests in `backend/tests/test_outbox_tenant_dedupe.py`: forged caller-provided `_agent_governance` is stripped without an active governed tool context; an active Agent Run context cannot enqueue a message under a different tenant (rejected before add/flush).
- This supplements the existing dispatcher boundary tests: `agent.run.execute` compares payload tenant to the durable outbox row tenant, rejects mismatches before broker publish, and forwards the durable row tenant to the Run worker.
- Focused outbox/dispatcher/email/AgentExecutionAdapter tests: 28 passed in 2.43s. py_compile, Ruff and `git diff --check` passed.
- Issue #1350 progress comment: `6741209969`.
- Fresh exact-head check-suite fetch for `9793f210...` currently returns only Freebuff Web suite `115448675682`, queued with no conclusion. Other suites have not provisioned yet; missing is not success. Re-fetch before any merge decision.
- No application code change, merge, deployment, migration, persistent-data mutation, or payment activation.


## 2026-11-09 delayed Agent Run revocation checkpoint

- PR #1434 exact head: `8fa32c46887351bb6d50371b93479c2a2f0f5747`.
- Added `test_run_worker_blocks_delayed_run_after_delegation_revocation` in `backend/tests/workers/test_run_worker.py`. It simulates a queued Agent Run whose delegated authority has been revoked before worker execution. The worker runs kill-switch and current authorization checks, rejects the revoked delegation, and never loads runtime memory or starts Run execution.
- Combined Run-worker/outbox/dispatcher/email/AgentExecutionAdapter tests: 37 passed in 4.69s. py_compile, Ruff and `git diff --check` passed.
- Issue #1350 progress comment: `6741237057`.
- This complements the existing durable outbox forged-proof stripping, tenant mismatch enqueue rejection, dispatcher payload-vs-row binding, and pre-SMTP authority revalidation tests.
- Refresh exact-head CI for `8fa32c46...` before any merge decision. Previous head `9793f210...` exposed only queued Freebuff suite `115448675682`; do not carry statuses to this new SHA. No application code change, merge, deployment, migration, or persistent-data mutation.

## 2026-11-09 existing-token commercial entitlement expiry checkpoint

- PR #1434 advanced from 8fa32c46887351bb6d50371b93479c2a2f0f5747 to 0d83105a752e298237b0ceb50821caf93ad93278 (commit: test: deny portal access after tenant entitlement expiry).
- Added test_expired_paid_period_and_expired_demo_grant_deny_existing_tenant_access: when the paid subscription period is over and no unexpired, unrevoked Demo grant exists, a tenant requiring explicit access has no commercial access. The test asserts the paid-period and Demo-expiry/revocation predicates are in the SQL lookup.
- Added test_already_issued_portal_grant_is_denied_after_commercial_access_expires: a still-unrevoked portal grant and active tenant rows do not preserve access after the target tenant loses commercial entitlement; request-time validation fails closed with HTTP 402.
- Local verification: tenant access, feature entitlement, subscription lifecycle and subscription creation-fence suites: 38 passed in 1.90s. Ruff, compileall and git diff --check passed. Dedicated PostgreSQL portal integration remains unrun locally because no local test DB URL is configured.
- Exact-head CI for 0d83105a... was freshly queried: 10 suites are queued/pending at observation time (including Freebuff and GitHub Actions); none is treated as passed. PR #1434 remains open/unmerged; review threads and submitted reviews were empty at the latest query.
- This covers time-bounded paid/Demo access at request time for an already-issued portal grant. Full subscription suspension and in-flight/background operation cancellation remain separate acceptance cases.
- No application code changed; no merge, deployment, migration, persistent-data mutation or payment activation occurred. Issue #1350 remains open.

## 2026-11-09 paused-subscription follow-up

- PR #1434 advanced to 2941f40324bc7307b2d4b4b376f655431ac4028b. Added test_paused_subscription_does_not_preserve_existing_tenant_access, asserting a subscription that is not active (including paused/suspended states) cannot satisfy the paid-access predicate even before the billing period end; no unexpired Demo grant means access is denied.
- Re-ran tenant access, feature entitlement, subscription lifecycle and subscription creation-fence tests: 39 passed in 1.97s. Ruff and git diff --check passed.
- This is a request-time entitlement predicate test; full PostgreSQL-backed lifecycle transitions and revocation of already-running background work remain pending CI/remaining matrix.
- Exact-head CI must be refreshed for 2941f403; statuses from 0d83105a must not be carried forward. No application code changed; no merge/deploy/migration/data mutation/payment activation.

## 2026-11-09 execution-boundary revalidation checkpoint

- PR #1434 advanced to `1219a9efa05434ee34adea2412dd66cb607badff` (`test: revalidate delegation before run side effects`).
- Added `test_run_service_rechecks_delegation_after_worker_preflight_before_execution`: simulates the worker preflight succeeding, then delegation being revoked before the canonical Run service execution boundary. The service-level governance wrapper re-authorizes using the persisted Run delegation proof; denial prevents the original execution function (and therefore provider/tool side effects) from being invoked.
- Combined governance bootstrap, Run Worker and delegation governance tests: 31 passed in 4.70s. Ruff and `git diff --check` passed.
- This verifies the second authorization boundary with a focused service wrapper test; a live PostgreSQL race test with two concurrent transactions is still not run locally and remains a CI/integration evidence gap.
- Prior exact-head CI for 2941f403 was green for GitHub Actions and CodeQL, with Freebuff queued. These results do not transfer to the new SHA `1219a9ef`; refresh exact-head checks. No application code changed; no merge, deployment, migration, persistent-data mutation or payment activation.

## 2026-11-09 CI refresh after Run revalidation commit

- PR #1434 current head: `1219a9efa05434ee34adea2412dd66cb607badff`. Fresh check-suite snapshot: eight GitHub Actions suites in progress, one GitHub Actions suite queued, and Freebuff Web queued. No current suite failure reported; CI is not complete.
- PR #1433 current head: `1f5193b7576f3630ba06ccf398620553398f6d28`. Fresh snapshot: GitHub Actions and GitHub Advanced Security completed successfully; Freebuff Web queued.
- PRs #1428, #1431 and #1432: GitHub Actions and GitHub Advanced Security completed successfully at their current heads; Freebuff Web remains queued.
- All five PRs remain open and unmerged. PR #1434 review threads and submitted reviews are both empty at the latest fetch. Do not treat Freebuff queued as success or merge any PR until every required check on the exact head is green.

## 2026-11-09 entitlement concurrency and portal navigation follow-up

- Fresh PR refresh: #1428 ba65814d05dd624d6095d0ce5a8da1be761c0bcf; #1431 c32576fec6c11d0fbd5bd79de98729818a35118d; #1432 5102b645511ca01083af0bd97db3645d1b3c2f24; #1433 4eeff9d5fdcad89548d731b47dc69196af83e140; #1434 1219a9efa05434ee34adea2412dd66cb607badff. All remain open/unmerged. GitHub Actions and GitHub Advanced Security suites succeeded on each exact head; Freebuff Web remains queued on all five. Review threads and submitted reviews are currently zero on all five.
- Portal audit confirmed no alternate mobile navigation inside ResellerSurface or TestCenterWorkspace. ResellerSidebar remains hidden ... md:flex; six Reseller routes without the shared Header therefore still lack a visible mobile navigation control. Static source inspection only; no browser/screen-reader test or frontend code change.
- Entitlement concurrency audit confirmed execute_run_locked() acquires WorkItem lineage root-to-leaf then Run, matching cancellation's ordering. tenant_access_source() reads Subscription and TenantDemoGrant without row locks; revoke paths lock their respective entitlement rows. Tenant-row locking is used by several other services with different surrounding lock orders, so adding a common tenant anchor requires a complete cross-service lock-order review before implementation; no safe global ordering has yet been established.
- Local DATABASE_URL, SUPPORT_TEST_DATABASE_URL, and COMMERCIAL_LICENSE_TEST_DATABASE_URL are unset. No live PostgreSQL race test was run. Issue #1350 comment 6742216504 records these findings.
- No code change, merge, deployment, migration, persistent-data mutation, or payment activation. Keep Issue #1350 open; Freebuff queued remains a merge blocker.

## 2026-11-09 Reseller mobile navigation remediation

- PR #1434 advanced to exact head fa00b497cc27d6249008acd65eccfb89cbb95d13 (fix: add mobile navigation to reseller portal).
- The Reseller route-group layout now provides a shared native, labelled mobile navigation select below the md breakpoint, using bilingual reseller labels and all 13 destinations from the desktop sidebar. The current route is selected; choosing a destination navigates through Next router. Desktop sidebar behavior is unchanged.
- Added a frontend contract covering the accessible label, mobile visibility breakpoint, navigation callback and route parity. Local verification: frontend contract 150 passed / 0 failed; Governance UI contract PASS; git diff --check PASS. Browser/Vitest and screen-reader checks remain outstanding because frontend/node_modules is not installed in the worktree.
- Fresh exact-head check suites for fa00b497...: Freebuff Web queued and nine GitHub Actions suites queued; none is a pass yet. PR #1434 remains open/unmerged, mergeable, with zero review threads and no submitted reviews.
- Issue #1350 comments 6742448078 and 6742459933 record the implementation and CI snapshot. No deployment, merge, migration, persistent-data mutation, or payment activation.


## 2026-11-09 exact-head CI completion for Reseller mobile navigation

- PR #1434 exact head `fa00b497cc27d6249008acd65eccfb89cbb95d13`: all 10 GitHub Actions check suites and GitHub Advanced Security completed successfully; Freebuff Web remains queued. PR remains open/unmerged. Review threads and submitted reviews remain zero.
- CI run 42634451684: frontend dependency installation, ESLint, contract tests, unit tests, production build, Chromium setup, Playwright browser regressions and visual-review screenshot upload all succeeded. Backend job also succeeded. Public widget browser/API acceptance run 42634451565 succeeded, including production frontend build and Chromium browser-to-real-API/worker flow. Additional architecture, CodeQL, HA recovery, production infrastructure, DAST, workforce and semantic real-stack runs succeeded.
- Scope qualification: broad Playwright browser regressions passed, but none is yet a dedicated interaction assertion for the new Reseller mobile navigation select; the added contract checks markup, accessibility label, mobile breakpoint, route callback and 13-route parity. Dedicated mobile interaction and screen-reader validation remain outstanding.
- All five PRs remain open/unmerged. Latest exact-head snapshot: #1428 (10 success, Freebuff queued); #1431 (10 success, Freebuff queued); #1432 (10 success, Freebuff queued); #1433 (3 success, Freebuff queued); #1434 (10 success, Freebuff queued). Do not merge while Freebuff remains queued.
- Issue #1350 comment 6742781635 records the CI details. No merge, deployment, migration, persistent-data mutation or payment activation.


## 2026-11-09 Reseller mobile navigation browser acceptance added

- PR #1434 advanced from `fa00b497cc27d6249008acd65eccfb89cbb95d13` to exact head `ca2a31bcaef8c35b184dae2d619dff551b2ac8e9` (commit `test: cover reseller mobile navigation in browser`).
- `frontend/e2e/portal-login.spec.ts` now exercises the Reseller portal at 390×844: accessible combobox visibility, 13 route options, initial Dashboard selection, selection of Integrations, route transition to `/reseller/integrations`, and selected-option synchronization.
- CI Playwright browser-regression command now includes `e2e/portal-login.spec.ts`; this converts the new mobile navigation check into an actual CI browser test.
- `git diff --check` passed before commit. Local Playwright execution was not completed: npm installation ran out of free space on the C: drive (about 504 MB remained); partial `frontend/node_modules` was removed. No tracked lockfile change.
- At the time of this handoff update, exact-head GitHub Actions suites for #1434 were in progress/queued; Freebuff Web was still queued. Do not claim browser interaction passed until the exact-head CI Playwright step succeeds.
- Issue #1350 comment: https://github.com/ijoolaie/AI-Employee/issues/1350#issuecomment-6743042079
- All five acceptance PRs remain open/unmerged. No deployment, migration, persistent-data change, or payment activation.


## 2026-11-09 mobile navigation CI fixture correction

- PR #1434 exact head `ca2a31bcaef8c35b184dae2d619dff551b2ac8e9` ran its full CI. Backend and eight other Actions workflows succeeded; Frontend Playwright failed in the existing sign-in routing loop before reaching the new mobile-navigation assertions.
- Root cause: the mocked `/auth/me` tenant fixture omitted `access_granted`. The login implementation treats missing/false access as inactive and correctly routes to `/billing`, while the test expected a permitted portal route.
- Corrected the E2E fixture to explicitly set `access_granted: true`; pushed commit `c474efe20e448565f21cc0d6c21e14252e4f52bc` to PR #1434. `git diff --check` passed. Local Playwright was not run because frontend dependencies are absent in the worktree. Exact-head CI had not yet appeared at handoff update time; do not claim it passed.
- Issue #1350 comment 6743679405 records the failure and correction.
- All five acceptance PRs remain open/unmerged. Latest previously refreshed review threads and submitted reviews were zero on all five. Freebuff remains a merge blocker until it reports success on each exact head. No merge, deployment, migration, persistent-data mutation, or payment activation.


## 2026-11-09 frontend CI package mirror remediation

- PR #1434 exact head `c474efe20e448565f21cc0d6c21e14252e4f52bc`: CI frontend and backend jobs both succeeded. The Playwright portal-login test including the 390×844 Reseller navigation assertions passed after adding `access_granted: true` to the mocked tenant. Eight of nine workflow runs succeeded; three independent image-build validations (Production Infrastructure, Ephemeral DAST, HA Recovery) failed at the same Docker frontend dependency install step.
- Failure root cause from all three job logs: `npm ci` received HTTP 500 from `registry.npmmirror.com` for `zod-4.6.7.tgz`, with mirror backend error `ER_NO_SUCH_TABLE`. This is a package-registry service failure, not an application/test failure.
- Remediation pushed to PR #1434 as `3d455b3d05049af82bdce4e147951a543b13002d`: `frontend/.npmrc` now points to canonical `https://registry.npmjs.org`; all 147 resolved tarball URLs in `frontend/package-lock.json` were changed to the canonical registry. Dependency versions and integrity hashes were not changed. `git diff --check` passed. No local npm installation attempted. Exact-head CI had not yet appeared.
- Issue #1350 comment 6744256956 records the failure evidence and fix.
- All five acceptance PRs remain open/unmerged. Freebuff Web remains queued on the previous exact heads and must report success on the current exact head before any merge. No merge, deployment, migration, persistent-data mutation, or payment activation.


## 2026-11-09 follow-up exact-head refresh

- All five acceptance PRs refreshed: #1428 `ba65814d05dd624d6095d0ce5a8da1be761c0bcf`, #1431 `c32576fec6c11d0fbd5bd79de98729818a35118d`, #1432 `5102b645511ca01083af0bd97db3645d1b3c2f24`, #1433 `b499890f47c44b5ab40368cd4a18132128b7086b`, #1434 `3d455b3d05049af82bdce4e147951a543b13002d`. All open/unmerged; zero review threads and submitted reviews.
- PR #1434 current exact-head workflows: HA Failure Recovery passed; Architecture Guard and W21 AI Business Network E2E passed; Backend, Frontend Playwright browser regressions, Production Infrastructure lifecycle/persistence, Ephemeral DAST/OWASP ZAP, Public Widget browser/API, Workforce semantic real-stack were still running at the latest job-level refresh without failed steps. Freebuff Web queued.
- PR #1433 current head Documentation Truth Consistency passed; CodeQL in progress; Freebuff queued.
- Local frontend dependency installation was attempted only in the approved PR1434 worktree and failed with Windows `ENOSPC` due to low C: storage (about 413 MB free). The partial ignored `frontend/node_modules` directory was removed and worktree status is clean. No further local install/browser test until storage is available; rely on CI.
- Entitlement check-vs-revocation race remains open for lock-order analysis. Execution locks WorkItem lineage then Run, but entitlement reads do not lock Subscription/DemoGrant rows while revoke operations do. No ad hoc Tenant anchor lock added because global lock-order reconciliation is still required. Issue #1350 comment 6744317044 records this refresh.
- No merge, deployment, migration, persistent-data mutation, or payment activation.


## 2026-11-09 acceptance refresh and entitlement-lock audit

- Refreshed exact heads and check suites for all five acceptance PRs. #1428, #1431, #1432 and #1434 each have all nine GitHub Actions workflow runs successful; #1433 has Documentation Truth Consistency and CodeQL successful. All five PRs remain open/unmerged, with zero review threads and zero submitted reviews.
- All five PRs still have the external Freebuff Web check suite in `queued`; this is a blocking non-success state. GitHub branch-protection read returned 403 for the connected integration, so required-check configuration could not be independently enumerated.
- PR #1434 exact head `3d455b3d05049af82bdce4e147951a543b13002d`: all nine Actions runs successful, including CI, Playwright browser regressions, CodeQL, Architecture Guard, W21 E2E, HA Recovery, Production Infrastructure, Ephemeral DAST and Public Widget browser/API.
- PR #1433 handoff head advanced to `6507977d059d3f5e1cb980c635881dc2ea422841`; Documentation Truth Consistency and CodeQL passed on this exact SHA.
- Deeper Run entitlement audit identifies a candidate row-level serialization approach: `FOR SHARE` (SQLAlchemy `with_for_update(read=True)`) on the qualifying Subscription or TenantDemoGrant during entitlement reads. Mutations/revocations already lock those entitlement rows with `FOR UPDATE`. This may serialize admission against revocation without adding a broad Tenant anchor lock. It is not yet proven: verify all writers, PostgreSQL SQL semantics, lock retention through Run terminal commit, and a two-session PostgreSQL race test for both paid and Demo entitlements. No code change made. Issue #1350 comment 6744411079 contains the detailed rationale and test plan.
- Local frontend npm install remains unavailable until disk space is restored (previous `ENOSPC`, partial ignored node_modules removed, worktree clean). Dedicated PostgreSQL URL was not configured locally. Use CI/PostgreSQL-backed tests for proof.
- No merge, deployment, migration, persistent-data mutation, or payment activation.


## 2026-11-09 latest acceptance refresh

- Exact-head check suites refreshed across all five open PRs. #1428 (`ba65814d05dd624d6095d0ce5a8da1be761c0bcf`), #1431 (`c32576fec6c11d0fbd5bd79de98729818a35118d`), #1432 (`5102b645511ca01083af0bd97db3645d1b3c2f24`), and #1434 (`3d455b3d05049af82bdce4e147951a543b13002d`) each have nine successful GitHub Actions suites plus successful GitHub Advanced Security. #1433 (`22d83c87524084b4b58eecdc7b0d6fc9e31eeeb0`) has Documentation Truth Consistency and CodeQL successful.
- All five remain open/unmerged, with zero review threads and zero submitted reviews. Freebuff Web remains `queued` on every PR and is not a pass. Combined legacy commit status has no contexts; branch protection API returned 403 to the connected integration.
- Reviewed additive portal test patches: #1428 nested Customer file lifecycle and parent isolation; #1431 delegated Reseller-in-Customer file lifecycle and parent-home isolation; #1432 sibling Customer file enumeration/read/download/delete denial under another Customer's grant.
- Entitlement race remains open. Candidate `FOR SHARE` on the qualifying Subscription/DemoGrant row is not implemented until PostgreSQL two-session tests prove the ordering and all writer paths are verified.
- No merge, deployment, migration, persistent-data mutation, or payment activation.


## 2026-11-10 acceptance refresh and entitlement-race refinement

- Refreshed all five PRs and their exact current heads: #1428 `ba65814d05dd624d6095d0ce5a8da1be761c0bcf`, #1431 `c32576fec6c11d0fbd5bd79de98729818a35118d`, #1432 `5102b645511ca01083af0bd97db3645d1b3c2f24`, #1433 `79b580aa4770a8594cac753d464f23120c30c716`, #1434 `3d455b3d05049af82bdce4e147951a543b13002d`. All remain open/unmerged.
- #1428/#1431/#1432/#1434 each have 9/9 GitHub Actions suites successful and GitHub Advanced Security successful. #1433 has Documentation Truth Consistency and CodeQL successful, plus GitHub Advanced Security successful. Freebuff Web remains queued on all five exact heads and is not a pass.
- All five have zero review threads and zero submitted reviews. No merge/deploy/migration/Production or Staging data mutation/payment activation.
- Concurrency audit refinement: for paid access, `tenant_access_source()` reads the qualifying Subscription without a row lock, but the subsequent `get_subscription()` -> `ensure_subscription()` locks that Subscription `FOR UPDATE` and checks active status in the same Run transaction. This may already serialize paid cancellation/update admission, but needs exact PostgreSQL race proof including expiry/period transitions.
- For Demo access, `tenant_access_source()` reads the unrevoked/unexpired TenantDemoGrant without locking it; the later subscription lock is on a different row. Demo-grant revocation can therefore still race admission. Protecting the DemoGrant through the Run transaction remains an open design/test task.
- Do not blindly add `FOR SHARE` to both entitlement reads: the paid path later requests `FOR UPDATE` on Subscription, so shared-to-exclusive lock upgrade among concurrent admissions could contend or deadlock. No code change made.
- Required proof remains PostgreSQL two-session barrier tests for DemoGrant revoke-vs-admit and paid Subscription cancel/update-vs-admit, plus writer-path and transaction-commit audit. No dedicated DB URL available in the local environment.
- Issue #1350 comment 6760491777 records this evidence. Issue #1350 remains open; no acceptance sign-off is claimed.


## 2026-11-10 follow-up exact-head refresh and transaction-boundary audit

- Refreshed all five exact PR heads: #1428 `ba65814d05dd624d6095d0ce5a8da1be761c0bcf`, #1431 `c32576fec6c11d0fbd5bd79de98729818a35118d`, #1432 `5102b645511ca01083af0bd97db3645d1b3c2f24`, #1433 `f6c1b162701fc108c8b1b11bdf334a411f36716b`, #1434 `3d455b3d05049af82bdce4e147951a543b13002d`. All remain open/unmerged.
- #1428/#1431/#1432/#1434 each have all nine GitHub Actions workflows successful and GitHub Advanced Security successful. #1433 has Documentation Truth Consistency and CodeQL successful plus GitHub Advanced Security successful. Freebuff Web remains `queued` on all five exact heads; it is not a pass.
- All five have zero review threads and zero submitted reviews. No merge, deployment, migration, Production/Staging data mutation, or payment activation.
- Source audit confirms `run_worker._run_async()` invokes `execute_run_locked()` within `worker_db_session()`, then flushes and commits after Runtime execution; exception path also commits. The worker transaction can therefore retain locks acquired during admission through the worker commit boundary, subject to the real runtime/session behavior.
- Demo revoke API calls `revoke_demo_grant()` then commits; service obtains `FOR UPDATE` on the grant row before setting `revoked_at`.
- Existing tenant-access tests mock `db.execute`; they do not assert an access-side grant lock or run concurrent PostgreSQL sessions. Run execution fence tests likewise use mocks/source contracts, not a DB race test.
- Candidate Demo-only fix is a PostgreSQL `FOR SHARE` lock on the qualifying TenantDemoGrant row in `tenant_access_source()` (SQLAlchemy `with_for_update(read=True)`), retained until Run worker commit. If revoke wins first, the locking SELECT should re-evaluate `revoked_at IS NULL` after waiting and deny; if admission locks first, revocation should wait for worker commit. This is not implemented or proven.
- Do not apply an untested code change. Required next proof: two-session PostgreSQL barrier tests for DemoGrant revoke-vs-admit and paid Subscription cancel/update-vs-admit, plus emitted SQL and transaction behavior. Issue #1350 comment 6760697717 records the evidence. Issue #1350 remains open.


## 2026-11-10 invitation activation race audit and exact-head refresh

- Refreshed exact heads: #1428 `ba65814d05dd624d6095d0ce5a8da1be761c0bcf`; #1431 `c32576fec6c11d0fbd5bd79de98729818a35118d`; #1432 `5102b645511ca01083af0bd97db3645d1b3c2f24`; #1433 `a35d160680ed5349c43b1a1e2eea95f3411b8273`; #1434 `3d455b3d05049af82bdce4e147951a543b13002d`. All five remain open/unmerged.
- On those exact heads, #1428/#1431/#1432/#1434 each have nine GitHub Actions workflow runs completed successfully plus GitHub Advanced Security success. #1433 has Documentation Truth Consistency and CodeQL completed successfully plus Advanced Security success. Freebuff Web remains `queued` on all five. All five have zero review threads and zero submitted reviews. Freebuff is not a pass; do not merge.
- Reviewed `tenant_invitation_service.py`: `_activate_if_paid()` reads qualifying DemoGrant rows without a row lock; `activate_eligible_invited_users()` locks Invitation and User rows but not the entitlement row. A revoke-vs-activation interleaving can therefore allow an invitee activation after a concurrent grant revocation commits, depending on transaction ordering. The revoke service locks DemoGrant `FOR UPDATE`; the admin route commits after revocation.
- Existing `test_tenant_invitation_service.py` covers activation/non-acceptance with mocked DB results; it does not prove concurrent PostgreSQL ordering. This adds a second DemoGrant consumer to the race audit alongside Run admission. Required real-PostgreSQL barrier tests must cover both consumers and both lock orderings.
- Policy remains unresolved: the repository's `accept_invitation()` activates identity for billing/login even when workspace entitlement is false. Separately, it is not established whether revoking a DemoGrant should deactivate already activated invitees, invalidate their sessions, or only prevent future activation/workspace access. No behavior was changed pending explicit product/security policy and test evidence.
- Issue #1350 comment 6761718588 records the source findings and policy boundary. No code change, migration, persistent-data mutation, merge, deployment, or payment activation.

## 2026-11-10 invitation-race classification correction and exact-head refresh

- Follow-up source inspection narrows the prior invitation-race severity. `accept_invitation()` deliberately sets `User.is_active = true` before checking entitlement so accepted invitees can sign in for billing. The auth API response explicitly says workspace access still requires paid access or an active Demo grant.
- `get_current_context()` independently enforces `tenant_has_access()` for every non-billing JWT request and for API-key requests, returning HTTP 402 when no paid subscription or active Demo grant exists. Delegated portal validation also rechecks target-tenant commercial access. Therefore, invitee identity activation is not itself a workspace entitlement and the observed `_activate_if_paid()` race is not evidence of a workspace-access bypass.
- Reclassify `activate_eligible_invited_users()` / `_activate_if_paid()` as an identity-lifecycle consistency path: an invitee whose identity is inactive at that moment could be reactivated after a concurrent Demo revocation, but workspace access remains independently gated. Any policy to disable billing/login identities after revocation is separate and not established by current code. No deactivation policy change is required for the workspace gate.
- Security-critical DemoGrant concurrency proof should focus on the actual request authorization gate (`get_current_context()` / `tenant_has_access()`) and Run worker admission. Test both lock orderings with two PostgreSQL sessions: revoke commits first and waiting admission denies after predicate re-evaluation; admission obtains the shared grant lock first and revocation waits until the protected request/Run transaction commits. Verify the FastAPI function-scoped `get_db` dependency is shared by context and endpoint so a lock survives the protected operation. Paid Subscription cancel/update/expiry remains a separate proof; do not blindly add a shared lock where a later `FOR UPDATE` may cause lock-upgrade contention.
- Issue #1350 correction: comment `6761986297`. Earlier invitation-race classification is superseded by this clarification.
- Exact PR heads refreshed 2026-11-10: #1428 `ba65814d05dd624d6095d0ce5a8da1be761c0bcf`; #1431 `c32576fec6c11d0fbd5bd79de98729818a35118d`; #1432 `5102b645511ca01083af0bd97db3645d1b3c2f24`; #1433 `a70fdba6f4a626df0739d2c1d44c9c070c89629c`; #1434 `3d455b3d05049af82bdce4e147951a543b13002d`. All remain open/unmerged. #1428/#1431/#1432/#1434 each have 9/9 GitHub Actions suites successful plus Advanced Security success; #1433 has 2/2 GitHub Actions suites successful plus Advanced Security success. Freebuff Web remains queued on all five exact heads, with zero check runs; it is not a pass. All five have zero review threads and zero submitted reviews.
- Approved worktree is clean. `DATABASE_URL`, `SUPPORT_TEST_DATABASE_URL`, and `COMMERCIAL_LICENSE_TEST_DATABASE_URL` are unset; no PostgreSQL race test was run. No application change, merge, deployment, migration, persistent-data mutation, or payment activation.

## 2026-11-10 PostgreSQL DemoGrant admission/revocation race fix and test

- Refreshed all five PR heads after the latest change: #1428 ba65814d05dd624d6095d0ce5a8da1be761c0bcf; #1431 c32576fec6c11d0fbd5bd79de98729818a35118d; #1432 5102b645511ca01083af0bd97db3645d1b3c2f24; #1433 6705e0127fca9b67e57b1ff67d2e53117c8c66d2; #1434 9a036d12921af3c3955ffdc4af3edc96643fca49. All five remain open and unmerged.
- PR #1434 now serializes qualifying DemoGrant authorization against revocation: tenant_access_source() uses SQLAlchemy with_for_update(read=True) (PostgreSQL FOR SHARE) only for the active, unrevoked, unexpired DemoGrant row. The paid Subscription lookup was deliberately not changed; its subsequent billing-service FOR UPDATE path remains separate.
- Added backend/tests/test_tenant_demo_grant_postgres_race.py. It uses independent async SQLAlchemy sessions with NullPool and observes actual PostgreSQL lock waits. It covers both orderings: authorization's shared row lock first makes revocation wait until the authorization transaction commits; revocation's exclusive row lock first makes authorization wait and then deny after PostgreSQL re-evaluates revoked_at IS NULL at READ COMMITTED.
- Local disposable PostgreSQL 16 container was used only on loopback port 15435, separate from the existing staging container. Alembic upgraded the disposable database to head. Local targeted verification after the fix: pytest tests/test_tenant_access_service.py tests/test_tenant_demo_grant_postgres_race.py -q — 13 passed. Ruff check and git diff --check passed.
- A broader attempt including test_run_execution_fence.py could not collect under the available Python 3.10 interpreter because that module imports enum.StrEnum (Python 3.11+). This is a local interpreter compatibility limitation, not a failed test assertion; no ad hoc package installation was performed.
- PR #1434 commit 9a036d12921af3c3955ffdc4af3edc96643fca49 has fresh GitHub Actions suites in progress at the last exact-head fetch; Freebuff Web remains queued. PR #1434 has zero review threads and zero submitted reviews. Other four PRs remain at their exact heads above; their GitHub Actions and Advanced Security suites are successful, while Freebuff Web remains queued on each.
- Issue #1350 comment 6762479757 records the implementation, two-session proof, exact local test result, and runtime limitation.
- The DemoGrant lock is held until the caller's transaction ends. Request path uses the function-scoped shared get_db dependency for authorization and endpoint; worker path has a separate transaction and explicit commit after runtime. End-to-end request/worker boundary integration remains a distinct follow-up verification.
- Paid Subscription cancel/update/expiry race has not been tested or changed. Invitation identity activation remains a separate identity-lifecycle path, not evidence of workspace access bypass; the request gate independently enforces commercial access.
- No merge, deployment, shared-environment migration, persistent Production/Staging data mutation, or payment activation. Issue #1350 remains open; Freebuff queued remains a merge blocker.

## 2026-11-10 PostgreSQL paid Subscription admission/lifecycle race proof

- Paid entitlement source is read optimistically by tenant_access_source(), but assert_run_execution_entitlement() then calls get_subscription() -> ensure_subscription(), which selects the tenant Subscription FOR UPDATE and checks its current state in the same transaction. Stripe lifecycle writers also lock Subscription rows before applying authoritative state.
- Added backend/tests/test_tenant_paid_subscription_postgres_race.py on PR #1434. The test uses independent async sessions (NullPool) and verifies real PostgreSQL lock waits in both orders: Run admission obtains FOR UPDATE first and lifecycle update waits for transaction commit; lifecycle update obtains FOR UPDATE first and admission waits, then rejects the newly committed canceled state even though the earlier paid-source SELECT observed the old committed active row.
- Local disposable PostgreSQL 16 verification: paid race test passed 3 consecutive independent runs. Combined suite (test_tenant_access_service.py, DemoGrant race, paid Subscription race, existing Subscription lock test) = 15 passed. Ruff lint passed; both new race tests are formatted; git diff --check passed. Existing tenant_access_service.py is not fully Ruff-formatted in baseline, so no unrelated mass formatting was applied.
- Commit pushed to PR #1434: 2bb490309e6afa3d420a5c24bf02eb91d3ed41f9. Exact-head GitHub Actions suites are in progress; Freebuff Web remains queued.
- Latest all-PR exact heads: #1428 ba65814d05dd624d6095d0ce5a8da1be761c0bcf; #1431 c32576fec6c11d0fbd5bd79de98729818a35118d; #1432 5102b645511ca01083af0bd97db3645d1b3c2f24; #1433 79c028c99564c6938b32a82d5eb346f7317c15f7; #1434 2bb490309e6afa3d420a5c24bf02eb91d3ed41f9. All remain open/unmerged, zero review threads, zero submitted reviews. Actions and Advanced Security successful on the first four; PR #1434 Actions are running. Freebuff queued on all five is still a merge blocker.
- Issue #1350 comment 6762642983 records the paid Subscription proof. The test proves billing-service admission/lifecycle transaction serialization; full Worker runtime duration and every Stripe webhook event type remain separate coverage.
- No merge, deployment, shared-environment migration, persistent-data mutation, or payment activation.

## 2026-11-10 paid entitlement post-lock revalidation correction

- A deeper race review found that locking Subscription after the first paid-source read was not sufficient for every mutable eligibility field. If a Stripe lifecycle update changed current_period_end to the past (or changed provider/plan eligibility) after the first source query but before admission obtained FOR UPDATE, _assert_subscription_active() only checked status and could accept an active-but-expired provider row.
- PR #1434 commit 971ff1b11374fed35157d33449baf9d8d2087541 adds _revalidate_tenant_access_after_subscription_lock(). After get_subscription() obtains the Subscription FOR UPDATE lock, all four billing admission/quota paths (assert_run_execution_entitlement, enforce_run_quota, enforce_employee_quota, enforce_workflow_quota) re-read the qualifying access source and fail closed if current paid eligibility has disappeared. Demo remains supported, and its DemoGrant FOR SHARE lock remains held. No shared Subscription lock or lock upgrade was introduced.
- Extended test_tenant_paid_subscription_postgres_race.py to prove the period-end interleaving: the initial paid-source SELECT sees the previously committed future period, admission waits on the lifecycle writer's Subscription lock, then post-lock revalidation sees the committed expired period and denies. The opposite ordering still proves lifecycle writer waits behind Run admission.
- Local disposable PostgreSQL 16: paid expiry race passed 3 consecutive runs; combined targeted suite across DemoGrant, paid Subscription, tenant access, billing lock, subscription-state fence, and vendor exemption = 30 passed. Ruff lint and formatting for the new race test passed; git diff --check passed.
- Issue #1350 comment 6762710615 records the newly identified stale-period race, fix, and test evidence.
- PR #1434 exact head is 971ff1b11374fed35157d33449baf9d8d2087541; all GitHub Actions suites freshly queued, Freebuff Web remains queued. PR remains open/unmerged with zero review threads and zero submitted reviews.
- Latest previously refreshed other heads: #1428 ba65814d05dd624d6095d0ce5a8da1be761c0bcf; #1431 c32576fec6c11d0fbd5bd79de98729818a35118d; #1432 5102b645511ca01083af0bd97db3645d1b3c2f24; #1433 c354398f28660e74d63ea632cb87abbfb87f4551. All open/unmerged; Freebuff queued on each; Actions and Advanced Security successful on #1428/#1431/#1432, while #1433 Documentation Truth Consistency passed and CodeQL was in progress at last refresh.
- Remaining: full Worker runtime duration and HTTP request-boundary integration, Stripe webhook event matrix, current exact-head CI, Freebuff blocker, and remaining multi-tenant acceptance matrix. No merge/deploy/shared-environment migration/persistent data mutation/payment activation.

## 2026-11-10 quota-path post-lock entitlement revalidation tests

- Added parameterized regression tests for enforce_run_quota, enforce_employee_quota, and enforce_workflow_quota. Each simulates an initial paid entitlement followed by a failed post-Subscription-lock revalidation and asserts quota usage is not consumed.
- Latest local disposable PostgreSQL 16 targeted result: 33 passed across DemoGrant race, paid Subscription period-end race, tenant access, Subscription lock, subscription-state creation fence, quota-path revalidation, and vendor billing exemption. Paid expiry race separately passed three consecutive runs. Ruff lint, new-test formatting, and git diff --check passed.
- PR #1434 test commit: 331b0ca0eabe38a5d4815435facae054262c5dc2. CI must be refreshed on this exact head.
- Issue #1350 comment 6762754308 records the expanded regression coverage.
- No merge, deployment, shared-environment migration, persistent data mutation, or payment activation.
