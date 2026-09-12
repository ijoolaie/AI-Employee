# Documentation Index

This is the top-level map for current project documentation.

## 1. Start here

| Need | Canonical document |
|---|---|
| Version / release / architecture truth | `00_START_HERE/VERSIONING_TRUTH.md` |
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
| Production server sizing/baseline | `current/PRODUCTION_SERVER_BASELINE.md` |
| Production evidence | `current/PRODUCTION_EVIDENCE_INDEX.md` |
| Production certification execution | `current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md` |
| Code ↔ documentation traceability | `current/CODE_DOCUMENTATION_TRACEABILITY.md` |
| Canonical vocabulary | `current/CANONICAL_VOCABULARY.md` |

## 3. Agent / workforce architecture

- `blueprint/V1.5_AGENTIC_OPERATING_MODEL.md` — Agentic Operating Model baseline.
- `blueprint/STAGE_8_ENGINEERING_EXECUTION_PLAN.md` — governed workforce implementation plan.
- `current/PRODUCTIZATION_ROADMAP.md` — current Agent capability phases: Tool Calling, Structured Arguments, Multi-step, Provider Validation and Release Gate.

## 4. Operations and delivery

- `operations/` — operational runbooks and procedures.
- `releases/` — release records and release-specific evidence.
- `current/PRODUCTION_SERVER_BASELINE.md` — recommended host, topology, secrets, backup and production evidence baseline.

## 5. Historical evidence

- `archive/` — superseded plans, dated audits, release snapshots and historical evidence.
- Historical documents remain traceable but do not override current canonical status.

## 6. Governance

See `DOCUMENTATION_GOVERNANCE.md` for truth hierarchy and reconciliation rules.

### Truth hierarchy

1. Current status.
2. Canonical architecture/release documents.
3. Verified evidence.
4. Planning documents.
5. Historical records.

### Version-axis rule

- `vX.Y.Z` = immutable product release.
- `VX.Y` = architecture generation/baseline.
- `Phase N` = engineering workstream/gate.
- `Stage N` = program/product stage.

### Normalization rule

Do not create parallel status/roadmap/release-truth documents. Update the canonical document when information becomes current; create a dated evidence record only when independent historical traceability is required.
