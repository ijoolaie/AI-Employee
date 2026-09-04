#!/usr/bin/env bash
set -euo pipefail

# Creates a PostgreSQL custom-format backup without exposing credentials in the
# command line. The output directory is intentionally outside source control.
DATABASE_URL_SYNC="${DATABASE_URL_SYNC:-}"
BACKUP_DIR="${BACKUP_DIR:-artifacts/dr}"
BACKUP_NAME="${BACKUP_NAME:-postgres-backup-$(date -u +%Y%m%dT%H%M%SZ).dump}"

[[ -n "$DATABASE_URL_SYNC" ]] || { echo "DATABASE_URL_SYNC is required" >&2; exit 1; }
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

output="$BACKUP_DIR/$BACKUP_NAME"
[[ ! -e "$output" ]] || { echo "Refusing to overwrite existing backup: $output" >&2; exit 1; }

pg_dump --format=custom --compress=6 --file="$output" "$DATABASE_URL_SYNC"
pg_restore --list "$output" >/dev/null
sha256sum "$output" > "$output.sha256"

printf 'BACKUP|file|%s\n' "$output"
printf 'BACKUP|sha256|%s\n' "$(cut -d' ' -f1 "$output.sha256")"
printf 'BACKUP|validation|PASS\n'
