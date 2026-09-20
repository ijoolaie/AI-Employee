# AI-Employee — A–F Test Tracker

**Status date:** 2026-09-20
**Repository:** `ijoolaie/AI-Employee`
**Purpose:** Single living tracker for the current test sequence. Update this document as evidence is completed; do not restart already-passed smoke/contract tests unless a regression requires it.

## PHASE A — Core

- [x] Health — automated/runtime evidence present
- [x] Dependencies — automated/runtime evidence present
- [x] Auth — automated coverage and real-stack certification passed
- [x] Tenant isolation — automated coverage and real-stack certification passed
- [x] Employee — automated coverage present
- [x] Version — automated coverage present
- [x] Run — automated coverage present
- [x] Worker — local Docker runtime observed healthy and Celery tasks succeeding
- [x] Trace — local Docker runtime verification passed

## PHASE B — Execution Safety

- [x] Guardrails — automated tests passed
- [x] Tool permissions — automated tests passed
- [x] Failure handling — automated coverage present
- [x] Retry — runtime fail-closed verification passed
- [x] Timeout — runtime sweep verification passed
- [x] Cancellation — runtime service verification passed

## PHASE C — AI

- [x] Real provider — local Docker runtime execution passed
- [x] Token accounting — automated coverage present
- [x] Cost accounting — automated coverage present
- [x] Prompt assembly — automated coverage present
- [x] RAG — full end-to-end runtime verification passed

## PHASE D — Workflow

- [x] Workflow — automated tests passed
- [x] Trigger — automated tests passed
- [x] Schedule — automated tests passed
- [x] Approval — automated tests passed
- [x] Webhook — runtime/API verification passed
- [x] Replay — runtime verification passed

## PHASE E — Business

- [x] Customer — implementation/test coverage present
- [x] Inbox — implementation/test coverage present
- [x] Sales — implementation/test coverage present
- [x] Commerce — implementation/test coverage present
- [x] Billing — implementation/test coverage present
- [x] Analytics — implementation/test coverage present
- [x] Full-stack business acceptance — five official real-stack acceptance gates passed on 2026-09-18

## PHASE F — Production Certification

- [x] Security — Production Certification workflow passed on exact `v1.4.7` SHA; CI/CodeQL/DAST-related release gates passed
- [x] Tenant isolation — exact-release Product Gate passed
- [x] Load — exact-release certification suite passed its load/performance gate
- [x] Recovery — exact-release recovery/HA gates passed
- [x] Dead letters — exact-release queue/dead-letter gate passed
- [x] Observability — exact-release observability/SLO contract gate passed

**Phase F aggregate release-certification gate: PASS.** Production Certification run `35498984521` executed from the `v1.4.7` tag, checked out `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`, recorded `0` Product Gate failures, and completed successfully. This is engineering/release certification evidence; external production deployment remains pending.

## Phase F — Exact-release Production Certification — 2026-09-20

- Release: `v1.4.7`
- Exact certified SHA: `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`
- Workflow run: `35498984521` — **PASS**
- Certification job: `106047204166` — **PASS**
- Product Gate Failures: `0`
- Frontend Playwright: `6/6` PASS
- Evidence artifact: `production-certification-evidence-v1.4.7-48a6df0ea8a2fb0624e831fbdea55ee4548807f6`
- Artifact SHA256: `86c82af5326bce9d6be634df8779bf0a0f28ca16503ee34095786858780e1427`
- External production deployment claim: **false / pending**

This closes the repository-level Phase F release-certification gate. It does not close external production deployment, live-provider, measured production SLO/DR, independent security review, or customer-acceptance gates.

## Evidence completed in current test session

### Phase E — Full-stack business acceptance — 2026-09-18 runtime evidence

- Conversation tenant isolation: **PASS**. `scripts/e2e_conversation_tenant_verify.py` passed public conversation creation/read, authenticated tenant-scoped listing, wrong-customer token rejection, cross-tenant public read rejection, and cross-tenant handoff rejection.
- Employee → Run → AI → Result: **PASS**. `scripts/e2e_employee_run_verify.py` passed authentication, commercial-license fixture, employee creation/version/list-get, run creation, terminal result, and the complete Employee → Run → AI → Result flow.
- Files → Knowledge → Memory: **PASS**. `scripts/e2e_files_knowledge_memory_verify.py` passed file upload/list/get/download, knowledge indexing/search, memory creation/search, and the aggregate product acceptance gate.
- Admin / Developer: **PASS**. `scripts/e2e_admin_developer_verify.py` passed non-platform admin denial, developer API-key creation, secret redaction, and API-key revocation.
- Workflow + Approval + Schedule: **PASS**. `scripts/e2e_workflow_approval_schedule_verify.py` passed workflow/version creation, approval create/approve, workflow resume completion, schedule next-run calculation, tenant-scoped schedule read, deactivation, and deletion.
- Phase E aggregate full-stack business acceptance gate: **PASS**. All five official acceptance scripts completed successfully against the current local Docker stack.

These are local Docker/PostgreSQL runtime observations, not GitHub Actions or production-certification evidence.

### P0 — Tenant Isolation + RBAC + Immutable Audit Retention — 2026-09-18 runtime evidence

- Real-stack tenant/RBAC certification: **PASS**. The certification script completed tenant registration, tenant-context isolation, cross-tenant employee/file/knowledge rejection, same-tenant access, RBAC read/write enforcement, and knowledge-search isolation successfully.
- Aggregate gate: **PASS**. `TENANT ISOLATION + RBAC + KNOWLEDGE P0 REAL-STACK CERTIFICATION PASS`.
- Certification fixture cleanup: **PASS**. The certification cleanup now deprovisions fixture tenants through the real lifecycle service instead of deleting tenant-owned data.
- Retention verification: **PASS**. Four certification tenants were retained in PostgreSQL with `status=deprovisioned`; all associated users had `is_active=false`; each tenant retained audit rows including one `edition.deprovisioned` audit event.
- Immutable audit retention gate: **PASS**. `ACTIVE_CERTIFICATION_TENANTS=0` and `IMMUTABLE_AUDIT_RETENTION_CHECK=PASS`.
- Legacy certification fixtures from the earlier destructive-cleanup implementation were also deprovisioned and retained; no tenant DELETE was used for cleanup.
- This evidence verifies local Docker/PostgreSQL runtime behavior and is not a GitHub Actions or production-deployment certification claim.

### Phase D — Webhook + Replay — 2026-09-18 runtime evidence

- Webhook HTTP runtime: **PASS**. Signed JSON webhook accepted with HTTP `202` and created a tenant-scoped delivery with `status=accepted`.
- Webhook deduplication: **PASS**. Re-sending the same `X-Event-Id` returned the same delivery with `duplicate=true`; delivery count remained **1**.
- Webhook dispatch: **PASS**. The durable delivery was processed by the worker and persisted as `dispatched` with `attempts=1` and a linked `WorkflowRun`.
- Replay enqueue: **PASS**. Replaying the delivery was accepted and enqueued through the durable outbox path.
- Replay runtime: **PASS**. Replay produced a second dispatched `WorkflowRun`; the delivery remained `dispatched` with `attempts=1`.
- Fixture cleanup: **PASS**. Runtime fixtures were cleaned without deleting immutable `workflow_versions`; related deliveries/runs/step rows were removed and the test workflow/trigger were deactivated.
- Phase D Webhook + Replay aggregate runtime gate: **PASS**.

These are local Docker/PostgreSQL runtime observations, not GitHub Actions or production-certification evidence.

### Phase A — Trace — 2026-09-18 runtime evidence

- Trace runtime: **PASS**. Run `a94553e5-2702-4815-9278-afc81c2a71d1` returned a tenant-scoped durable trace with `status=success`, 5 events, 19 total tokens, and zero cost.
- Trace event coverage: **PASS**. The trace contained `run.created`, `knowledge.retrieved`, `ai_provider_call`, `ai.provider_call`, and `run.completed`.
- Tenant-scoping: **PASS**. Trace retrieval was performed with the run tenant and returned the expected run only.

These are local Docker/PostgreSQL runtime observations, not GitHub Actions or production-certification evidence.

## Evidence completed in current test session

### Phase C — 2026-09-18 runtime evidence

- Real provider runtime: **PASS**. Customer `a2a96af0-5f64-4dbc-8eec-f299d39b56e3` executed Employee Version `8d75b84f-be51-4f47-a8da-3cc4dc3588a5` successfully through the local runtime boundary; provider call persisted with `status=success`.
- RAG indexing/retrieval: **PASS**. A tenant-scoped `phase-c-refund-policy.txt` knowledge fixture was indexed into 1 chunk using `deterministic-certification`; semantic search returned 1 result with score `0.361478`.
- Full RAG E2E: **PASS**. Run `a94553e5-2702-4815-9278-afc81c2a71d1` completed with `status=success`; provider metadata recorded `rag_enabled=true` and `rag_result_count=1`.
- Audit evidence: **PASS**. The run persisted `run.created`, `knowledge.retrieved`, `ai.provider_call`, and `run.completed`.
- Phase C aggregate runtime gate: **PASS**.

These are local Docker/PostgreSQL runtime observations, not GitHub Actions or production-certification evidence.

### Phase B — 2026-09-17 runtime evidence

- Retry fail-closed runtime: **PASS**. A linked failed employee Run raised `ValidationAppError` with the replacement-blocking message; child count remained **1** before and after execution; no replacement child was created; cleanup passed.
- Timeout runtime: **PASS**. A synthetic expired running WorkflowRun was processed by the timeout sweep and persisted as `timed_out` with `WORKFLOW_TIMEOUT`; cleanup passed.
- Cancellation runtime: **PASS**. A synthetic pending WorkflowRun was cancelled through `cancel_workflow_run` and persisted as `cancelled` with `WORKFLOW_CANCELLED`, cancellation reason, `cancelled_at`, and `completed_at`; cleanup passed.
- Phase B aggregate runtime gate: **PASS**.

These are local Docker/PostgreSQL runtime observations, not GitHub Actions or production-certification evidence.

### Backend — previously recorded evidence

- `pytest -q /app/tests` → **194 passed, 1 warning**
- `pytest -q /app/tests/test_workflow_foundation.py /app/tests/test_workflow_approval.py /app/tests/test_workflow_triggers.py` → **7 passed, 1 warning**
- `pytest -q /app/tests/test_v033_execution_hardening.py /app/tests/test_v038_workflow_versioning_contract.py` → **8 passed**
- Phase B focused retry/timeout/cancellation suites → **30 passed** across the recorded focused runs.

The known warning is the Python `crypt` deprecation emitted through Passlib; it is not currently a test failure.

### Docker runtime

The local stack was observed healthy:

- API — healthy
- Frontend — healthy
- PostgreSQL — healthy
- Redis — healthy
- Worker — running
- Beat — running

Worker logs show recurring `outbox.dispatch`, `workflow.schedule_tick`, `workflow.timeout_sweep`, and `workflow.approval_expiry` tasks completing successfully.

### Production Certification workflow correction

The Production Certification workflow previously hard-coded the old migration revision `v111releaseidentity` when checking for a single Alembic head. The current migration graph has progressed through the RC9 merge chain and ends at `rc9merge04`.

The certification workflow has therefore been corrected to assert **exactly one Alembic head dynamically** using:

`alembic heads | grep -c '(head)'`

The same dynamic assertion is used for the production-like Docker API container.

### Post-release productization evidence — 2026-08-22

Detailed evidence is recorded in `docs/current/08_POST_RELEASE_PRODUCTIZATION_TEST_EVIDENCE_2026-08-22.md`.

- [x] Authenticated password-change implementation and Settings → Security / Password surface completed.
- [x] Password reset flow manually verified successfully by the project owner.
- [x] Password Security UX validation and re-authentication flow added.
- [x] Tenant lifecycle transition tests added for active/suspended/deprovisioned states.
- [x] Tenant deprovisioning child-dependency guard added and tested.
- [x] Tenant deprovisioning preserves data and disables tenant users rather than deleting tenant data.
- [x] Vendor → Reseller → Customer direct-parent and edition boundaries preserved by lifecycle operations.
- [x] Lifecycle actions remain auditable.
- [x] PR #29, PR #30 and PR #31 changes are included in the current `main` lineage.

These are post-release productization/security evidence, not a new production-certification claim.

## What can be tested from GitHub

- Repository structure and source/test presence
- Workflow definitions and their static correctness
- Migration graph source and revision relationships
- Documentation/release-state consistency
- GitHub Actions results when a workflow run exists
- Pull request/commit review and source-level inspection

## What must be tested locally

- Docker Compose runtime behavior
- Real PostgreSQL/Redis/Celery interaction
- Real provider/LM Studio behavior
- Browser/Playwright execution against the local stack
- OCR runtime/container dependencies
- Load and recovery rehearsal
- Backup/restore
- Real webhook/payment integrations
- Production deployment target and secrets

## Next test order

1. Execute the remaining external production-readiness sequence against the accepted `v1.4.7` release: real target deployment, backup/restore and RPO/RTO, live providers, Vendor → Reseller → Client runtime isolation/RBAC, deployed DAST, independent security review, network/secrets lifecycle, HA/failure recovery, incident response/on-call, and customer acceptance.
2. Record every external evidence item against exact release SHA `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`.

**Rule:** Every completed test changes the corresponding `[ ]` to `[x]` here with the command/result recorded in the evidence section or a linked dated evidence document.
