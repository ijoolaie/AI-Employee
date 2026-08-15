#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[1/5] Starting PostgreSQL + Redis + API + Celery worker + Beat"
docker compose up -d --build postgres redis api worker beat

echo "[2/5] Waiting for API/dependencies"
for _ in $(seq 1 30); do
  if docker compose exec -T api python scripts/e2e_stack_verify.py; then
    break
  fi
  sleep 2
done

echo "[3/5] Applying the complete Alembic chain"
docker compose exec -T api alembic upgrade head

echo "[4/5] Re-checking dependencies after migration"
docker compose exec -T api python scripts/e2e_stack_verify.py

echo "[5/5] Celery worker ping"
docker compose exec -T api celery -A app.workers.celery_app inspect ping --timeout=10

echo "REAL E2E STACK READY"
