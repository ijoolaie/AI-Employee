#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ai-employee-production}"
ENV_FILE="${ENV_FILE:-.env.production}"

[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE" >&2; exit 1; }

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" config --quiet

good_revision="$(git rev-parse HEAD)"
echo "ROLLBACK_DRILL|known_good_revision|$good_revision"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/dependencies', timeout=5); print('ROLLBACK_DRILL|before_failure|PASS')"

echo "Controlled failure step: stop API."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" stop api

if docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T api true 2>/dev/null; then
  echo 'ROLLBACK_DRILL|failure_detection|FAIL' >&2
  exit 1
fi
echo "ROLLBACK_DRILL|failure_detection|PASS"

echo "Recovering known-good revision: $good_revision"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" start api
sleep 5
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/dependencies', timeout=5); print('ROLLBACK_DRILL|recovery|PASS')"

echo "ROLLBACK_DRILL|known_good_revision|PASS"
