# AI-Employee acceptance checkpoint — 2026-10-31

## Repository and worktree
- Evidence baseline `main` at acceptance execution: `f90211484b0b64f042785cd7f69504ef0449ccd9`; PR #1327 recorded the checkpoint and merged as `46d1407c8171de936556dd616bc68e50fdc023ae`.
- PR #1326 reconciled the start-here docs with main and was merged after CodeQL (Python + JavaScript/TypeScript) and Release identity consistency all passed.
- Original Windows checkout remains dirty and 132 commits behind; it was not reset, cleaned, or fast-forwarded. Acceptance work ran in a separate clean Git worktree from current main.

## PostgreSQL-backed customer identity/order acceptance
- Docker Desktop was started; Docker Engine 29.8.2 responded successfully.
- Reused the existing dedicated container `ai-employee-support-test-postgres` (PostgreSQL 16.15, bound to 127.0.0.1:15433; database `support_test`; user `support_test_user`). The named data volume was preserved.
- Created a custom-format pg_dump backup before schema changes: `support_test_before_migrations.dump` (456,448 bytes).
- Initial Alembic revision: `w23_support_message_attachments`. Applied w24, w25, w26 and w27 successfully. Current revision: `w27_product_inventory_nullable`.
- Targeted verified-email test: `python -m pytest tests/test_public_customer_email_verification_postgres.py -q` → **1 passed in 1.95s**.
- PostgreSQL handoff suite: `python -m pytest tests/test_customer_channel_handoff_postgres.py -q` → **2 passed in 1.73s**.
- Combined focused support/email tests, including the verified-email PostgreSQL test: **92 passed in 1.89s**.
- Additional handoff/notification/dispatcher/email-worker regression group: **25 passed in 2.28s**.
- Expanded customer-support matrix across 18 files (customer channel, multi-turn context/PostgreSQL, email verification, slot filling/PostgreSQL, escalation API/PostgreSQL, handoff/ack/follow-up, outbox, dispatcher, worker): **136 passed in 69.24s**. The first attempt had one environment-only failure because `SUPPORT_TEST_DATABASE_URL_SYNC` was missing; rerunning with both validated async/sync URLs passed.
- Test exercises persisted verification outbox creation, invalid then valid challenge verification, unique same-tenant customer linking, customer-scoped order projection, and fail-closed behavior for stale order sync evidence.

## Non-production SMTP sink proof
- Started isolated Mailpit container `ai-employee-support-mailpit`, bound only to localhost (SMTP 127.0.0.1:1025; UI/API 127.0.0.1:8025).
- Invoked the application's actual `send_email_task` worker against one synthetic customer-verification outbox record with SMTP configured to Mailpit.
- Mailpit API confirmed one received message with subject `Verify your email address`, sender `support@example.test`, and a synthetic `@example.com` recipient.
- PostgreSQL confirmed that exact outbox row reached `dispatched`, had `dispatched_at`, and had no `last_error`.
- This proves local non-production SMTP transport and worker state transition only. It does not prove a real SMTP provider, inbox placement, SPF/DKIM/DMARC, or real-customer delivery.

## Customer handoff notification delivery
- Ran `python -m pytest tests/test_customer_channel_handoff_postgres.py -q` → **2 passed** against the isolated PostgreSQL database. The tests cover tenant-scoped assignment, handoff persistence without creating a new AI Run, tenant-scoped/deduplicated staff notification outbox creation, and persisted retry/dead-letter transitions.
- Selected one synthetic handoff outbox row addressed to `ops@example.test` and invoked the actual `send_email_task` worker with SMTP configured to the local Mailpit sink.
- Mailpit API confirmed receipt of the `Customer requested human support` message at `ops@example.test`; PostgreSQL confirmed that exact outbox row reached `dispatched`, populated `dispatched_at`, and had no `last_error`.
- This verifies configured handoff notification delivery to a local non-production sink. It does not prove a real provider, actual staff ownership/response, or an SLA. Issue #1288 remains open for those operational requirements.

## Handoff notification semantics
- Added `docs/architecture/CUSTOMER_HANDOFF_NOTIFICATION.md` to define the tenant-configured destination, transactional outbox behavior, meaning of `dispatched` versus human acknowledgement, retry/dead/uncertain states, and the explicit absence of an SLA until an owner and measurable policy are approved.

## Remaining acceptance gates — Issue #1258 / #1288
1. Real-provider SMTP validation and a named staff owner plus measurable SLA (#1288).
2. Broader tenant/privacy matrix and multi-turn order/ETA/handoff scenarios.
3. Real customer validation and product discovery.
4. Keep customer-facing claims fail-closed when trusted provider data is stale or unavailable.

PR #1257 remains Draft/on hold pending authenticated real-runtime desktop/mobile evidence and explicit human visual approval. Latest production-certified release remains `v1.4.17`; no production deployment, live Shopify sync, or release promotion is claimed.
