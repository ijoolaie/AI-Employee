# GitHub Actions Retention Preview

The `Retention Preview (Read Only)` workflow runs daily at 02:17 UTC and can also be started manually.
It reports eligible usage events, terminal/expired employee memories, stale active file metadata, and expired customer conversation slots, grouped by tenant.

## Required one-time configuration

1. Create a GitHub Environment named `retention-preview`.
2. Add environment secret `RETENTION_PREVIEW_DATABASE_URL` pointing to the **Staging** PostgreSQL database, using a dedicated database role with `SELECT` privileges only on `tenants`, `usage_events`, `employee_memories`, `file_objects`, and `customer_conversation_slots`.
3. Add repository variable `RETENTION_PREVIEW_ENABLED=true` only after the secret is configured and verified.
4. Optionally set repository variable `DATA_RETENTION_DAYS` (default `365`, allowed range `1`–`3650`).

The workflow is disabled by default until `RETENTION_PREVIEW_ENABLED` is set. If enabled without the environment secret, it fails closed.

## Safety boundary

- The preview script starts a PostgreSQL `READ ONLY` transaction and issues only `SELECT` statements.
- It does not call `enforce_retention`, commit mutations, delete rows, soft-delete files, or alter schema.
- Do not point this workflow at Production. Do not use an application-owner or write-capable database credential.
- Actual retention execution, scheduler acceptance, object-storage lifecycle, orphan reconciliation, backups, and legal-hold verification remain separate operational gates tracked by Issue #1305.
- GitHub Actions usage is subject to the repository/account plan and included-minute quotas; this avoids Render but is not a guarantee of unlimited free execution. A reachable PostgreSQL database is still required.
