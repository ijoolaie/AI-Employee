# Versioning Truth

**Status:** CANONICAL
**Reconciled:** 2026-09-21

This document defines the independent version axes used by the AI Employee Platform.

## 1. Release version

A **Release** is an immutable product snapshot identified by a Git tag and exact commit SHA. Certification, deployment evidence, customer acceptance and rollback evidence attach to that exact SHA.

### Current release truth

- Latest published release: **`v1.4.9`**
- Latest certified release: **`v1.4.9`**, exact certified SHA `f1ce20c010779f5273eb5d0051da24cdd57b33f6`.
- `v1.4.9` Git tag: **VERIFIED**, resolving to the certified release commit.
- `v1.4.9` GitHub Release: **PUBLISHED**, not draft, not prerelease.
- `v1.4.9` exact-SHA Production Certification: **PASS** on run `35575615877`, job `106256713583`.
- Evidence artifact: `production-certification-evidence-v1.4.9-f1ce20c010779f5273eb5d0051da24cdd57b33f6`.
- Evidence digest: `sha256:32962353a3511d7d5ae951eb6d0a44620a10211493730544342afe55f980a896`.
- External production deployment: **NOT VERIFIED / not claimed by certification**.
- Customer acceptance / live provider validation: **PENDING**.

`v1.4.9` is the current engineering/release-certified snapshot. It must not be described as externally production-certified until target-specific evidence exists.

Current `main` equals the certified `v1.4.9` SHA. Any subsequent source commit will be outside the certified release snapshot and requires fresh certification before being represented as part of a certified release.

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
- Stage 8: **GOVERNED AGENT WORKFORCE FOUNDATION IMPLEMENTED; ACCEPTANCE/EVIDENCE RECONCILIATION CONTINUES WHERE REQUIRED**
- Stage 9: **CURRENT PLANNED SLICES IMPLEMENTED; PRESENT IN THE CURRENT v1.4.8 RELEASE**

## 4. Stage 9 optimization workstream

Stage 9 is the optimization layer above the governed execution substrate. Its current planned slices were implemented and certified as part of the v1.4.2 release and remain included in the current v1.4.8 release:

1. Capability-aware workload routing.
2. Task/risk/cost-aware model selection.
3. Queue-aware workload balancing.
4. Persisted workload-balancing evidence.
5. Telemetry-backed Agent fitness.
6. Agent version fitness.
7. Promotion evidence.
8. Governed promotion.
9. Governed rollback planning.
10. Workforce capacity forecasting.
11. Governed workforce scaling control loop.

Optimization remains subordinate to identity, policy, approval, budget, lifecycle, concurrency, audit and execution controls.

## 5. Agent capability workstream

The focused Agent capability gate remains separate from external production deployment. The capabilities are:

1. **Tool Calling** — model/tool execution contract, allow-listed registry and execution guardrails.
2. **Structured Arguments** — JSON-schema-defined arguments, provider-neutral validation and fail-closed behavior before side effects.
3. **Multi-step** — bounded model → tool → result → model cycles with explicit iteration/step limits and auditability.
4. **Provider validation** — real-provider validation, starting with LM Studio.
5. **Release gate** — fresh exact-SHA certification for Agent capability code promoted into a release.

These capabilities are substantially present in the architecture; active work should focus on acceptance evidence and hardening rather than rebuilding the stack from zero.

## 6. How the axes relate

```text
RELEASE
v1.3.8 ─────► v1.4.2 ─────► v1.4.5 ─────► v1.4.6 ─────► v1.4.7
 historical     certified      historical     certified      current certified
                                                             |
                                                             +-- external production: pending

ARCHITECTURE
V1.4 frozen foundation
        │
        ▼
V1.5 Agentic Operating Model

ENGINEERING
Phase 11 → 12 → 13 → 14.x → Stage 7 external execution
                              └→ Stage 8 governed workforce foundation
                                  └→ Stage 9 optimization/control loops
```

These axes may advance independently.

## 7. Evidence rules

1. A blueprint does not prove implementation.
2. An engineering phase does not create a release.
3. A release tag does not prove external production deployment.
4. CI/browser/production-like evidence does not prove customer acceptance.
5. Certification evidence is bound to the exact commit SHA.
6. No evidence transfers automatically across SHAs.
7. Historical documents remain traceable but cannot override current canonical truth.

## 8. Naming rule

- `vX.Y.Z` → immutable product release.
- `VX.Y` → architecture baseline/generation.
- `Phase N` → engineering workstream/gate.
- `Stage N` → program/product stage.
- `RC` → release candidate.
- `CERTIFIED` → exact-SHA certification evidence exists.
- `PRODUCTION VERIFIED` → independently verified deployment evidence exists.

## 9. Source-of-truth order

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
