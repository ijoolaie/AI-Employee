#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$(mktemp -d)}"
PG_CONTAINER="${PG_CONTAINER:-dr-postgres}"
REDIS_CONTAINER="${REDIS_CONTAINER:-dr-redis}"
cleanup() {
  docker rm -f "$PG_CONTAINER" "$REDIS_CONTAINER" >/dev/null 2>&1 || true
  rm -rf "$WORKDIR"
}
trap cleanup EXIT

mkdir -p "$WORKDIR"

docker run -d --name "$PG_CONTAINER" \
  -e POSTGRES_USER=druser \
  -e POSTGRES_PASSWORD=drpass \
  -e POSTGRES_DB=drdb \
  postgres:16-alpine >/dev/null

docker run -d --name "$REDIS_CONTAINER" redis:7-alpine \
  redis-server --appendonly yes >/dev/null

for _ in {1..30}; do
  docker exec "$PG_CONTAINER" pg_isready -U druser -d drdb >/dev/null 2>&1 && break
  sleep 1
done
docker exec "$PG_CONTAINER" pg_isready -U druser -d drdb >/dev/null

# Seed PostgreSQL and create a logical backup.
docker exec -i "$PG_CONTAINER" psql -U druser -d drdb <<'SQL'
CREATE TABLE dr_probe (id integer primary key, value text not null);
INSERT INTO dr_probe VALUES (1, 'restore-ok');
SQL

docker exec "$PG_CONTAINER" pg_dump -U druser -d drdb -Fc > "$WORKDIR/postgres.dump"

# Destroy the database state and restore into a fresh database.
docker exec "$PG_CONTAINER" psql -U druser -d postgres -c 'DROP DATABASE drdb;'
docker exec "$PG_CONTAINER" psql -U druser -d postgres -c 'CREATE DATABASE drdb;'
docker exec -i "$PG_CONTAINER" pg_restore -U druser -d drdb --exit-on-error < "$WORKDIR/postgres.dump"
test "$(docker exec "$PG_CONTAINER" psql -U druser -d drdb -tAc "SELECT value FROM dr_probe WHERE id=1")" = "restore-ok"

# Redis: persist a known probe, capture the AOF, recreate the container, and replay it.
docker exec "$REDIS_CONTAINER" redis-cli SET dr:probe restore-ok >/dev/null
docker exec "$REDIS_CONTAINER" redis-cli BGSAVE >/dev/null
sleep 2
docker cp "$REDIS_CONTAINER:/data/appendonlydir" "$WORKDIR/appendonlydir"

docker rm -f "$REDIS_CONTAINER" >/dev/null
docker run -d --name "$REDIS_CONTAINER" redis:7-alpine \
  redis-server --appendonly yes >/dev/null
sleep 1
docker cp "$WORKDIR/appendonlydir" "$REDIS_CONTAINER:/data/"
docker restart "$REDIS_CONTAINER" >/dev/null
for _ in {1..20}; do
  test "$(docker exec "$REDIS_CONTAINER" redis-cli GET dr:probe 2>/dev/null || true)" = "restore-ok" && break
  sleep 1
done
test "$(docker exec "$REDIS_CONTAINER" redis-cli GET dr:probe)" = "restore-ok"

echo 'DR_RESTORE_SMOKE|PASS|PostgreSQL logical restore + Redis AOF restore verified'
