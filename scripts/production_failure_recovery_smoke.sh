#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-aiep-recovery-smoke}"
BASE_URL="${BASE_URL:-http://127.0.0.1:18000}"

compose() {
  docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "$@"
}

wait_http() {
  local url="$1"
  local attempts="${2:-60}"
  for _ in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "FAIL: timed out waiting for $url" >&2
  return 1
}

check_services() {
  local services=(postgres redis api worker beat frontend)
  for service in "${services[@]}"; do
    local state
    state="$(compose ps --format '{{.Service}} {{.State}}' "$service" | awk -v s="$service" '$1 == s {print $2; exit}')"
    if [[ "$state" != "running" ]]; then
      echo "FAIL: service $service is not running (state=$state)" >&2
      return 1
    fi
  done
}

echo "RECOVERY_SMOKE=START"
check_services
wait_http "$BASE_URL/health"
wait_http "$BASE_URL/health/dependencies"

echo "RECOVERY_SMOKE=RESTART_API"
compose restart api
wait_http "$BASE_URL/health"
wait_http "$BASE_URL/health/dependencies"

for service in worker beat; do
  echo "RECOVERY_SMOKE=RESTART_${service^^}"
  compose restart "$service"
  check_services
  sleep 3
done

for service in redis postgres; do
  echo "RECOVERY_SMOKE=RESTART_${service^^}"
  compose restart "$service"
  check_services
  wait_http "$BASE_URL/health/dependencies"
done

compose exec -T api alembic current >/tmp/aiep-alembic-current.txt
if ! grep -Eq '[0-9a-f]{12,}' /tmp/aiep-alembic-current.txt; then
  echo "FAIL: Alembic current revision was not reported after dependency recovery" >&2
  cat /tmp/aiep-alembic-current.txt >&2
  exit 1
fi

check_services
wait_http "$BASE_URL/health"
wait_http "$BASE_URL/health/dependencies"
echo "RECOVERY_SMOKE=PASS"
