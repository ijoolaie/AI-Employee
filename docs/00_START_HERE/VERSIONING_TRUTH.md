# Versioning Truth

**Status:** CANONICAL
**Reconciled:** 2026-09-12

This document defines the independent version axes used by the AI Employee Platform.

## 1. Release version

A **Release** is an immutable product snapshot identified by a Git tag and exact commit SHA. Certification, deployment evidence, customer acceptance and rollback evidence attach to that exact SHA.

### Current release truth

- Latest published release: **`v1.4.1`**
- Release commit: **`f7f5062feb125c7ca50263f74a0e40bc4abfa591`**
- `v1.4.1` release assets: **published and verified**.
- `v1.4.1` exact-SHA Production Certification: **PASS** on certification run `34696339261`.
- `v1.4.1` external production deployment: **NOT VERIFIED**.
- Customer acceptance / live provider validation: **PENDING**.

`v1.4.1` is the current engineering-certified release snapshot. It must not be described as externally production-certified until target-specific evidence exists.

Historical certified release `v1.3.8` remains frozen and traceable at `fd1e74b6b4c1701f7443efc202bad161ff19618c`.

## 2. Architecture version

An **Architecture Version** describes the intended platform architecture and operating model. It is not a release identity unless an explicit release record says so.

### Architecture truth

- **V1.4:** frozen architecture foundation.
- **V1.5:** active Agentic Operating Model extension.

V1.5 is an architecture/operating-model baseline, not a separately certified release. It defines the Human + Agent model and governance contracts; implementation claims require code and test evidence.

Canonical architecture document:
`docs/blueprint/V1.5_AGENTIC_OPERATING_MODEL.md`

## 3. Engineering phase

An **Engineering Phase** records implementation work and acceptance gates. Phases are not release numbers.

Current phase truth:

- Phase 11 Unified Execution acceptance: **COMPLETE**
- Phase 12 Test Center: **IMPLEMENTED / OPERATIONAL HARDENING**
- Phase 13 Agent Teams & Marketplace: **ENGINEERING COMPLETE**
- Phase 14.1–14.16: **ENGINEERING COMPLETE WHERE TRACKED**
- Stage 7: **ACTIVE — EXTERNAL PRODUCTION EXECUTION / CERTIFICATION**
- Stage 8: **ACTIVE — GOVERNED AGENT WORKFORCE ENGINEERING**

## 4. New Agent capability workstream

The next focused Agent capability gate is intentionally separate from external production deployment. The capabilities are:

1. **Tool Calling** — model/tool execution contract, allow-listed registry and execution guardrails.
2. **Structured Arguments** — JSON-schema-defined arguments, provider-neutral validation and fail-closed behavior before side effects.
3. **Multi-step** — bounded model → tool → result → model cycles with explicit iteration/step limits and auditability.

These capabilities are substantially present in the current architecture; the new work is acceptance testing and hardening rather than rebuilding the stack from zero.

## 5. How the axes relate

```text
RELEASE
v1.3.8 ─────────► v1.4.0 candidate ─────────► v1.4.1
 frozen            certified candidate          current release
                                                   |
                                                   +-- external production: pending

ARCHITECTURE
V1.4 frozen foundation
        │
        ▼
V1.5 Agentic Operating Model

ENGINEERING
Phase 11 → 12 → 13 → 14.x → Stage 7 external execution
                              └→ Stage 8 governed workforce / Agent capabilities
```

These axes may advance independently.

## 6. Evidence rules

1. A blueprint does not prove implementation.
2. An engineering phase does not create a release.
3. A release tag does not prove external production deployment.
4. CI/browser/production-like evidence does not prove customer acceptance.
5. Certification evidence is bound to the exact commit SHA.
6. No evidence transfers automatically across SHAs.
7. Historical documents remain traceable but cannot override current canonical truth.

## 7. Naming rule

- `vX.Y.Z` → immutable product release.
- `VX.Y` → architecture baseline/generation.
- `Phase N` → engineering workstream/gate.
- `Stage N` → program/product stage.
- `RC` → release candidate.
- `CERTIFIED` → exact-SHA certification evidence exists.
- `PRODUCTION VERIFIED` → independently verified deployment evidence exists.

## 8. Source-of-truth order

For release truth:
1. `docs/releases/RELEASE_TRUTH_LEDGER.md`
2. exact Git tag and commit SHA
3. certification/deployment evidence

For architecture truth:
1. canonical blueprint documents
2. `docs/00_START_HERE/PROJECT_OVERVIEW.md`
3. implementation traceability

For engineering status:
1. `docs/00_START_HERE/CURRENT_STATUS.md`
2. `docs/current/PRODUCTIZATION_ROADMAP.md`
3. phase-specific evidence
4. verified CI/test evidence

If documents disagree, update the canonical document rather than creating a parallel status file.
