# Version & Release Reconciliation — 2026-08-27

## Status

**Authoritative reconciliation checkpoint**

This document resolves the meaning of the repository's currently overlapping version labels:

- Product/release versions
- Architecture baseline versions
- Documentation-package versions

These namespaces are related, but they are **not interchangeable**.

## Executive decision

### v1.2.0 — CURRENT CERTIFIED CONTROLLED-DEPLOYMENT RELEASE

This is the current authoritative product release line.

Evidence:

- Release Engineering: PASS
- Controlled Deployment Eligibility: PASS
- GitHub Actions release run: `32738347495`
- Runtime and edition artifacts: verified
- External Production Certification: NOT YET CERTIFIED
- Commercial Go-Live: NOT YET CERTIFIED

The current release-truth index remains:

`docs/current/39_RELEASE_TRUTH_V1.2.0.md`

### v1.3.0 — HISTORICAL/UNRECONCILED RELEASE CLAIM

The repository contains `docs/PRODUCTION_HANDOFF_v1.3.0.md`, which claims:

- Status: Production Released
- Release tag validated
- Production certification workflow passed
- Runtime and edition artifacts generated

However, the current authoritative release documentation was explicitly reconciled around **v1.2.0** on 2026-08-24, and the current roadmap identifies v1.2.0 as the certified controlled-deployment release.

Therefore, until immutable tag, workflow run, artifact and certification evidence for v1.3.0 is reconciled into the release-truth system, **v1.3.0 MUST NOT override v1.2.0 as the current release**.

Classification:

**HISTORICAL / UNRECONCILED — NOT CURRENT RELEASE TRUTH**

The stale draft v1.3.1 SaaS Foundation execution branch was also closed as no longer the active execution frontier.

### V1.4 — ARCHITECTURE + EXECUTION BASELINE

V1.4 is not currently equivalent to a `v1.4.0` product release.

Classification:

- Architecture Blueprint: FROZEN
- Execution Baseline: ACTIVE
- Initial implementation wave: COMPLETE
- Product release certification: NOT CLAIMED

Completed initial wave:

1. PR #69 — Tenant/runtime context
2. PR #70 — Knowledge tenant isolation
3. PR #71 — Conversation tenant isolation
4. PR #72 — Scoped API keys
5. PR #73 — Idempotent usage event ledger

A merged PR or successful CI does not equal external production certification.

## Canonical version namespaces

### 1. Product Release Version

Format:

```text
vMAJOR.MINOR.PATCH
```

Examples:

- v1.2.0 — current certified controlled-deployment release
- future v1.3.0 — next product release only when release evidence is reconciled
- future v1.4.0 — product release only after explicit release certification

### 2. Architecture Baseline

Format:

```text
V<baseline> Blueprint
```

Example:

- V1.4 Blueprint — frozen architecture baseline

Architecture baseline numbering does not automatically create a product release.

### 3. Execution Wave

Format:

```text
V<baseline> Execution Wave <n>
```

Example:

- V1.4 Execution Wave 1 — PRs #69–#73

Execution completion does not automatically create a release.

### 4. Documentation Package Revision

Documentation package history may contain labels such as Docs v1.2, Docs v1.3 and Docs v1.4.

These labels are documentation-package revisions and must never be interpreted as product releases without explicit release-truth evidence.

## Version matrix

| Identifier | Namespace | Current classification | Authoritative status |
|---|---|---|---|
| v1.2.0 | Product Release | Certified controlled deployment | CURRENT RELEASE |
| v1.3.0 | Product Release claim | Historical/unreconciled | NOT CURRENT |
| v1.3.1 SaaS Foundation | Execution/planning branch | Superseded | CLOSED / NOT ACTIVE |
| V1.4 Blueprint | Architecture | Frozen | ACTIVE ARCHITECTURE BASELINE |
| V1.4 Execution Wave 1 | Execution | Implemented | COMPLETE INITIAL WAVE |
| Docs v1.2/v1.3/v1.4 | Documentation | Historical package revisions | NOT PRODUCT RELEASES |

## Governance rules

1. Only the current release-truth index may define the current product release.
2. Historical handoff documents cannot supersede current release truth merely because they contain a higher version number.
3. A Blueprint version is not a semantic-release tag.
4. A completed execution wave is not a production release.
5. CI/repository verification and external production certification remain separate evidence layers.
6. A future product release must include immutable tag, source identity, workflow evidence, artifacts/checksums and explicit certification classification.
7. Documentation revisions must identify themselves as documentation revisions when their numbering could be confused with product releases.

## Immediate consequence

The project should continue from this reconciled position:

```text
CURRENT PRODUCT RELEASE
v1.2.0
    |
    +-- External production/commercial gates remain open
    |
ACTIVE ARCHITECTURE/IMPLEMENTATION
V1.4 Blueprint (Frozen)
    |
    +-- Execution Wave 1 complete (#69–#73)
    +-- Next dependency-ordered gap audit/slice
```

No document should currently claim that V1.4 equals a released `v1.4.0`.

## References

- `docs/current/39_RELEASE_TRUTH_V1.2.0.md`
- `docs/current/42_V1.2.0_FINAL_AUDIT_SUMMARY.md`
- `docs/current/43_V1.2.0_RELEASE_CHECKLIST.md`
- `docs/current/09_PRODUCTION_READINESS_STATUS.md`
- `docs/current/PRODUCTIZATION_ROADMAP.md`
- `docs/current/V1.4_EXECUTION_STATUS_2026-08-26.md`
- `docs/PRODUCTION_HANDOFF_v1.3.0.md` (historical/unreconciled claim)
