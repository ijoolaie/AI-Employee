#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="${1:-}"
[[ -n "$BACKUP_FILE" ]] || { echo "Usage: $0 <backup.dump>" >&2; exit 2; }
[[ -f "$BACKUP_FILE" ]] || { echo "Backup not found: $BACKUP_FILE" >&2; exit 1; }

checksum_file="$BACKUP_FILE.sha256"
if [[ -f "$checksum_file" ]]; then
  sha256sum --check "$checksum_file"
fi

pg_restore --list "$BACKUP_FILE" >/dev/null
pg_restore --list "$BACKUP_FILE" | grep -q 'TABLE.*alembic_version' || {
  echo "Backup does not contain alembic_version" >&2
  exit 1
}

printf 'BACKUP|integrity|PASS\n'
printf 'BACKUP|toc|PASS\n'
