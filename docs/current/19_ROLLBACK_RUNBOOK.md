# Rollback Runbook

## Trigger rollback when

- Release health checks fail and cannot be safely remediated forward.
- A migration is incompatible with the supported rollback path.
- Critical customer workflows regress.
- Security or data-integrity risk is detected.

## Procedure

1. Freeze new deployments and record the incident time.
2. Preserve logs, metrics, release manifest and migration state.
3. Confirm the previous known-good release archive and checksum.
4. Confirm the latest verified backup.
5. Follow the migration-specific rollback guidance; never blindly downgrade a database schema.
6. Restore the previous runtime artifact.
7. Restore data only when required by the approved recovery plan.
8. Start the stack and verify health.
9. Run customer acceptance smoke tests.
10. Record final state and incident evidence.

## Guardrails

Rollback is not complete until API/frontend health, worker health, tenant isolation, authentication and critical customer flows pass. If the target release introduced irreversible schema/data changes, use restore-to-known-good rather than an unsafe binary downgrade.
