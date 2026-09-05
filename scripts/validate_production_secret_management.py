#!/usr/bin/env python3
"""Validate repository-verifiable production secret-management invariants.

This intentionally validates wiring and leakage boundaries only. It never reads
real secret values and never claims that an external secret manager, rotation,
or recovery drill has been executed.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.production.yml"
CONFIG = ROOT / "backend/app/core/config.py"
TEMPLATES = [
    ROOT / "ops/production/production.env.example",
    ROOT / "ops/production/STAGING_ENV.template",
    ROOT / "config/templates/.env.customer.example",
]

CRITICAL = (
    "POSTGRES_PASSWORD",
    "REDIS_PASSWORD",
    "SECRET_KEY",
    "DATABASE_URL",
    "DATABASE_URL_SYNC",
    "REDIS_URL",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
)
OPTIONAL_SECRETS = (
    "LM_STUDIO_API_KEY",
    "ANTHROPIC_API_KEY",
    "SMTP_PASSWORD",
    "BILLING_WEBHOOK_SECRET",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "SHOPIFY_CLIENT_SECRET",
)


def fail(message: str) -> None:
    raise SystemExit(f"SECRET_MANAGEMENT_CONTRACT=FAIL: {message}")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")

    assert_true(COMPOSE.exists(), "production compose is missing")
    assert_true(CONFIG.exists(), "production config is missing")

    # Critical runtime secrets must be required through environment substitution;
    # no literal credential/default may be embedded in the production compose.
    for name in CRITICAL:
        assert_true(
            re.search(rf"{re.escape(name)}:\s*\$\{{{re.escape(name)}:\?", compose),
            f"{name} is not fail-closed in production compose",
        )

    # Optional provider credentials may be absent, but when present they must
    # still come from the environment and may not carry literal secret defaults.
    for name in OPTIONAL_SECRETS:
        matches = re.findall(rf"^\s*{re.escape(name)}:\s*(.+)$", compose, re.MULTILINE)
        assert_true(matches, f"{name} is not declared in production compose")
        for value in matches:
            assert_true("${" in value, f"{name} contains a non-variable literal")
            assert_true(not re.search(r"(?:secret|password|api[_-]?key)[=:]\s*[^$\s]", value, re.I),
                        f"{name} appears to contain a literal secret")

    # Production application config must reject the known weak/default key.
    assert_true("change-me-to-a-long-random-string-in-production" in config,
                "expected weak-secret sentinel is absent from config")
    assert_true("SECRET_KEY" in config and "production" in config.lower(),
                "production SECRET_KEY safety guard is not visible")

    # Checked-in templates may describe where secrets belong, but must not hold
    # usable credential material.
    for path in TEMPLATES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for name in CRITICAL + OPTIONAL_SECRETS:
            for match in re.finditer(rf"(?m)^\s*{re.escape(name)}\s*=\s*(.*)$", text):
                value = match.group(1).strip()
                assert_true(
                    value == "" or value.startswith(("<", "REPLACE_", "${")),
                    f"{path.relative_to(ROOT)} contains a concrete value for {name}",
                )

    # Repository evidence must never serialize secret values into artifacts.
    workflow_root = ROOT / ".github/workflows"
    for workflow in workflow_root.glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")
        assert_true("secrets." not in text or "echo ${{ secrets." not in text,
                    f"{workflow.relative_to(ROOT)} may echo a GitHub secret")
        assert_true("production.env" not in text or "cat" not in text,
                    f"{workflow.relative_to(ROOT)} may serialize a production env file")

    print("SECRET_MANAGEMENT_CONTRACT=PASS")
    print("secret_values_read=false")
    print("external_secret_manager_validation_required=true")
    print("rotation_execution_required=true")
    print("recovery_execution_required=true")
    print("production_certification_claimed=false")


if __name__ == "__main__":
    main()
