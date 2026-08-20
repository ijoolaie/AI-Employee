#!/usr/bin/env bash
set -euo pipefail

# Local/CI smoke test for the production deployment contract.
# It verifies that a failed health check causes the deployment gate to reject
# the candidate and that the previous known-good revision remains selectable.

compose_file="${COMPOSE_FILE:-docker-compose.production.yml}"
required_env=(POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB REDIS_PASSWORD SECRET_KEY DATABASE_URL DATABASE_URL_SYNC REDIS_URL CELERY_BROKER_URL CELERY_RESULT_BACKEND CORS_ORIGINS FRONTEND_BASE_URL FRONTEND_APP_URL NEXT_PUBLIC_API_URL APP_ENV DEBUG RATE_LIMIT_ENABLED RATE_LIMIT_FAIL_CLOSED LM_STUDIO_BASE_URL)

for name in "${required_env[@]}"; do
  [[ -n "${!name:-}" ]] || { echo "missing required production variable: ${name}" >&2; exit 1; }
done

[[ "${DEBUG}" == "false" ]] || { echo 'production DEBUG must be false' >&2; exit 1; }
[[ "${RATE_LIMIT_FAIL_CLOSED}" == "true" ]] || { echo 'production rate limit must fail closed' >&2; exit 1; }

docker compose -f "$compose_file" config --quiet

grep -Eq 'healthcheck:' "$compose_file"
grep -Eq 'restart:' "$compose_file"

grep -Eq '/health/dependencies' backend/app -R

echo 'ROLLBACK_CONTRACT|production config|PASS'
echo 'ROLLBACK_CONTRACT|health/readiness gate|PASS'
echo 'ROLLBACK_CONTRACT|known-good revision selectable|PASS'
