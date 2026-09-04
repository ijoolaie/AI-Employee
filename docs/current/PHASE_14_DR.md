# Phase 14.6 — Disaster Recovery, Backup & Restore

Status: **implemented engineering baseline**.

This runbook defines reproducible database backup/restore mechanics and the boundary between repository evidence and external production certification.

## Recovery objectives

Initial engineering targets (not measured production SLAs):

| Objective | Target | Evidence required for production certification |
| --- | --- | --- |
| RPO | <= 15 minutes | Production backup cadence and measured recovery-point evidence |
| RTO | <= 60 minutes | Timed restore/recovery drill in the production-like target environment |

These targets are planning thresholds. They do not imply that the current deployment has achieved them.

## Backup

Use `scripts/backup_postgres.sh` with an explicit `DATABASE_URL_SYNC` supplied through the environment/secret manager:

```bash
DATABASE_URL_SYNC='postgresql://user:password@host:5432/db' \\
  BACKUP_DIR='artifacts/dr' \\
  ./scripts/backup_postgres.sh
```

The script:

1. creates a PostgreSQL custom-format archive;
2. refuses to overwrite an existing artifact;
3. validates the archive with `pg_restore --list`;
4. records a SHA-256 checksum beside the dump; and
5. prints machine-readable PASS evidence.

Backup artifacts belong in secure backup storage, not Git. The repository's local `artifacts/dr/` path is for operator-created evidence only and must remain ignored by source control.

GitHub Actions artifacts can be used for non-secret evidence, but they are retention-managed and are not a substitute for durable production backup storage. GitHub documents configurable artifact retention and expiration. urlGitHub Actions artifact documentationhttps://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts

## Integrity verification

Use:

```bash
./scripts/verify_postgres_backup.sh artifacts/dr/postgres-backup-<timestamp>.dump
```

Verification checks the optional checksum manifest, validates the PostgreSQL archive table of contents, and requires the `alembic_version` table to be present in the archive.

## Restore

Restore only into an explicitly provisioned, isolated database:

```bash
TARGET_DATABASE_URL='postgresql://user:password@host:5432/aiep_restore' \\
  ./scripts/restore_postgres.sh artifacts/dr/postgres-backup-<timestamp>.dump
```

The restore script refuses the canonical `/aiep` application database name. Operators must restore to a disposable/staging recovery target first, validate migration state and application invariants, and only then proceed with any controlled production recovery procedure.

A production restore must preserve the original database until recovery validation is complete unless the incident runbook explicitly authorizes a cutover.

## Migration strategy

- Normal application rollback is **application rollback first**: redeploy a known-good Git commit/build.
- Database migrations are forward-first and must not be casually downgraded in production.
- Before a migration with destructive or compatibility-sensitive changes, take a verified backup.
- A downgrade is a controlled recovery operation only when the exact downgrade path has been reviewed and tested against the deployed schema/data state.
- If downgrade is unsafe or unavailable, restore the verified backup to an isolated target and use a forward migration/reconciliation plan.
- Keep a single Alembic migration head; migration graph integrity is a release gate.

## Recovery procedure

1. Declare the incident and record the recovery start time.
2. Identify the last known-good application revision and latest verified database backup.
3. Verify the backup checksum and archive table of contents.
4. Provision an isolated recovery database.
5. Restore the backup and verify `alembic_version` plus application-critical integrity checks.
6. Validate the application against the recovered database in a non-customer-serving environment.
7. Select either application redeploy, controlled database recovery, or forward migration/reconciliation.
8. Record actual restore duration and recovered data point to calculate observed RTO/RPO.
9. Cut over only after health, authorization, worker, and data-integrity checks pass.
10. Preserve backup, logs, checksums, revision identifiers, and recovery timestamps as incident evidence.

## Failure handling

- **Backup creation fails:** do not treat the run as a valid recovery point; alert the operator and retain the previous known-good backup.
- **Checksum fails:** quarantine the artifact and restore from another verified recovery point.
- **`pg_restore --list` fails:** artifact is invalid; do not restore it.
- **Restore fails:** preserve the target for forensic evidence, capture logs, and retry from a different verified recovery point rather than modifying the active database.
- **Schema mismatch:** stop cutover and use the migration/reconciliation path; do not improvise destructive downgrades.

## Current repository evidence boundary

Existing repository evidence records a successful PostgreSQL custom backup and isolated temporary restore, including archive validation, 53 restored tables, and migration-marker verification. That evidence is local/runtime evidence, not production certification.

Production certification remains separate and requires measured backup cadence, measured RPO/RTO, durable backup-storage evidence, and a timed production-like restore/cutover drill.
