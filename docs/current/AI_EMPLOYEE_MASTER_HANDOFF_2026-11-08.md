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
