# Current Priorities

## Priority 0 — Documentation Truth Reconciliation

Keep roadmap/status documents aligned with merged implementation. This reconciliation records the completed workspace integration merged through PR #168 and removes stale wording that treated completed Platform/Reseller workspace work as future-only.

## Priority 1 — Unified Execution E2E Acceptance

Validate the real end-to-end execution contract:

`Human or Agent → WorkItem → authorization/policy → approval when required → execution → audit → result/history`.

Acceptance must exercise runtime integration, not only unit or contract tests.

## Priority 2 — Workspace ↔ Execution Integration

Verify Platform, Reseller and Client workspaces against real WorkItem/Agent APIs and role boundaries. Navigation and route separation are merged; remaining acceptance work is operational behavior and evidence.

## Priority 3 — Test Center & Evidence Expansion

Promote safe, permission-aware testing and repeatable acceptance evidence into workspace workflows where E2E validation requires it.

## Priority 4 — Production Hardening and External Evidence

Continue production hardening, release/certification reconciliation and independent collection of external production evidence. CI success must not be used as a substitute for production acceptance.

## Priority 5 — Scale and Governance

Continue Agent Teams, evaluations, cost controls, observability, reliability and production governance after the execution substrate and E2E acceptance are stable.