# Documentation Index

This is the top-level map for project documentation. Start here, then use the canonical documents below.

## 1. Start here

| Need | Canonical document |
|---|---|
| Project overview | `00_START_HERE/PROJECT_OVERVIEW.md` |
| Current state | `00_START_HERE/CURRENT_STATUS.md` |
| What to do next | `00_START_HERE/CURRENT_PRIORITIES.md` |
| Navigation rules | `00_START_HERE/HOW_TO_NAVIGATE.md` |

## 2. Current implementation and delivery truth

| Topic | Canonical document |
|---|---|
| Implementation / verification | `current/STATUS.md` |
| Delivery roadmap | `current/PRODUCTIZATION_ROADMAP.md` |
| Current documentation set | `current/README.md` |
| Current-state reconciliation | `current/49_CURRENT_STATE_RECONCILIATION_2026-08-31.md` |
| Production-candidate boundary | `current/50_PRODUCTION_CANDIDATE_READINESS_2026-08-31.md` |
| Code ↔ documentation traceability | `current/CODE_DOCUMENTATION_TRACEABILITY.md` |
| Canonical vocabulary | `current/CANONICAL_VOCABULARY.md` |

## 3. Architecture

- `blueprint/` — canonical architecture and operating-model documents.
- `current/01_ARCHITECTURE_AND_MODULE_MAP.md` — implementation-oriented module map.

## 4. Operations and delivery

- `operations/` — operational runbooks and procedures.
- `releases/` — release records and release-specific evidence.
- `current/36_PHASE6E_PRODUCTION_DELIVERY_RUNBOOK.md` — Phase 6E delivery procedure.
- `current/11_DELIVERY_PACKAGE_SPEC.md` — delivery package contract.

## 5. Historical evidence

- `archive/` — superseded plans, dated audits, release snapshots, and historical evidence.
- Historical documents must remain traceable but must not override current status.

## 6. Governance

See `DOCUMENTATION_GOVERNANCE.md` for the truth hierarchy and documentation rules.

### Truth hierarchy

1. Current status.
2. Explicit canonical architecture/release documents.
3. Verified evidence.
4. Planning documents.
5. Historical records.

A higher version number in an older file does not override current truth.

### Normalization rule

Do not create parallel status/roadmap/release-truth documents. Update the canonical document when the information is current; create a dated evidence record only when independent historical traceability is required.
