#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ai-employee-production}"
ENV_FILE="${ENV_FILE:-.env.production}"

[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE. Copy the documented production template and set local-only secrets." >&2; exit 1; }

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" config --quiet
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" build
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d

echo "Waiting for production services..."
for i in $(seq 1 30); do
  if docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps --format json | grep -q '"Health":"healthy"'; then
    if docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps | grep -q 'api'; then
      echo "LOCAL_PRODUCTION|health|PASS"
      break
    fi
  fi
  sleep 5
done

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/dependencies', timeout=5); print('LOCAL_PRODUCTION|readiness|PASS')"

echo "LOCAL_PRODUCTION|revision|$(git rev-parse HEAD)"
