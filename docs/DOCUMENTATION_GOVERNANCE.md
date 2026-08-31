# Documentation Governance

## Goal

A new contributor should be able to determine:

1. what the project is;
2. where it is now;
3. what is proven;
4. what is planned;
5. what happened previously;
6. what to do next.

## Source-of-truth hierarchy

1. `docs/00_START_HERE/CURRENT_STATUS.md` — executive current state.
2. `docs/current/STATUS.md` — implementation and verification truth.
3. Explicit canonical architecture/release documents.
4. Verified evidence records.
5. Planning documents.
6. Historical/archive records.

A higher version number in an old file does not override current truth.

## Document classes

- **Current/canonical:** maintained and decision-authoritative.
- **Evidence:** dated proof of tests, audits, certifications, or environment observations.
- **Runbook/specification:** operational procedures or stable technical contracts.
- **Historical:** preserved for traceability; never used as current status.

## Required PR checklist

- [ ] Code changed, if applicable
- [ ] Tests updated
- [ ] Current status checked
- [ ] Roadmap checked
- [ ] Architecture updated, if applicable
- [ ] ADR added for significant decisions
- [ ] Migration documented
- [ ] Evidence linked
- [ ] Superseded documents classified
- [ ] No duplicate status/roadmap/release-truth document introduced

## Normalization rules

1. Update an existing canonical document instead of creating a parallel status or roadmap file.
2. Create a dated evidence document only when a point-in-time record has independent traceability value.
3. Historical RC/release/audit records belong under `docs/archive/` or their dedicated historical area.
4. Preserve historical content before deleting or consolidating a document.
5. When two documents contain the same information, retain one canonical copy and classify the other as duplicate/superseded before removal.
6. Never change code or product behavior solely to make documentation appear consistent; reconcile the documentation to verified implementation truth.
