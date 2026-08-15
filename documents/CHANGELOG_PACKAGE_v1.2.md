# AI Employee Platform — Documentation Package Changelog

## Package: Docs v1.2
**Date:** 2026-08-06
**Previous package:** Docs v1.1

---

## Summary

This package records the outcome of an architecture review requested by the
product owner, covering 10 proposed cross-cutting additions (DDD, Event Bus,
Agent Runtime, Plugin System, Prompt/Workflow Versioning, Audit Log, Cost
Dashboard, Feature Flags, Job Orchestration, Telemetry/Observability).

The review was done against the v1.1 document set **and** the actual state
of the Backend codebase (v0.1.0 — Identity layer only, pre-migration).
No phase sequence was broken; decisions were fit into the existing
Core-First / Backend-first order from `03_Roadmap`.

---

## Files changed in this package

| File | Old version | New version | What changed |
|------|-------------|-------------|---------------|
| **21_CrossCutting_Additions** | — (new) | **v1.0** | New addendum document recording the review: a decision table for all 10 proposed items (accepted / deferred / rejected), detailed rationale per accepted item, and the resulting impact on the Phase 1–3 roadmap |
| 20_Changelog | v1.1 | *unchanged this package* | Not modified — package-level history is now tracked in this file (`CHANGELOG_PACKAGE_v1.2.md`); `20_Changelog` remains the in-document changelog and will be updated in the next full content revision |

## Files unchanged

All other documents remain at their v1.1 package versions:
00 Master Plan, 01 Product Vision, 02 Business Model, 03 Roadmap (v1.1),
04 Architecture, 05 Database, 06 API, 07 Backend, 08 Frontend (v1.1),
09 UI/UX, 10 AI Core (v1.1), 11 Employee Framework, 12 Workflow Engine,
13 Integrations, 14 Security, 15 Deployment, 16 Testing, 17 Marketing,
18 Sales, 19 Finance.

**Note:** `21_CrossCutting_Additions` is a *decision record*, not yet merged
into the body of 04/10/11/12/14. The next content revision (proposed
`v1.3`) should fold the accepted items into those documents directly
(e.g. Audit Log into 04_Architecture §4 and 14_Security, Event Bus into
04_Architecture §4, Feature Flags into 07_Backend) and retire this
addendum once merged.

---

## Review outcome (binding)

**Accepted — added to scope:**
1. DDD-lite domain boundaries (Identity / AI Core / Workflow Engine / Employee Framework) — Phase 1
2. Audit Log as an independent Core module — Phase 1
3. Prompt & Workflow Versioning — confirmed as a non-removable MVP requirement (was already planned) — Phase 1
4. Telemetry & Observability (Trace, Cost, Replay) — confirmed as a non-removable MVP requirement (was already planned) — Phase 1
5. Event Bus (lightweight, Redis pub/sub) — Phase 2
6. Cost Dashboard (UI on top of existing AI Gateway data) — Phase 2
7. Feature Flags (lightweight, in-house) — Phase 2
8. Plugin-ready Employee Contract (formal input/output/tools/rules schema) — Phase 2 design, Phase 3 loader

**Deferred to post-MVP:**
9. Agent Runtime (Planner → Executor → Tool Manager) — Phase 3, only once a real Employee needs multi-step autonomous reasoning inside a single Run

**Rejected:**
10. Job Orchestration as a separate system — fully overlaps `12_Workflow_Engine`; future orchestration needs extend that document instead

Full rationale and the decision table are in `21_CrossCutting_Additions_v1.0.docx`.

---

## How to use this package

- Treat **v1.2 files** as the current source of truth where present, together with `21_CrossCutting_Additions_v1.0`.
- For documents not listed above as changed, content is unchanged from v1.1 and still valid.
- Future package revisions should follow: `AI_Employee_Platform_Docs_v1.3.zip`, `v1.4`, … and include an updated `CHANGELOG_PACKAGE_*.md`.

---

*End of package changelog v1.2*

> **Current-state synchronization (v0.2.9-LMSTUDIO, 2026-08-07):** This document remains authoritative for its planned/design scope. Current implementation status is tracked in `00_AS_BUILT_BASELINE_v0.2.9_LMSTUDIO.md` and `23_AS_BUILT_CURRENT_STATE_v0.2.9.md`. LM Studio is the default local provider; Windows Celery uses `--pool=solo`; the real `.env` is excluded from release packages.

