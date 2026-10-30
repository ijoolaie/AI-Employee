# Customer handoff/outbox priority update — 2026-10-30

This dated priority record preserves the actionable guidance introduced by the superseded 2026-10-29 handoff PR #1299, reconciled against the newer master handoff and merged PR #1300.

## Current priorities

1. Treat [Issue #1288](https://github.com/ijoolaie/AI-Employee/issues/1288) as the operational acceptance tracker. The code and automated tests cover tenant-configured notification routing, transactional outbox persistence, deduplication, dispatcher-to-email-worker task handoff, retry/dead-letter behavior, and durable acknowledgement.
2. Keep evidence boundaries explicit: mocked SMTP/worker tests and queued outbox rows do not prove real SMTP delivery, staff ownership/assignment, a response SLA, or customer acceptance. Validate live delivery only in an authorized non-production environment with an explicitly configured tenant destination and SMTP transport.
3. Define a named human owner and measurable response SLA before claiming the handoff is operationally complete. Preserve tenant isolation, deduplication, and the no-new-AI-Run behavior after handoff.
4. Continue [Issue #1061](https://github.com/ijoolaie/AI-Employee/issues/1061) as the MVP/customer-evidence gate: target five decision-maker conversations and at least two concrete sample/trial commitments before broadening integrations.
5. Keep [World visual acceptance #1044](https://github.com/ijoolaie/AI-Employee/issues/1044) deferred. Do not merge draft PR #1257 or begin another redesign before reliability and customer-evidence blockers are addressed.
6. Latest published certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Mainline merges and green CI do not imply production deployment or new release certification.

## Supersession and evidence

- The current detailed implementation/test checkpoint is [AI-Employee master handoff 2026-10-30](AI_EMPLOYEE_MASTER_HANDOFF_2026-10-30.md).
- [PR #1300](https://github.com/ijoolaie/AI-Employee/pull/1300) is merged at `b028f3644aaf4346c7b975726c587da7e8c141b5`; it adds exact dispatcher-to-email-task handoff regression coverage.
- [PR #1301](https://github.com/ijoolaie/AI-Employee/pull/1301) is merged at `ccc9d2245f5a707bb905b38aedcc457bda7fcc71`; it supersedes the stale 2026-10-29 documentation snapshot.
- This file preserves current-priority guidance, not a claim of operational or production acceptance.
