#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="${1:-}"
TARGET_DATABASE_URL="${TARGET_DATABASE_URL:-}"

[[ -n "$BACKUP_FILE" ]] || { echo "Usage: $0 <backup.dump>" >&2; exit 2; }
[[ -f "$BACKUP_FILE" ]] || { echo "Backup not found: $BACKUP_FILE" >&2; exit 1; }
[[ -n "$TARGET_DATABASE_URL" ]] || { echo "TARGET_DATABASE_URL is required" >&2; exit 1; }

# Safety invariant: restoration requires an explicitly supplied target and is
# never allowed to fall back to DATABASE_URL_SYNC/the active application DB.
if [[ "$TARGET_DATABASE_URL" == *"/aiep" ]]; then
  echo "Refusing restore into the application database; use an isolated target" >&2
  exit 1
fi

pg_restore --clean --if-exists --no-owner --no-privileges \
  --dbname="$TARGET_DATABASE_URL" "$BACKUP_FILE"

# A restored migration marker is the minimum schema-integrity assertion. A
# caller may add domain-specific row-count/checksum assertions after restore.
psql "$TARGET_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -c 'SELECT version_num FROM alembic_version;' >/dev/null

printf 'RESTORE|database|isolated\n'
printf 'RESTORE|integrity|PASS\n'
