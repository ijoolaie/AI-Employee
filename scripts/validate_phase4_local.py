#!/usr/bin/env python3
"""Local Phase 4 delivery validation.

Runs deterministic checks first, then optional Docker-backed checks when Docker
Compose and a production .env are available. Never mutates production data.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "current"
REQUIRED_FILES = [
    "scripts/build_release_package.py",
    "scripts/generate_customer_config.py",
    "config/templates/.env.customer.example",
    "docs/current/14_RELEASE_ARTIFACT_PACKAGE.md",
    "docs/current/15_CONFIG_GENERATION.md",
    "docs/current/16_INSTALLATION_RUNBOOK.md",
    "docs/current/17_UPGRADE_MIGRATION_RUNBOOK.md",
    "docs/current/18_BACKUP_RESTORE_RUNBOOK.md",
    "docs/current/19_ROLLBACK_RUNBOOK.md",
    "docs/current/20_CUSTOMER_ACCEPTANCE_CHECKLIST.md",
    "docs/current/21_SECURITY_SECRETS_CHECKLIST.md",
    "docs/current/22_COMPATIBILITY_MATRIX.md",
    "docs/current/23_HANDOFF_RUNBOOK.md",
    "docs/current/24_PHASE4_DELIVERY_ACCEPTANCE.md",
]


def run(cmd: list[str], *, timeout: int = 120) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (p.stdout + "\n" + p.stderr).strip()
    return p.returncode == 0, output


def check(name: str, ok: bool, detail: str = "") -> bool:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docker", action="store_true", help="run non-destructive Docker Compose validation")
    parser.add_argument("--env-file", default=".env", help="env file used only for compose config")
    args = parser.parse_args()

    results: list[dict[str, str]] = []
    failures = 0

    def record(name: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        check(name, ok, detail)
        results.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
        failures += int(not ok)

    for relative in REQUIRED_FILES:
        record(f"required: {relative}", (ROOT / relative).is_file())

    compose = ROOT / "docker-compose.production.yml"
    record("production compose exists", compose.is_file())

    generator = ROOT / "scripts" / "generate_customer_config.py"
    if generator.is_file():
        ok, output = run([sys.executable, str(generator), "--domain", "validation.example.com"])
        # The generator is expected to be safe to invoke, but its output path is
        # implementation-specific; remove generated validation files if created.
        for candidate in ROOT.glob("*validation*.env"):
            if candidate.is_file():
                candidate.unlink()
        record("config generator smoke test", ok, output[-500:])

    manifest_doc = DOCS / "14_RELEASE_ARTIFACT_PACKAGE.md"
    if manifest_doc.is_file():
        text = manifest_doc.read_text(encoding="utf-8")
        for term in ("RELEASE-MANIFEST.json", "SHA256SUMS", "source_commit_sha"):
            record(f"release contract contains {term}", term in text)

    if compose.is_file():
        text = compose.read_text(encoding="utf-8")
        for term in ("services:", "postgres", "redis"):
            record(f"compose contains {term}", term in text)

    if args.docker:
        if shutil.which("docker") is None:
            record("Docker available", False, "docker executable not found")
        else:
            record("Docker available", True)
            env_file = ROOT / args.env_file
            if env_file.is_file():
                ok, output = run(
                    ["docker", "compose", "--env-file", str(env_file), "-f", str(compose), "config"],
                    timeout=180,
                )
                record("production compose interpolation", ok, output[-1000:])
            else:
                record("production env available for compose validation", False, f"missing {args.env_file}")

    out = ROOT / "dist" / "phase4-validation"
    out.mkdir(parents=True, exist_ok=True)
    report = out / "phase4-local-validation.json"
    report.write_text(json.dumps({"results": results}, indent=2) + "\n", encoding="utf-8")
    print(f"\nReport: {report}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
