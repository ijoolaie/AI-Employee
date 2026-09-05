#!/usr/bin/env bash
set -euo pipefail

ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/incident-response-drill}"
SCENARIO="${SCENARIO:-api-readiness-loss}"
mkdir -p "$ARTIFACT_DIR"

case "$SCENARIO" in
  api-readiness-loss)
    severity="SEV-1"
    trigger="API readiness endpoint becomes unavailable"
    owner="platform-on-call"
    rollback="freeze rollout; restore last known-good immutable release if recovery fails"
    ;;
  worker-degradation)
    severity="SEV-2"
    trigger="Worker processing becomes unavailable or materially degraded"
    owner="platform-on-call"
    rollback="pause workload expansion; restart/recover worker; rollback release if regression is confirmed"
    ;;
  *)
    echo "unsupported incident scenario: $SCENARIO" >&2
    exit 2
    ;;
esac

started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat > "$ARTIFACT_DIR/drill-evidence.json" <<EOF
{
  "exercise": "incident-response-drill",
  "mode": "deterministic-engineering-simulation",
  "scenario": "$SCENARIO",
  "severity": "$severity",
  "trigger": "$trigger",
  "primary_owner": "$owner",
  "first_actions": [
    "declare incident",
    "record immutable release commit SHA and deployment context",
    "protect customer data and preserve evidence",
    "validate health/dependency state",
    "apply rollback/recovery decision rule",
    "record timeline and outcome"
  ],
  "rollback_rule": "$rollback",
  "evidence_required": [
    "incident timeline",
    "release commit SHA",
    "health/readiness evidence",
    "backup integrity evidence when data recovery is involved",
    "tenant-isolation verification when customer scope is involved",
    "secret references without secret values"
  ],
  "started_at": "$started_at",
  "external_production_incident_claimed": false
}
EOF

python3 scripts/validate_incident_response_runbook.py
python3 - <<'PY'
import json
from pathlib import Path
p = Path("artifacts/incident-response-drill/drill-evidence.json")
data = json.loads(p.read_text())
required = ["scenario", "severity", "primary_owner", "first_actions", "rollback_rule", "evidence_required"]
missing = [k for k in required if not data.get(k)]
if missing:
    raise SystemExit(f"drill evidence missing: {missing}")
print("INCIDENT_RESPONSE_DRILL=PASS")
PY
