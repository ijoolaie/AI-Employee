# Commercial Foundation v2 — 2026-08-24

## Purpose

This document records the controlled extraction of Commercial Production Foundation work from PR #34 onto the current `main` release baseline.

## Baseline

- Current release: `v1.2.0`
- Commercial release channel: Vendor / Reseller / Customer
- Current production-like baseline remains authoritative.
- PR #34 is **not** merged as a whole because its branch is 35 commits behind current `main` and contains stale release workflow/policy changes.

## v2 changes

1. Commercial release admission is aligned to certified `v1.2.0`.
2. New commercial licenses must explicitly declare feature codes.
3. Empty feature sets are fail-closed; only migration-created grandfathered licenses may use an empty set.
4. External-provider subscriptions do not auto-renew when the period timestamp passes. Renewal must be represented by an idempotent provider billing event.
5. Existing commercial execution and tenant-entitlement gates remain in place.

## Intentionally excluded from this extraction

- PR #34's legacy `release-artifact.yml` — current multi-edition release pipeline remains authoritative.
- PR #34's CI cancellation-policy change — certification evidence must not be cancelled by a newer commit.
- Unverified production deployment changes.
- Automatic paid subscription renewal without payment-provider confirmation.

## Acceptance gate

This branch must pass the repository CI, architecture, CodeQL, production-compose validation, and release-manifest checks before merge.

## Follow-up

After merge, complete integration tests for license issuance/revocation, reseller delegation, subscription webhook idempotency, and production deployment evidence before Commercial Go-Live.
