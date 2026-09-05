#!/usr/bin/env bash
set -euo pipefail

TARGET_URL="${DAST_TARGET_URL:-http://127.0.0.1:18000/}"
REPORT_DIR="${DAST_REPORT_DIR:-artifacts/dast}"
mkdir -p "$REPORT_DIR"

# OWASP ZAP runs in a disposable container. Use the runner's host network so
# the scan reaches the API port published by Docker Compose on Linux CI.
# This is an engineering gate against the ephemeral target, not a substitute
# for an authenticated production scan or an independent penetration test.
docker run --rm \
  --network host \
  --user 0:0 \
  -v "$PWD/$REPORT_DIR:/zap/wrk:rw" \
  zaproxy/zap-stable:latest \
  zap-baseline.py \
    -t "$TARGET_URL" \
    -J dast-report.json \
    -r dast-report.html \
    -m 3 \
    -I

if [[ ! -s "$REPORT_DIR/dast-report.json" ]]; then
  echo "DAST report was not generated" >&2
  exit 1
fi

python - <<'PY'
import json
from pathlib import Path

report = Path("artifacts/dast/dast-report.json")
data = json.loads(report.read_text(encoding="utf-8"))
site = data.get("site", [])
alerts = []
for entry in site if isinstance(site, list) else []:
    alerts.extend(entry.get("alerts", []) if isinstance(entry, dict) else [])

risk_counts = {}
for alert in alerts:
    risk = str(alert.get("riskdesc", alert.get("riskcode", "Unknown"))).split(" ")[0]
    risk_counts[risk] = risk_counts.get(risk, 0) + 1

summary = {
    "target": "http://127.0.0.1:18000/",
    "alert_count": len(alerts),
    "risk_counts": risk_counts,
}
Path("artifacts/dast/summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
PY
