#!/usr/bin/env python3
"""Validate repository-level production network hardening invariants.

This is an engineering contract, not evidence of a deployed network perimeter.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.production.yml"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing {label}: {needle}")


def service_block(compose: str, service: str) -> str:
    match = re.search(rf"(?ms)^  {re.escape(service)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", compose)
    if not match:
        raise AssertionError(f"missing service block: {service}")
    return match.group(0)


def main() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")

    # Production services must not publish host ports directly; ingress belongs
    # to the operator-managed edge/load-balancer layer.
    if re.search(r"(?m)^    ports:", compose):
        raise AssertionError("production compose must not publish host ports")
    require(compose, "networks:\n  backend:\n    driver: bridge", "backend network declaration")

    for service in ("postgres", "redis", "api", "worker", "beat", "frontend"):
        block = service_block(compose, service)
        require(block, "networks: [backend]", f"{service} private backend network")

    # Health checks use loopback, avoiding accidental dependence on published ports.
    require(compose, "127.0.0.1:8000/health/dependencies", "API loopback health check")
    require(compose, "127.0.0.1:3000/login", "frontend loopback health check")

    # Production configuration must enforce rate limiting fail-closed.
    require(compose, 'RATE_LIMIT_ENABLED: "true"', "rate limiting enabled")
    require(compose, 'RATE_LIMIT_FAIL_CLOSED: "true"', "rate limiting fail-closed")

    # External ingress/egress controls and TLS termination remain operator-managed.
    print("PRODUCTION_NETWORK_HARDENING_CONTRACT=PASS")
    print("external_network_perimeter_validation_required=true")
    print("production_certification_claimed=false")


if __name__ == "__main__":
    main()
