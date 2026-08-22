# AI-Employee — A–F Test Tracker

**Status date:** 2026-08-22  
**Repository:** `ijoolaie/AI-Employee`  
**Purpose:** Single living tracker for the current test sequence. Update this document as evidence is completed; do not restart already-passed smoke/contract tests unless a regression requires it.

## PHASE A — Core

- [x] Health — automated/runtime evidence present
- [x] Dependencies — automated/runtime evidence present
- [x] Auth — automated coverage present; full runtime certification remains pending
- [x] Tenant isolation — automated coverage present; full runtime certification remains pending
- [x] Employee — automated coverage present
- [x] Version — automated coverage present
- [x] Run — automated coverage present
- [x] Worker — local Docker runtime observed healthy and Celery tasks succeeding
- [ ] Trace — runtime verification pending

## PHASE B — Execution Safety

- [x] Guardrails — automated tests passed
- [x] Tool permissions — automated tests passed
- [x] Failure handling — automated coverage present
- [ ] Retry — runtime verification pending
- [ ] Timeout — runtime verification pending
- [ ] Cancellation — runtime verification pending

## PHASE C — AI

- [ ] Real provider — local provider/runtime verification pending
- [x] Token accounting — automated coverage present
- [x] Cost accounting — automated coverage present
- [x] Prompt assembly — automated coverage present
- [ ] RAG — end-to-end runtime verification pending

## PHASE D — Workflow

- [x] Workflow — automated tests passed
- [x] Trigger — automated tests passed
- [x] Schedule — automated tests passed
- [x] Approval — automated tests passed
- [ ] Webhook — runtime/API verification pending
- [ ] Replay — runtime verification pending

## PHASE E — Business

- [x] Customer — implementation/test coverage present
- [x] Inbox — implementation/test coverage present
- [x] Sales — implementation/test coverage present
- [x] Commerce — implementation/test coverage present
- [x] Billing — implementation/test coverage present
- [x] Analytics — implementation/test coverage present
- [ ] Full-stack business acceptance — pending

## PHASE F — Production Certification

- [ ] Security — certification pending
- [ ] Tenant isolation — certification pending
- [ ] Load — certification pending
- [ ] Recovery — certification pending
- [ ] Dead letters — certification pending
- [ ] Observability — certification pending

## Evidence completed in current test session

### Backend

- `pytest -q /app/tests` → **194 passed, 1 warning**
- `pytest -q /app/tests/test_workflow_foundation.py /app/tests/test_workflow_approval.py /app/tests/test_workflow_triggers.py` → **7 passed, 1 warning**
- `pytest -q /app/tests/test_v033_execution_hardening.py /app/tests/test_v038_workflow_versioning_contract.py` → **8 passed**

The only warning reported by the full suite is the Python `crypt` deprecation emitted through Passlib; it is not currently a test failure.

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

1. Run the corrected migration-head check locally.
2. Continue Phase A runtime verification: Trace.
3. Continue Phase B: Retry → Timeout → Cancellation.
4. Continue Phase C: Real provider → RAG.
5. Continue Phase D: Webhook → Replay.
6. Run Phase E full-stack business acceptance.
7. Run Phase F production certification.

**Rule:** Every completed test changes the corresponding `[ ]` to `[x]` here with the command/result recorded in the evidence section or a linked dated evidence document.