#!/usr/bin/env bash
set -euo pipefail

# Phase 14.10 local certification harness.
# This produces reproducible engineering evidence against the exact checked-out SHA.
# It intentionally does NOT claim external production certification or customer acceptance.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="${CERTIFICATION_OUT_DIR:-$ROOT/artifacts/phase-14-10-local-certification-$TIMESTAMP}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ai-employee-certification}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
LOCAL_OVERRIDE="${LOCAL_OVERRIDE:-docker-compose.local-production.yml}"
PROVIDER_HEALTHCHECK_URL="${PROVIDER_HEALTHCHECK_URL:-}"
KEEP_STACK="${KEEP_STACK:-true}"

mkdir -p "$OUT_DIR"

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -f "$LOCAL_OVERRIDE" -p "$COMPOSE_PROJECT_NAME" "$@"
}

run_capture() {
  local name="$1"; shift
  echo "== $name =="
  if "$@" >"$OUT_DIR/$name.log" 2>&1; then
    echo "PASS" >"$OUT_DIR/$name.status"
    echo "LOCAL_CERTIFICATION|$name|PASS"
  else
    echo "FAIL" >"$OUT_DIR/$name.status"
    echo "LOCAL_CERTIFICATION|$name|FAIL" >&2
    cat "$OUT_DIR/$name.log" >&2
    return 1
  fi
}

GIT_SHA="$(git rev-parse HEAD)"
GIT_REF="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || printf 'detached')"
ARCHIVE_SHA256="$(git archive --format=tar "$GIT_SHA" | sha256sum | awk '{print $1}')"

cat >"$OUT_DIR/identity.env" <<EOF
CERTIFICATION_CLASS=LOCAL_PRODUCTION_LIKE_ENGINEERING_EVIDENCE
CERTIFICATION_STATUS=EXTERNAL_PENDING
UTC_TIMESTAMP=$TIMESTAMP
GIT_SHA=$GIT_SHA
GIT_REF=$GIT_REF
GIT_ARCHIVE_SHA256=$ARCHIVE_SHA256
COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT_NAME
ENV_FILE=$ENV_FILE
EOF

printf '%s\n' "Phase 14.10 local certification harness" >"$OUT_DIR/README.md"
printf '%s\n' "Exact SHA: $GIT_SHA" >>"$OUT_DIR/README.md"
printf '%s\n' "Archive SHA256: $ARCHIVE_SHA256" >>"$OUT_DIR/README.md"
printf '%s\n' "Status: LOCAL_PRODUCTION_LIKE_ENGINEERING_EVIDENCE / EXTERNAL-PENDING" >>"$OUT_DIR/README.md"
printf '%s\n' "No secrets, credentials, access tokens, or customer data belong in this directory." >>"$OUT_DIR/README.md"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE. Copy the documented production template and set local-only secrets." >&2
  exit 1
fi
[[ -f "$LOCAL_OVERRIDE" ]] || { echo "Missing $LOCAL_OVERRIDE." >&2; exit 1; }

run_capture production_completeness_audit python scripts/production_completeness_audit.py
run_capture compose_config compose config --quiet
# Validate the application settings before starting the full stack. This catches malformed
# JSON-backed list/dict environment values early and records the failure without exposing secrets.
run_capture configuration_preflight compose run --rm --no-deps api python -c "from app.core.config import Settings; Settings(); print('CONFIGURATION_PREFLIGHT|PASS')"
run_capture local_production_deploy env COMPOSE_PROJECT_NAME="$COMPOSE_PROJECT_NAME" ENV_FILE="$ENV_FILE" bash scripts/local_production_deploy.sh
run_capture service_snapshot compose ps

run_capture api_dependency_readiness compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/dependencies', timeout=5); print('API_DEPENDENCY_READINESS|PASS')"
run_capture frontend_login curl --fail --silent --show-error http://127.0.0.1:13000/login
run_capture backup_restore_smoke bash scripts/production_backup_restore_smoke.sh
run_capture rollback_drill env COMPOSE_PROJECT_NAME="$COMPOSE_PROJECT_NAME" ENV_FILE="$ENV_FILE" bash scripts/local_rollback_drill.sh
run_capture post_recovery_readiness compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/dependencies', timeout=5); print('POST_RECOVERY_READINESS|PASS')"

if [[ -n "$PROVIDER_HEALTHCHECK_URL" ]]; then
  # Only record status metadata; never log response bodies or authorization headers.
  if curl --fail --silent --show-error --output /dev/null --write-out '%{http_code}' "$PROVIDER_HEALTHCHECK_URL" >"$OUT_DIR/provider_http_status.txt"; then
    echo PASS >"$OUT_DIR/provider_validation.status"
    echo "LOCAL_CERTIFICATION|provider_validation|PASS"
  else
    echo FAIL >"$OUT_DIR/provider_validation.status"
    echo "LOCAL_CERTIFICATION|provider_validation|FAIL" >&2
    exit 1
  fi
else
  echo NOT_EXECUTED >"$OUT_DIR/provider_validation.status"
fi

cat >"$OUT_DIR/EVIDENCE_INDEX.md" <<EOF
# Phase 14.10 — Local Certification Evidence Index

- Certification class: **LOCAL_PRODUCTION_LIKE_ENGINEERING_EVIDENCE**
- Formal Phase 14.10 status: **EXTERNAL-PENDING**
- UTC execution time: \`$TIMESTAMP\`
- Exact Git SHA: \`$GIT_SHA\`
- Git ref: \`$GIT_REF\`
- Git archive SHA256: \`$ARCHIVE_SHA256\`
- Compose project: \`$COMPOSE_PROJECT_NAME\`

## Executed evidence

| Evidence | Result |
| --- | --- |
| Production completeness audit | $(cat "$OUT_DIR/production_completeness_audit.status") |
| Docker Compose configuration | $(cat "$OUT_DIR/compose_config.status") |
| Configuration preflight | $(cat "$OUT_DIR/configuration_preflight.status") |
| Local production-like deployment | $(cat "$OUT_DIR/local_production_deploy.status") |
| Service snapshot | $(cat "$OUT_DIR/service_snapshot.status") |
| API dependency readiness | $(cat "$OUT_DIR/api_dependency_readiness.status") |
| Frontend login endpoint | $(cat "$OUT_DIR/frontend_login.status") |
| Backup/restore smoke | $(cat "$OUT_DIR/backup_restore_smoke.status") |
| Recovery drill | $(cat "$OUT_DIR/rollback_drill.status") |
| Post-recovery readiness | $(cat "$OUT_DIR/post_recovery_readiness.status") |
| Provider healthcheck | $(cat "$OUT_DIR/provider_validation.status") |

## Evidence boundary

This package demonstrates a reproducible local production-like execution against one exact source SHA. It does **not** establish:

- independent external deployment or provider certification;
- measured production SLO/error-budget attainment;
- production RPO/RTO against the real target infrastructure;
- independent security/compliance attestation; or
- Vendor → Reseller → Client customer acceptance.

Those records must be attached separately to the same exact release identity before Phase 14.10 can be marked ACCEPTED or CONDITIONALLY ACCEPTED.

## Secret-safety rule

Do not commit this directory when it contains local environment output. Review generated files before retention or sharing. Never copy credentials, access tokens, database URLs, private keys, or unnecessary personal/customer data into evidence.
EOF

if [[ "$KEEP_STACK" != "true" ]]; then
  compose down --remove-orphans >"$OUT_DIR/compose_down.log" 2>&1 || true
fi

echo "LOCAL_CERTIFICATION|evidence_dir|$OUT_DIR"
echo "LOCAL_CERTIFICATION|status|PASS_ENGINEERING_EVIDENCE_EXTERNAL_PENDING"
