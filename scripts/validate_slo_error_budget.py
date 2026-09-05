#!/usr/bin/env python3
"""Validate the repository SLO/error-budget engineering contract.

This validator intentionally uses deterministic synthetic observations. It does
not claim production traffic, production SLA compliance, or customer acceptance.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Objective:
    name: str
    target: float
    window_days: int
    description: str


OBJECTIVES = (
    Objective("api_availability", 0.995, 30, "Successful API requests / eligible API requests"),
    Objective("api_5xx_rate", 0.005, 30, "HTTP 5xx requests / eligible API requests"),
    Objective("api_p95_latency", 0.95, 30, "At least 95% of API requests complete within the latency threshold"),
)

SYNTHETIC = {
    "eligible_requests": 100_000,
    "successful_requests": 99_700,
    "http_5xx": 300,
    "latency_within_threshold": 96_000,
}


def build_evidence() -> dict:
    availability = SYNTHETIC["successful_requests"] / SYNTHETIC["eligible_requests"]
    error_rate = SYNTHETIC["http_5xx"] / SYNTHETIC["eligible_requests"]
    latency_ratio = SYNTHETIC["latency_within_threshold"] / SYNTHETIC["eligible_requests"]
    return {
        "mode": "deterministic-engineering-simulation",
        "window": "30d-planning-window",
        "objectives": [asdict(o) for o in OBJECTIVES],
        "observations": SYNTHETIC,
        "results": {
            "api_availability": availability,
            "api_5xx_rate": error_rate,
            "api_p95_latency_objective_ratio": latency_ratio,
        },
        "error_budget": {
            "availability_allowed_failure_ratio": 1 - OBJECTIVES[0].target,
            "availability_remaining_ratio": max(0.0, availability - OBJECTIVES[0].target) / (1 - OBJECTIVES[0].target),
            "five_xx_allowed_ratio": OBJECTIVES[1].target,
            "five_xx_remaining_ratio": max(0.0, OBJECTIVES[1].target - error_rate) / OBJECTIVES[1].target,
        },
        "production_certification_claimed": False,
    }


def main() -> None:
    evidence = build_evidence()
    assert evidence["results"]["api_availability"] >= OBJECTIVES[0].target
    assert evidence["results"]["api_5xx_rate"] <= OBJECTIVES[1].target
    assert evidence["results"]["api_p95_latency_objective_ratio"] >= OBJECTIVES[2].target
    with open("slo-error-budget-evidence.json", "w", encoding="utf-8") as fh:
        json.dump(evidence, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("SLO_ERROR_BUDGET_CONTRACT=PASS")
    print(json.dumps(evidence["results"], sort_keys=True))


if __name__ == "__main__":
    main()
