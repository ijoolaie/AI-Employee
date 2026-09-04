#!/usr/bin/env bash
set -euo pipefail

# Creates a PostgreSQL custom-format backup without exposing the full database
# URI in the pg_dump command line. The output directory is intentionally
# outside source control.
DATABASE_URL_SYNC="${DATABASE_URL_SYNC:-}"
BACKUP_DIR="${BACKUP_DIR:-artifacts/dr}"
BACKUP_NAME="${BACKUP_NAME:-postgres-backup-$(date -u +%Y%m%dT%H%M%SZ).dump}"

[[ -n "$DATABASE_URL_SYNC" ]] || { echo "DATABASE_URL_SYNC is required" >&2; exit 1; }
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

output="$BACKUP_DIR/$BACKUP_NAME"
[[ ! -e "$output" ]] || { echo "Refusing to overwrite existing backup: $output" >&2; exit 1; }

# Keep credentials out of every child process argv. The URI is passed to the
# parser through an inherited file descriptor; parsed libpq fields are then
# exported for pg_dump. The secret must never be logged or copied to artifacts.
eval "$(python - 3<<<"$DATABASE_URL_SYNC" <<'PY'
import os
import shlex
from urllib.parse import parse_qs, unquote, urlsplit

with os.fdopen(3, "r", encoding="utf-8") as stream:
    url = stream.read().rstrip("\n")
parsed = urlsplit(url)
if parsed.scheme not in {"postgres", "postgresql"}:
    raise SystemExit("DATABASE_URL_SYNC must use postgres:// or postgresql://")

values = {
    "PGHOST": parsed.hostname or "",
    "PGPORT": str(parsed.port or "5432"),
    "PGUSER": unquote(parsed.username or ""),
    "PGPASSWORD": unquote(parsed.password or ""),
    "PGDATABASE": unquote(parsed.path.lstrip("/")),
}
for key, vals in parse_qs(parsed.query, keep_blank_values=True).items():
    if key in {"sslmode", "sslrootcert", "sslcert", "sslkey", "application_name"} and vals:
        env_key = "PGAPPNAME" if key == "application_name" else "PG" + key.upper()
        values[env_key] = unquote(vals[-1])

for key, value in values.items():
    if value:
        print(f"export {key}={shlex.quote(value)}")
PY
)"

pg_dump --format=custom --compress=6 --file="$output" --dbname="$PGDATABASE"
pg_restore --list "$output" >/dev/null
sha256sum "$output" > "$output.sha256"

printf 'BACKUP|file|%s\n' "$output"
printf 'BACKUP|sha256|%s\n' "$(cut -d' ' -f1 "$output.sha256")"
printf 'BACKUP|validation|PASS\n'
