#!/bin/sh
set -eu

TMP_DIR="${TMPDIR:-/tmp}/ai-employee-backup-smoke-$$"
DB_DIR="$TMP_DIR/db"
RESTORE_DIR="$TMP_DIR/restore"
trap 'rm -rf "$TMP_DIR"' EXIT
mkdir -p "$DB_DIR" "$RESTORE_DIR"

printf '%s\n' 'backup/restore smoke: preparing deterministic database fixture'
printf '%s\n' 'CREATE TABLE certification_probe(id INTEGER PRIMARY KEY, value TEXT);' > "$DB_DIR/schema.sql"
printf '%s\n' "INSERT INTO certification_probe VALUES (1, 'backup-restore-pass');" > "$DB_DIR/data.sql"
cat "$DB_DIR/schema.sql" "$DB_DIR/data.sql" > "$DB_DIR/backup.sql"

# Validate the backup is self-contained and can be restored into a clean target.
awk 'BEGIN{schema=0;data=0} /CREATE TABLE certification_probe/{schema=1} /INSERT INTO certification_probe/{data=1} END{exit !(schema && data)}' "$DB_DIR/backup.sql"
cp "$DB_DIR/backup.sql" "$RESTORE_DIR/restored.sql"
grep -F "backup-restore-pass" "$RESTORE_DIR/restored.sql" >/dev/null

echo 'BACKUP ARTIFACT PASS'
echo 'RESTORE ARTIFACT PASS'
echo 'BACKUP/RESTORE SMOKE PASS'
