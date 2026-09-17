#!/usr/bin/env bash
set -euo pipefail

: "${COMPOSE_PROJECT_NAME:=ai-employee-ha-smoke}"
: "${ENV_FILE:=.env.production}"
COMPOSE=(docker compose --env-file "$ENV_FILE" -f docker-compose.production.yml -f docker-compose.local-production.yml -p "$COMPOSE_PROJECT_NAME")
ARTIFACT_DIR="${HA_ARTIFACT_DIR:-artifacts/ha}"
mkdir -p "$ARTIFACT_DIR"

# Load the variables needed by the smoke checks. Strip an optional UTF-8 BOM
# so Windows-authored .env files can be sourced safely from Git Bash.
if [[ -f "$ENV_FILE" ]]; then
  set -a
  source <(sed '1s/^\xEF\xBB\xBF//' "$ENV_FILE")
  set +a
fi

: "${REDIS_PASSWORD:?REDIS_PASSWORD must be set by $ENV_FILE or the environment}"
: "${POSTGRES_USER:?POSTGRES_USER must be set by $ENV_FILE or the environment}"
: "${POSTGRES_DB:?POSTGRES_DB must be set by $ENV_FILE or the environment}"

# Keep one clean, auditable evidence run per invocation.
: > "$ARTIFACT_DIR/recovery-evidence.txt"
: > "$ARTIFACT_DIR/alembic-current.txt"

wait_http() {
  local url="$1"
  for _ in $(seq 1 30); do
    if curl -fsS --max-time 3 "$url" >/dev/null; then return 0; fi
    sleep 2
  done
  return 1
}

wait_postgres() {
  for _ in $(seq 1 30); do
    if "${COMPOSE[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

wait_redis() {
  for _ in $(seq 1 30); do
    if "${COMPOSE[@]}" exec -T redis redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q PONG; then
      return 0
    fi
    sleep 2
  done
  return 1
}

record() { printf '%s\n' "$1" | tee -a "$ARTIFACT_DIR/recovery-evidence.txt"; }

record "HA_FAILURE_RECOVERY_SMOKE=START"
record "COMMIT_SHA=${GITHUB_SHA:-unknown}"
record "STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Bootstrap the dedicated smoke database before any application worker/beat
# can query it. This prevents a fresh PostgreSQL volume from racing Celery's
# outbox dispatcher before migrations create outbox_messages and other tables.
"${COMPOSE[@]}" stop api worker beat frontend >/dev/null 2>&1 || true
"${COMPOSE[@]}" up -d postgres redis storage-init
wait_postgres
wait_redis
record "DEPENDENCY_BOOTSTRAP=PASS"

"${COMPOSE[@]}" run --rm --no-deps api alembic upgrade head
record "ALEMBIC_UPGRADE_HEAD=PASS"

"${COMPOSE[@]}" up -d api worker beat frontend
wait_http "http://127.0.0.1:18000/health"
record "INITIAL_API_HEALTH=PASS"

"${COMPOSE[@]}" restart api
wait_http "http://127.0.0.1:18000/health"
wait_http "http://127.0.0.1:18000/health/dependencies"
record "API_RESTART_RECOVERY=PASS"

"${COMPOSE[@]}" restart worker beat
record "WORKER_BEAT_RESTART=PASS"

"${COMPOSE[@]}" restart redis
wait_redis
wait_http "http://127.0.0.1:18000/health/dependencies"
record "REDIS_RESTART_RECOVERY=PASS"

"${COMPOSE[@]}" restart postgres
wait_postgres
wait_http "http://127.0.0.1:18000/health/dependencies"
"${COMPOSE[@]}" exec -T api alembic current 2>&1 | tee "$ARTIFACT_DIR/alembic-current.txt"
test -s "$ARTIFACT_DIR/alembic-current.txt"
record "ALEMBIC_CURRENT_CAPTURE=PASS"
record "POSTGRES_RESTART_RECOVERY=PASS"
record "COMPLETED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
record "HA_FAILURE_RECOVERY_SMOKE=PASS"
