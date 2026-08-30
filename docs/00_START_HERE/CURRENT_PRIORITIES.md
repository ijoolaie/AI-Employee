# Current Priorities

## Priority 0 — Documentation Truth Reconciliation

Keep roadmap/status documents aligned with merged implementation. The current reconciliation records workspace integration through PR #168 and the subsequent Unified Execution lifecycle/concurrency hardening through PR #189. Current wording must distinguish implementation-complete slices from final runtime acceptance evidence.

## Priority 1 — Finish Unified Execution E2E Acceptance

Complete the final runtime acceptance evidence for the canonical execution contract:

`Human or Agent → WorkItem → authorization/policy → approval when required → execution → audit → result/history`.

The implementation and major acceptance slices are already merged. The remaining work is final runtime evidence reconciliation, gap closure and closure of Issue #170 only after its exit criteria are actually met.

## Priority 2 — Workspace ↔ Execution Integration

Verify Platform, Reseller and Client workspace actions against real WorkItem/Agent APIs and role boundaries. Navigation and route separation are merged; operational behavior and evidence remain the acceptance focus.

## Priority 3 — Runtime Gap Closure & Compatibility

Close discrepancies discovered by E2E acceptance across API contracts, authorization, tenant boundaries, lifecycle behavior, frontend/backend integration and legacy Employee compatibility paths.

## Priority 4 — Test Center & Evidence Expansion

Promote safe, permission-aware testing and repeatable acceptance evidence into workspace workflows where E2E validation requires it. Test Center remains a planned first-class evidence platform, not a prerequisite for every existing acceptance slice.

## Priority 5 — Production Hardening and External Evidence

Continue production hardening, release/certification reconciliation and independent collection of external production evidence. CI success must not be used as a substitute for production acceptance.

## Priority 6 — Downstream Scale and Governance

After the execution substrate and E2E acceptance are operationally stable, continue Agent Teams, evaluations, cost controls, observability, reliability, governance and later Marketplace work according to the roadmap.
