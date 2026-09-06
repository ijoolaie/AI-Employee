# Current Documentation

This directory contains the maintained project documentation for the current `main` implementation line.

## Source of truth

1. `STATUS.md` — implementation, certification and deployment truth.
2. `PRODUCTIZATION_ROADMAP.md` — delivery roadmap and phase status.
3. `../00_START_HERE/CURRENT_STATUS.md` — executive current-state summary.
4. `../00_START_HERE/CURRENT_PRIORITIES.md` — immediate execution order.
5. `PHASE_14_EXTERNAL_PRODUCTION_EVIDENCE.md` — final external-production/customer-acceptance evidence gate.
6. `PRODUCTION_GAP_REGISTER_2026-09-04.md` — current reconciled gap register.
7. `49_CURRENT_STATE_RECONCILIATION_2026-08-31.md` — retained point-in-time reconciliation evidence.
8. `50_PRODUCTION_CANDIDATE_READINESS_2026-08-31.md` — retained point-in-time candidate evidence; it does not override the current canonical status.

## Current release position

- Certified release candidate: **`v1.3.8`**.
- Certified commit: **`fd1e74b6b4c1701f7443efc202bad161ff19618c`**.
- Certification run: **`34052885700` — PASS**.
- Tag identity: **VERIFIED**.
- Production deployment: **PENDING REAL INFRASTRUCTURE**.
- Deployment attempt `34060615390`: failed during SSH configuration before remote deployment.
- Customer acceptance and live provider validation: **PENDING**.

## Current phase position

- Phase 13 Agent Teams & Marketplace: **engineering complete**.
- Phase 14 engineering: **complete**.
- Phase 14 external production/customer acceptance gate: **external-pending**.

The active external-production work is tracked by issues #210, #19 and #269, with deployment checkpoint #343. No external certification or customer acceptance is inferred from repository/CI evidence.

## Document classes

- **Canonical/current:** maintained continuously; may be used for decisions.
- **Evidence:** dated records of tests, certification, audits, or environment observations.
- **Runbook/specification:** operational procedures or stable technical contracts.
- **Historical:** retained for traceability but not authoritative for current status.

## Naming convention

- Stable documents use descriptive names without dates when continuously maintained.
- Point-in-time evidence uses `YYYY-MM-DD`.
- Historical release/RC records keep their original identity and must not be presented as current status.

## Rule

Do not create another status, roadmap, or release-truth document when an existing canonical document can be updated. Create a dated evidence record only when a point-in-time audit or certification needs independent traceability.
