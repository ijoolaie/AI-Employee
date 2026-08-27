# AI-Employee Documentation

This directory is the canonical source for project documentation.

## Start here

- [Current Status](current/STATUS.md) — the single current snapshot of what is actually implemented, verified, and still unproven.
- [Architecture](architecture/README.md) — architecture decisions and boundaries.
- [Operations](operations/README.md) — deployment, recovery, observability, and production procedures.
- [Releases](releases/README.md) — release and certification records.
- [Archive](archive/README.md) — historical snapshots retained for traceability.

## Documentation rules

1. `docs/current/STATUS.md` is the canonical current status. Do not maintain competing status matrices elsewhere.
2. A feature is **AS-BUILT** only when implementation exists in the repository. Documentation alone is not evidence.
3. A feature is **VERIFIED** only when the relevant automated tests/checks pass.
4. A feature is **PRODUCTION-PROVEN** only when runtime/external evidence exists. CI success is not production certification.
5. Historical documents are immutable records. If their content becomes stale, do not silently rewrite history; add or update the current status instead.
6. Every new certification or execution record should link back to the current status and identify the exact commit/environment where evidence was collected.

## Status vocabulary

| Status | Meaning |
|---|---|
| AS-BUILT | Implementation is present in source code. |
| VERIFIED | Relevant automated verification passes. |
| PARTIAL | Some implementation/evidence exists, but an important boundary remains unverified. |
| BLOCKED | A current failing check prevents claiming verification. |
| EXTERNAL-PENDING | Implementation may be ready, but real external/runtime evidence is missing. |
| DEFERRED | Explicitly outside the current execution scope. |

## Current baseline

The current implementation baseline is **V1.4**. The current source of truth is the status document above, not older release notes or planning matrices.
