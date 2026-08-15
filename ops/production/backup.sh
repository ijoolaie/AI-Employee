#!/usr/bin/env bash
set -euo pipefail

: "${BACKUP_DIR:?Set BACKUP_DIR}"
: "${DATABASE_URL_SYNC:?Set DATABASE_URL_SYNC}"
: "${STORAGE_DIR:?Set STORAGE_DIR}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR/$STAMP"

pg_dump --format=custom --no-owner --no-privileges "$DATABASE_URL_SYNC" > "$BACKUP_DIR/$STAMP/database.dump"
tar -C "$STORAGE_DIR" -czf "$BACKUP_DIR/$STAMP/storage.tar.gz" .
sha256sum "$BACKUP_DIR/$STAMP/"* > "$BACKUP_DIR/$STAMP/SHA256SUMS"

echo "Backup created: $BACKUP_DIR/$STAMP"
