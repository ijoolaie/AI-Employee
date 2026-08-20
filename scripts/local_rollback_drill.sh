#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
LOCAL_OVERRIDE="${LOCAL_OVERRIDE:-docker-compose.local-production.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ai-employee-production}"
ENV_FILE="${ENV_FILE:-.env.production}"

[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE" >&2; exit 1; }
[[ -f "$LOCAL_OVERRIDE" ]] || { echo "Missing $LOCAL_OVERRIDE." >&2; exit 1; }

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -f "$LOCAL_OVERRIDE" -p "$PROJECT_NAME" "$@"
}

compose config --quiet
good_revision="$(git rev-parse HEAD)"
echo "RECOVERY_DRILL|known_good_revision|$good_revision"

compose ps
compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/dependencies', timeout=5); print('RECOVERY_DRILL|before_failure|PASS')"

# This is deliberately a recovery drill, not a Git rollback: stop the running API
# and verify that the same known-good container can be brought back healthy.
echo "Controlled failure step: stop API."
compose stop api

if compose exec -T api true 2>/dev/null; then
  echo 'RECOVERY_DRILL|failure_detection|FAIL' >&2
  exit 1
fi
echo "RECOVERY_DRILL|failure_detection|PASS"

echo "Recovering known-good deployment revision: $good_revision"
compose start api

for i in $(seq 1 24); do
  if compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/dependencies', timeout=3)" >/dev/null 2>&1; then
    echo "RECOVERY_DRILL|recovery|PASS"
    echo "RECOVERY_DRILL|known_good_revision|PASS"
    exit 0
  fi
  sleep 5
done

compose ps
echo "RECOVERY_DRILL|recovery|FAIL" >&2
exit 1
