# Backup / Restore Runbook

## Backup policy

Back up the Postgres database and application storage before upgrades and according to the customer's retention policy. Store backups outside the application host when possible and protect them with access controls and encryption.

## Pre-upgrade backup

1. Confirm Postgres is healthy.
2. Create a logical database backup using the approved PostgreSQL tooling.
3. Snapshot/copy the `app_storage` volume using the platform's supported volume backup mechanism.
4. Record backup IDs, timestamps and retention expiry.
5. Verify the backup files are readable before upgrade.

## Restore procedure

1. Stop application writers (API/worker/beat) while preserving database services as appropriate.
2. Restore Postgres into a clean/approved target database.
3. Restore application storage with ownership/permissions matching the production containers.
4. Start dependencies and validate health.
5. Start API, worker, beat and frontend.
6. Run smoke/acceptance checks.

## Restore acceptance

- Database connectivity works.
- Alembic history is coherent.
- Customer authentication works.
- Tenant boundaries remain intact.
- Stored files are accessible.
- Background jobs execute.
- Frontend can reach the API.

Record the restore point, backup identifiers, operator and result. Never overwrite the only known-good backup during recovery.
