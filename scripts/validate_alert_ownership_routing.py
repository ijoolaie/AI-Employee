"""Validate the repository alert ownership/escalation contract.

This is an engineering contract check. It does not contact a paging provider
and must not be interpreted as proof of live alert delivery.
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate alert-routing.yml") from exc

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "ops" / "alerting" / "alert-routing.yml"
OUT = ROOT / "artifacts" / "alerting" / "alert-ownership-routing-evidence.json"

REQUIRED = {"api_readiness_loss", "worker_degradation"}
SCENARIO_TO_SEVERITY = {
    "api-readiness-loss": "SEV-1",
    "worker-degradation": "SEV-2",
}


def main() -> int:
    data = yaml.safe_load(ROUTES.read_text(encoding="utf-8"))
    assert data.get("external_production_certification_claimed") is False
    routes = data.get("routes")
    assert isinstance(routes, list) and routes

    by_alert = {item.get("alert"): item for item in routes}
    assert REQUIRED <= by_alert.keys(), f"missing required routes: {REQUIRED - by_alert.keys()}"

    evidence_routes = []
    for alert in sorted(REQUIRED):
        route = by_alert[alert]
        scenario = route.get("incident_scenario")
        escalation = route.get("escalation") or {}
        assert route.get("severity") == SCENARIO_TO_SEVERITY[scenario]
        assert route.get("owner") == "platform-on-call"
        assert escalation.get("primary") == route.get("owner")
        assert escalation.get("secondary")
        ack = escalation.get("acknowledgement_sla_minutes")
        assert isinstance(ack, int) and ack > 0
        assert route.get("channel") == "external-paging-target"
        evidence_routes.append(
            {
                "alert": alert,
                "severity": route["severity"],
                "owner": route["owner"],
                "primary": escalation["primary"],
                "secondary": escalation["secondary"],
                "acknowledgement_sla_minutes": ack,
                "channel": route["channel"],
                "incident_scenario": scenario,
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "contract": "alert-ownership-escalation-routing",
                "status": "PASS",
                "production_certification_claimed": False,
                "live_alert_delivery_tested": False,
                "routes": evidence_routes,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print("ALERT_OWNERSHIP_ROUTING_CONTRACT=PASS")
    print(f"EVIDENCE={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
