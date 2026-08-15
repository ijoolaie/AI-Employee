#!/usr/bin/env bash
set -euo pipefail

: "${BACKUP_PATH:?Set BACKUP_PATH to a backup directory}"
: "${DATABASE_URL_SYNC:?Set DATABASE_URL_SYNC}"
: "${STORAGE_DIR:?Set STORAGE_DIR}"

test -f "$BACKUP_PATH/database.dump"
test -f "$BACKUP_PATH/storage.tar.gz"

if [[ "${CONFIRM_RESTORE:-}" != "YES" ]]; then
  echo "Refusing restore. Set CONFIRM_RESTORE=YES after confirming the target database/storage."
  exit 2
fi

pg_restore --clean --if-exists --no-owner --no-privileges --dbname="$DATABASE_URL_SYNC" "$BACKUP_PATH/database.dump"
mkdir -p "$STORAGE_DIR"
tar -C "$STORAGE_DIR" -xzf "$BACKUP_PATH/storage.tar.gz"

echo "Restore completed. Run the final verification phase before serving traffic."
