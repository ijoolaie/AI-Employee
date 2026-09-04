#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
LOCAL_OVERRIDE="${LOCAL_OVERRIDE:-docker-compose.local-production.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ai-employee-infra-validation}"
ENV_FILE="${ENV_FILE:-.env.production}"

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -f "$LOCAL_OVERRIDE" -p "$PROJECT_NAME" "$@"
}

backup_file="/tmp/ai-employee-backup-$$.dump"
trap 'compose exec -T postgres rm -f "$backup_file" >/dev/null 2>&1 || true' EXIT

compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 \
  -c "CREATE TABLE IF NOT EXISTS backup_restore_probe(id integer primary key, value text not null);" \
  -c "INSERT INTO backup_restore_probe(id,value) VALUES (1,'backup-restore-pass') ON CONFLICT (id) DO UPDATE SET value=EXCLUDED.value;"

# Use PostgreSQL's real custom-format backup and restore tools inside the database container.
compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f "$backup_file"
compose exec -T postgres pg_restore --list "$backup_file" >/dev/null

restore_db="${POSTGRES_DB}_restore_smoke"
compose exec -T postgres dropdb --if-exists -U "$POSTGRES_USER" "$restore_db" >/dev/null
compose exec -T postgres createdb -U "$POSTGRES_USER" "$restore_db"
compose exec -T postgres pg_restore -U "$POSTGRES_USER" -d "$restore_db" --exit-on-error "$backup_file"
compose exec -T postgres psql -U "$POSTGRES_USER" -d "$restore_db" -v ON_ERROR_STOP=1 \
  -c "SELECT 1 FROM backup_restore_probe WHERE value='backup-restore-pass';"
compose exec -T postgres dropdb -U "$POSTGRES_USER" "$restore_db" >/dev/null

echo 'BACKUP ARTIFACT PASS'
echo 'RESTORE DATABASE PASS'
echo 'BACKUP/RESTORE SMOKE PASS'
