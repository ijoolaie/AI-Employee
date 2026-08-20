#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
LOCAL_OVERRIDE="${LOCAL_OVERRIDE:-docker-compose.local-production.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ai-employee-production}"
ENV_FILE="${ENV_FILE:-.env.production}"

[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE. Copy the documented production template and set local-only secrets." >&2; exit 1; }
[[ -f "$LOCAL_OVERRIDE" ]] || { echo "Missing $LOCAL_OVERRIDE." >&2; exit 1; }

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -f "$LOCAL_OVERRIDE" -p "$PROJECT_NAME" "$@"
}

compose config --quiet
compose build
compose up -d

echo "Waiting for production services..."
for i in $(seq 1 36); do
  if compose ps --services --filter status=running | grep -qx 'api' && \
     compose ps --services --filter status=running | grep -qx 'frontend'; then
    api_health="$(compose ps --format json api 2>/dev/null | tr -d '\n')"
    frontend_health="$(compose ps --format json frontend 2>/dev/null | tr -d '\n')"
    if printf '%s' "$api_health" | grep -q 'healthy' && printf '%s' "$frontend_health" | grep -q 'healthy'; then
      echo "LOCAL_PRODUCTION|health|PASS"
      break
    fi
  fi
  if [[ "$i" -eq 36 ]]; then
    echo "LOCAL_PRODUCTION|health|FAIL" >&2
    compose ps
    exit 1
  fi
  sleep 5
done

compose ps
compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/dependencies', timeout=5); print('LOCAL_PRODUCTION|readiness|PASS')"

curl --fail --silent --show-error http://127.0.0.1:3000/login >/dev/null
echo "LOCAL_PRODUCTION|frontend|PASS"
echo "LOCAL_PRODUCTION|revision|$(git rev-parse HEAD)"
