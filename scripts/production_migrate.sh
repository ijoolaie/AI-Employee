#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib/docker_compat.sh
source "$SCRIPT_DIR/lib/docker_compat.sh"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
LOCAL_OVERRIDE="${LOCAL_OVERRIDE:-docker-compose.local-production.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ai-employee-production}"
ENV_FILE="${ENV_FILE:-.env.production}"

[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE." >&2; exit 1; }
[[ -f "$COMPOSE_FILE" ]] || { echo "Missing $COMPOSE_FILE." >&2; exit 1; }

COMPOSE=(docker_compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")
if [[ -f "$LOCAL_OVERRIDE" ]]; then
  COMPOSE+=( -f "$LOCAL_OVERRIDE" )
fi
COMPOSE+=( -p "$PROJECT_NAME" )

compose() {
  "${COMPOSE[@]}" "$@"
}

: "${POSTGRES_USER:?POSTGRES_USER must be set by $ENV_FILE or the environment}"
: "${POSTGRES_DB:?POSTGRES_DB must be set by $ENV_FILE or the environment}"

wait_postgres() {
  for _ in $(seq 1 30); do
    if compose exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

echo "PRODUCTION_MIGRATE|infrastructure|starting"
compose up -d postgres redis storage-init

echo "PRODUCTION_MIGRATE|postgres|waiting"
wait_postgres

echo "PRODUCTION_MIGRATE|alembic|upgrade_head"
compose run --rm --no-deps api alembic upgrade head

echo "PRODUCTION_MIGRATE|alembic|current"
current="$(compose run --rm --no-deps api alembic current 2>&1 | tr -d "\r")"
printf "%s\n" "$current"

echo "PRODUCTION_MIGRATE|alembic|heads"
heads="$(compose run --rm --no-deps api alembic heads 2>&1 | tr -d "\r")"
printf "%s\n" "$heads"

current_head="$(printf "%s\n" "$current" | grep -Eo "^[[:alnum:]_]+ \\(head\\)( \\(mergepoint\\))?$" | sed "s/ (head).*//" | sort -u)"
expected_head="$(printf "%s\n" "$heads" | grep -Eo "^[[:alnum:]_]+ \\(head\\)$" | sed "s/ (head)$//" | sort -u)"

[[ -n "$expected_head" ]] || { echo "No Alembic head was reported." >&2; exit 1; }
[[ "$expected_head" != *$'\n'* ]] || { echo "Multiple Alembic heads detected." >&2; exit 1; }
[[ "$current_head" == "$expected_head" ]] || {
  echo "Database migration verification failed: current=$current_head expected=$expected_head" >&2
  exit 1
}

compose run --rm --no-deps api alembic check

echo "PRODUCTION_MIGRATE|verification|PASS"
echo "PRODUCTION_MIGRATE|head|$expected_head"
