# Documentation Normalization Plan

## Objective

Normalize documentation without deleting evidence or rewriting historical truth.

## Wave A — Complete

- Start Here entry point created.
- Current project orientation created.
- Current priorities created.
- Documentation governance created.
- Source-of-truth index created.

## Wave B — Classification

Review every documentation file and assign one of:

CURRENT, CANONICAL, HISTORICAL, SUPERSEDED, EVIDENCE, TEMPLATE.

No historical evidence is deleted.

## Wave C — Structural normalization

Move or index documents into stable domains:

- 00_START_HERE
- product
- architecture
- workspaces
- agents
- execution
- engineering
- operations
- roadmap
- decisions
- evidence
- archive

Moves must preserve links or provide compatibility redirects/index references.

## Wave D — Drift audit

Compare canonical documentation against:

- backend implementation
- frontend routes/workspaces
- tests and CI
- migrations
- deployment configuration

Any mismatch is recorded as AS-BUILT, PLANNED, PARTIAL or SUPERSEDED.

## Exit gate

Documentation normalization is complete only when a new contributor can identify project purpose, current status, canonical architecture, verified evidence and next implementation phase without interpreting historical files.