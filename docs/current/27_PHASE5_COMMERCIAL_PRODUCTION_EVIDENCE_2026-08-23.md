# Phase 5 — Commercial Production Evidence — 2026-08-23 / reconciled 2026-08-24

## Scope

This evidence record updates the Phase 5 Commercial Production implementation state on branch `phase5-commercial-production-foundation`. It records local execution evidence separately from GitHub Actions and external-production evidence.

## Implementation evidence

The branch contains and tests the following Phase 5 controls:

- Commercial license authority with issuer, tenant and edition binding.
- License issuance/revocation with audit records and fail-closed execution admission.
- Tenant feature entitlement enforcement at the Tool Registry execution boundary.
- Subscription lifecycle transitions for expired trials, cancellation-at-period-end, period renewal and canceled subscriptions.
- Release-channel supported-version and upgrade admission policy for vendor, reseller and customer channels.
- Alembic graph reconciled to a single migration head after the Phase 5 commercial-license migration.

## Local automated evidence

On the Windows working tree, the complete backend suite reached **238 passed** after the Phase 5 implementation slices above.

Focused Phase 5 suites also passed locally:

- commercial license contract tests;
- subscription lifecycle tests;
- feature-entitlement execution-boundary tests;
- release-channel and tenant-upgrade tests;
- existing billing and Stripe contract tests.

This is local automated evidence only. It is not a GitHub Actions result and does not constitute external production certification.

## Local production-like operational evidence

A production-like Docker stack was exercised locally using conflict-safe Windows validation ports:

- API: `127.0.0.1:18000`
- Frontend: `127.0.0.1:13000`
- PostgreSQL: `127.0.0.1:15432`
- Redis: `127.0.0.1:16379`

Observed local readiness:

- API container healthy.
- PostgreSQL container healthy.
- Redis container healthy.
- `/health/dependencies` returned PostgreSQL and Redis `ok`.
- Frontend `/login` returned successfully.

## Backup / restore evidence

`production_dr_restore_smoke.sh` was executed successfully through Git Bash on Windows and produced:

`DR_RESTORE_SMOKE|PASS|PostgreSQL logical restore + Redis AOF restore verified`

This verifies the repository's local PostgreSQL logical-restore and Redis persistence/restore smoke path. It does not prove restore behavior for an external customer production target.

## Recovery / rollback evidence

`local_rollback_drill.sh` was executed successfully against the local production-like stack and produced:

- `RECOVERY_DRILL|before_failure|PASS`
- `RECOVERY_DRILL|failure_detection|PASS`
- `RECOVERY_DRILL|recovery|PASS`
- `RECOVERY_DRILL|known_good_revision|PASS`

Known-good revision recorded by the drill: `fc214360715d194c5057de2da341f0768298751d`.

The drill intentionally stopped the API, verified failure detection, restarted the known-good deployment and verified recovery readiness. This is a local recovery drill, not a live external production rollback.

## Preparation completed without external credentials

The repository now has explicit preparation contracts for the external gates:

- `docs/current/28_PRODUCTION_ENVIRONMENT_PREPARATION.md` defines required target inputs, release admission, deployment sequence and recovery preparation.
- `docs/current/29_COMMERCIAL_SUPPORT_UPDATE_POLICY.md` defines Vendor/Reseller/Customer support responsibilities, escalation, update policy and change control.

These are preparation artifacts only; they do not claim that a real production target, monitoring service, support contact or commercial payment environment has been configured.

## Remaining Phase 5 gates

The following remain explicitly open:

- GitHub Actions validation when Actions capacity is available.
- Real payment/subscriber/revenue evidence for the commercial exit criterion.
- External production deployment evidence per actual environment.
- External monitoring/alerting evidence.
- Production-target rollback/recovery rehearsal.
- Final production security certification.
- Environment-specific commercial support/update-policy contacts and handoff evidence.

## Conclusion

Phase 5 implementation is substantially advanced and the core commercial controls are exercised locally. Evidence preparation for external deployment and commercial handoff is now documented, while GitHub Actions and real-production commercial/operational gates remain environment-dependent.
