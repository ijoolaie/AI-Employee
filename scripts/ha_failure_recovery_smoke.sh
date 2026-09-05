#!/usr/bin/env bash
set -euo pipefail

: "${COMPOSE_PROJECT_NAME:=ai-employee-ha-smoke}"
: "${ENV_FILE:=.env.production}"
COMPOSE=(docker compose --env-file "$ENV_FILE" -f docker-compose.production.yml -f docker-compose.local-production.yml -p "$COMPOSE_PROJECT_NAME")
ARTIFACT_DIR="${HA_ARTIFACT_DIR:-artifacts/ha}"
mkdir -p "$ARTIFACT_DIR"

wait_http() {
  local url="$1"
  for _ in $(seq 1 30); do
    if curl -fsS --max-time 3 "$url" >/dev/null; then return 0; fi
    sleep 2
  done
  return 1
}

record() { printf '%s\n' "$1" | tee -a "$ARTIFACT_DIR/recovery-evidence.txt"; }

record "HA_FAILURE_RECOVERY_SMOKE=START"
record "COMMIT_SHA=${GITHUB_SHA:-unknown}"
record "STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

wait_http "http://127.0.0.1:18000/health"
record "INITIAL_API_HEALTH=PASS"

"${COMPOSE[@]}" restart api
wait_http "http://127.0.0.1:18000/health"
wait_http "http://127.0.0.1:18000/health/dependencies"
record "API_RESTART_RECOVERY=PASS"

"${COMPOSE[@]}" restart worker beat
record "WORKER_BEAT_RESTART=PASS"

"${COMPOSE[@]}" restart redis
for _ in $(seq 1 30); do
  if "${COMPOSE[@]}" exec -T redis redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q PONG; then break; fi
  sleep 2
done
wait_http "http://127.0.0.1:18000/health/dependencies"
record "REDIS_RESTART_RECOVERY=PASS"

"${COMPOSE[@]}" restart postgres
for _ in $(seq 1 30); do
  if "${COMPOSE[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then break; fi
  sleep 2
done
wait_http "http://127.0.0.1:18000/health/dependencies"
"${COMPOSE[@]}" exec -T api alembic current | tee "$ARTIFACT_DIR/alembic-current.txt"
record "POSTGRES_RESTART_RECOVERY=PASS"
record "COMPLETED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
record "HA_FAILURE_RECOVERY_SMOKE=PASS"
