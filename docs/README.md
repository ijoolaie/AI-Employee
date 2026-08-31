# AI-Employee Documentation

This directory is the canonical source for project documentation.

## Start here

- [Documentation Index](DOCUMENTATION_INDEX.md) — source-of-truth map and navigation.
- [Current Status](00_START_HERE/CURRENT_STATUS.md) — executive current state.
- [Current Priorities](00_START_HERE/CURRENT_PRIORITIES.md) — immediate execution order.
- [Current implementation status](current/STATUS.md) — implementation and verification truth.
- [Current documentation set](current/README.md) — maintained documents and conventions.
- [Architecture](architecture/README.md) — architecture decisions and boundaries.
- [Operations](operations/README.md) — deployment, recovery, observability, and production procedures.
- [Releases](releases/README.md) — release and certification records.
- [Archive](archive/README.md) — historical snapshots retained for traceability.

## Documentation rules

1. Current status is authoritative; older release notes and plans do not override it.
2. A feature is **AS-BUILT** only when implementation exists in the repository.
3. A feature is **VERIFIED** only when the relevant automated tests/checks pass.
4. A feature is **PRODUCTION-PROVEN** only when runtime/external evidence exists. CI success is not production certification.
5. Historical documents are preserved for traceability and must be classified rather than silently rewritten.
6. Every new certification or execution record should identify the exact commit and environment where evidence was collected.
7. Do not create competing status, roadmap, or release-truth documents; update the canonical document instead.

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

The current implementation truth is the `main` branch and its current status documents. Architecture lineage includes V1.4 and the V1.5 Human + Agent operating-model extension; version labels in historical planning files do not override current implementation truth.
