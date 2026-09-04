#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
LOCAL_OVERRIDE="${LOCAL_OVERRIDE:-docker-compose.local-production.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ai-employee-infra-validation}"
ENV_FILE="${ENV_FILE:-.env.production}"

[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE" >&2; exit 1; }

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -f "$LOCAL_OVERRIDE" -p "$PROJECT_NAME" "$@"
}

cleanup() {
  compose down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

compose config --quiet
compose build
compose up -d

services=(postgres redis api worker beat frontend)
for service in "${services[@]}"; do
  echo "Waiting for $service..."
  for _ in $(seq 1 36); do
    state="$(compose ps --format json "$service" 2>/dev/null | tr -d '\n')"
    if printf '%s' "$state" | grep -q 'healthy'; then
      echo "INFRA|$service|healthy"
      break
    fi
    if ! compose ps --services --filter status=running | grep -qx "$service"; then
      compose ps
      echo "INFRA|$service|not-running" >&2
      exit 1
    fi
    sleep 5
  done
  state="$(compose ps --format json "$service" 2>/dev/null | tr -d '\n')"
  printf '%s' "$state" | grep -q 'healthy' || { compose ps; echo "INFRA|$service|health-timeout" >&2; exit 1; }
done

# PostgreSQL: write, restart the database container, and verify persistence.
compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 \
  -c "CREATE TABLE IF NOT EXISTS infrastructure_probe(id integer primary key, value text not null);" \
  -c "INSERT INTO infrastructure_probe(id,value) VALUES (1,'postgres-persistence-pass') ON CONFLICT (id) DO UPDATE SET value=EXCLUDED.value;"
compose restart postgres
for _ in $(seq 1 24); do
  if compose exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then break; fi
  sleep 2
done
compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 \
  -c "SELECT 1 FROM infrastructure_probe WHERE value='postgres-persistence-pass';"
echo 'INFRA|postgres|persistence-pass'

# Redis: write, restart the Redis container, and verify AOF-backed persistence.
compose exec -T redis redis-cli -a "$REDIS_PASSWORD" SET infrastructure_probe redis-persistence-pass >/dev/null
compose restart redis
for _ in $(seq 1 24); do
  if compose exec -T redis redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q PONG; then break; fi
  sleep 2
done
[[ "$(compose exec -T redis redis-cli -a "$REDIS_PASSWORD" GET infrastructure_probe | tr -d '\r\n')" == 'redis-persistence-pass' ]]
echo 'INFRA|redis|persistence-pass'

# API dependency endpoint proves API can reach PostgreSQL and Redis after restarts.
compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/dependencies', timeout=5)"
echo 'INFRA|api|dependency-readiness-pass'

# Frontend must remain reachable through the published local validation port.
curl --fail --silent --show-error http://127.0.0.1:13000/login >/dev/null
echo 'INFRA|frontend|http-pass'

# Worker and Beat are validated by their healthchecks; no task is submitted here so this remains deterministic.
echo 'INFRA|worker|healthy'
echo 'INFRA|beat|healthy'
echo 'INFRA|lifecycle|PASS'
