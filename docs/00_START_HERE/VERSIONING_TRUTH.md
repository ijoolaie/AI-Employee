# Versioning Truth

**Status:** CANONICAL  
**Reconciled:** 2026-09-10

This document defines the three independent version axes used by the AI Employee Platform. They must never be treated as interchangeable.

## 1. Release version

A **Release** is an immutable product snapshot identified by a Git tag and an exact commit SHA. Release certification, deployment evidence, customer acceptance and rollback evidence attach to that exact SHA.

### Current release truth

- Certified release candidate: **`v1.3.8`**
- Certified commit: **`fd1e74b6b4c1701f7443efc202bad161ff19618c`**
- Certification run: **`34052885700` — PASS**
- Production deployment: **PENDING REAL INFRASTRUCTURE**
- Customer acceptance / live provider validation: **PENDING**

`v1.3.8` is therefore the current certified release baseline. The current engineering mainline is newer and is **not certified**.

## 2. Architecture version

An **Architecture Version** describes the intended platform architecture and operating model. It is not a release identity unless an explicit release record says so.

### Architecture truth

- **V1.4:** frozen architecture foundation.
- **V1.5:** Agentic Operating Model extension.

V1.5 is currently an **architecture/documentation baseline**, not a separately certified product release. It defines the Human + Agent model and its contracts; it must not be used as evidence that every V1.5 capability is implemented or production-ready.

Canonical document:

`docs/blueprint/V1.5_AGENTIC_OPERATING_MODEL.md`

## 3. Engineering phase

An **Engineering Phase** records implementation work and acceptance gates. Phases are not release numbers and do not automatically change the current release identity.

### Current phase truth

- Phase 11 Unified Execution acceptance: **COMPLETE**
- Phase 12 Test Center P12.1–P12.6: **IMPLEMENTED / OPERATIONAL HARDENING**
- Phase 13 Agent Teams & Marketplace: **ENGINEERING COMPLETE**
- Phase 14.1–14.16: **ENGINEERING COMPLETE for tracked implementation**
- Stage 7 / Phase 14.10 external production/customer acceptance: **EXTERNAL-PENDING**
- Stage 8 governed workforce foundation: **ENGINEERING ACTIVE on mainline / NOT A RELEASE**

## 4. Current engineering baseline

The current `main` baseline is:

`decde0ad333ba972a79053b3da6489f92a2648de`

Since `v1.3.8`, mainline hardening has included governance, provider idempotency, database concurrency, outbox, billing, onboarding, RAG indexing and TeamInstallation scope work. These changes require fresh release certification before they can be represented as certified.

## 5. How the three axes relate

```text
RELEASE
v1.3.8 ───────────────────────────────► next certified release
   │
   │ exact SHA: fd1e74b6...
   │
   └── certification / deployment / acceptance evidence

ARCHITECTURE
V1.4 frozen foundation
        │
        ▼
V1.5 Agentic Operating Model
        │
        ▼
Future architecture extensions

ENGINEERING
Phase 11 ─► Phase 12 ─► Phase 13 ─► Phase 14
                                      │
                                      ▼
                         Stage 8 governance hardening
```

These axes may advance at different times. That is expected.

## 6. Evidence rules

1. A blueprint does not prove implementation.
2. An engineering phase does not create a release.
3. A release tag does not prove external production deployment.
4. CI/browser evidence does not prove customer acceptance.
5. Certification evidence is bound to the exact commit SHA.
6. No evidence may be inherited from another SHA without explicit revalidation.
7. Historical documents remain traceable but cannot override this canonical truth.
8. The current engineering SHA must be distinguished from the current certified release SHA.

## 7. Naming rule for future documents

Use these terms precisely:

- `vX.Y.Z` → immutable product release.
- `VX.Y` → architecture baseline/architecture generation.
- `Phase N` → engineering workstream/gate.
- `RC` → release candidate state.
- `CERTIFIED` → certification evidence exists for the exact SHA.
- `PRODUCTION` → independently verified deployment evidence exists.

Do not write phrases such as `V1.5 release`, `Phase 14 release`, or `v1.3.8 architecture` unless the context explicitly requires them.

## 8. Source-of-truth order

For release truth use:

1. `docs/releases/RELEASE_TRUTH_LEDGER.md`
2. exact Git tag and commit SHA
3. certification/deployment evidence

For architecture truth use:

1. canonical blueprint documents
2. `docs/00_START_HERE/PROJECT_OVERVIEW.md`
3. implementation traceability

For engineering status use:

1. `docs/00_START_HERE/CURRENT_STATUS.md`
2. `docs/current/STATUS.md`
3. phase-specific evidence
4. verified CI/test evidence

If documents disagree, reconcile the canonical document; do not create another parallel status file.
