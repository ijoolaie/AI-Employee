# Current Documentation

This directory contains the maintained project documentation for the current `main` implementation line.

## Source of truth

1. `STATUS.md` — implementation and verification truth.
2. `PRODUCTIZATION_ROADMAP.md` — delivery roadmap and phase status.
3. `../00_START_HERE/CURRENT_STATUS.md` — executive current-state summary.
4. `../00_START_HERE/CURRENT_PRIORITIES.md` — immediate execution order.
5. `49_CURRENT_STATE_RECONCILIATION_2026-08-31.md` — latest reconciliation of code, releases, CI, PR history, and roadmap.
6. `50_PRODUCTION_CANDIDATE_READINESS_2026-08-31.md` — current production-candidate boundary and evidence.

## Document classes

- **Canonical/current:** maintained continuously; may be used for decisions.
- **Evidence:** dated records of tests, certification, audits, or environment observations.
- **Runbook/specification:** operational procedures or stable technical contracts.
- **Historical:** retained for traceability but not authoritative for current status.

## Naming convention

- Stable documents use descriptive names without dates when they are continuously maintained.
- Point-in-time evidence uses `YYYY-MM-DD`.
- Historical release/RC records keep their original identity and must not be presented as current status.

## Rule

Do not create another status, roadmap, or release-truth document when an existing canonical document can be updated. Create a dated evidence record only when a point-in-time audit or certification needs independent traceability.
