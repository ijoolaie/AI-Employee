# Git Tags and Release Reconciliation Policy

**Status:** CANONICAL GOVERNANCE POLICY
**Date:** 2026-08-27

## Why tags are part of project truth

Documentation, branches, commits, Git tags, GitHub releases and CI artifacts are separate evidence sources. Current status must reconcile all of them.

A document claiming a version does not create a Git release.

A Git tag alone does not prove production deployment.

## Release truth hierarchy

For every claimed release, record:

1. Git tag/ref
2. Commit SHA
3. Branch/source
4. GitHub release, if any
5. CI artifact/check evidence
6. Certification document
7. Deployment evidence
8. Production acceptance evidence

## Status labels

- TAGGED
- BUILT
- CERTIFIED
- DEPLOYED
- EXTERNALLY_ACCEPTED

These labels must never be conflated.

## Mandatory audit rule

Every version reconciliation and repository audit must inspect tags and map them to commit and documentation evidence before declaring the current release.

## Current audit action

The existing v1.2.0 release documents are documentation/certification evidence. Tag/ref existence and exact SHA must be verified against Git metadata during the repository ref audit and recorded in the release truth ledger.

## Planned artifact

Create and maintain a Release Truth Ledger containing every relevant tag, its commit SHA, semantic status, evidence and supersession relationship.