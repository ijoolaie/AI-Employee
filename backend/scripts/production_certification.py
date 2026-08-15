"""Production certification gate.

Run in a fully provisioned environment after dependencies, database, Redis,
Shopify staging, Stripe test mode and the frontend are configured. This script
never reports external integrations as PASS without explicit evidence.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def env_required(name: str) -> Check:
    value = os.getenv(name, "").strip()
    return Check(name, bool(value), "configured" if value else "missing")


def main() -> int:
    checks = [
        env_required("DATABASE_URL"),
        env_required("REDIS_URL"),
        env_required("SECRET_KEY"),
    ]

    if os.getenv("APP_ENV", "").lower() in {"production", "prod", "staging"}:
        checks.extend([
            env_required("CORS_ORIGINS"),
            env_required("SHOPIFY_CLIENT_ID"),
            env_required("SHOPIFY_CLIENT_SECRET"),
            env_required("STRIPE_SECRET_KEY"),
            env_required("STRIPE_WEBHOOK_SECRET"),
        ])

    failures = [c for c in checks if not c.passed]
    for check in checks:
        print(f"{'PASS' if check.passed else 'FAIL'} {check.name}: {check.detail}")

    if failures:
        print(f"CERTIFICATION BLOCKED: {len(failures)} required checks failed", file=sys.stderr)
        return 1

    print("CERTIFICATION ENVIRONMENT GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
