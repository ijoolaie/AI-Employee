# Customer support explicit human handoff - as-built checkpoint v0.1

Date: 2026-10-25
Branch: `feat/customer-support-human-handoff-20261025`
Base at checkpoint: `fcaf23680ca7d4bd7ccd06a4e1b05b942def6948` (PR #1263 merged to `main`)

## Change

- Recognize a bounded set of explicit English and Persian requests to speak with a human using only the current customer message. Prior transcript text is not used to trigger handoff.
- For a new explicit request with no active AI Run, persist `handoff_requested=true`, `status=human`, and no assignee; save both the customer's request and an acknowledgement as `CustomerMessage` rows.
- Return without creating or queuing a new AI Run. Subsequent messages continue to follow the existing human-handoff boundary and are saved without starting an AI Run.
- If an AI Run is already pending/running/waiting, preserve the existing conflict response rather than changing routing state while execution may still be in flight.
- Acknowledgement does not promise a response time. It is written only after the state change is flushed within the request transaction.

## Validation evidence

- Targeted local tests: `64 passed` across customer-handoff behavior, customer-channel service, support slot filling, and customer-channel tests.
- The PostgreSQL handoff integration test was collected but skipped locally because the dedicated support test database URL is not configured. Its test path was extended to exercise the public customer-message service path against PostgreSQL when that dedicated test database is available.
- Ruff, compileall, and `git diff --check` passed for the changed files.
- Full backend suite has not yet been verified for this change. Exact-head CI and the PostgreSQL integration run remain required before merge.
- No production database, live channel, external provider, or customer data was used. No deployment or release was performed.

## Boundaries / next steps

- This is a persisted conversation routing state, not proof of staff notification, assignment, or response-time SLA.
- Verify the PostgreSQL-backed path and full CI on the exact PR head, then update this checkpoint with actual results.
- Keep MVP customer-demand evidence and the separate World visual-acceptance gate unchanged.
