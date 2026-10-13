#!/usr/bin/env python3
"""Fail fast when current documentation disagrees on the published release identity.

This check validates consistency, not release validity or external deployment.
The release ledger's first current-identity row and the current manifest must agree;
the current summary documents must carry that same immutable version and SHA.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "PROJECT_MANIFEST_CURRENT.json"
LEDGER = ROOT / "docs/releases/RELEASE_TRUTH_LEDGER.md"
SUMMARY_DOCS = (
    "README.md",
    "docs/00_START_HERE/CURRENT_STATUS.md",
    "docs/00_START_HERE/CURRENT_PRIORITIES.md",
    "docs/00_START_HERE/PROJECT_OVERVIEW.md",
    "docs/00_START_HERE/VERSIONING_TRUTH.md",
    "docs/current/PRODUCTION_EVIDENCE_INDEX.md",
    "docs/current/PRODUCTION_GAP_REGISTER_2026-09-04.md",
    "docs/current/README.md",
)


def fail(message: str) -> None:
    print(f"DOCUMENTATION TRUTH CHECK: FAIL: {message}", file=sys.stderr)


def main() -> int:
    errors: list[str] = []
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        release = manifest["latest_published_release"]
        version = release["version"]
        sha = release["certified_sha"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        fail(f"cannot read manifest latest_published_release: {exc}")
        return 1

    if not re.fullmatch(r"v\d+\.\d+\.\d+", version):
        errors.append(f"manifest release version has unexpected format: {version!r}")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        errors.append(f"manifest certified_sha is not a full lowercase Git SHA: {sha!r}")

    try:
        ledger = LEDGER.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cannot read release truth ledger: {exc}")
        return 1

    rows = re.findall(
        r"^\|\s*`?(v\d+\.\d+\.\d+)`?\s*\|\s*`?([0-9a-f]{40})`?\s*\|",
        ledger,
        flags=re.MULTILINE,
    )
    if not rows:
        errors.append("release ledger has no parseable release-identity table row")
    elif rows[0] != (version, sha):
        errors.append(
            "manifest latest_published_release disagrees with the first/current "
            f"release-ledger row: manifest=({version}, {sha}), ledger={rows[0]}"
        )

    for relative_path in SUMMARY_DOCS:
        path = ROOT / relative_path
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{relative_path}: cannot read file: {exc}")
            continue
        missing = [value for value in (version, sha) if value not in content]
        if missing:
            errors.append(
                f"{relative_path}: missing current release identity value(s): "
                + ", ".join(missing)
            )

    if errors:
        for error in errors:
            fail(error)
        return 1

    print(
        "DOCUMENTATION TRUTH CHECK: PASS: "
        f"{version} / {sha} agrees across manifest, release ledger, "
        f"and {len(SUMMARY_DOCS)} current summary documents."
    )
    print(
        "Scope note: this checks documentation consistency only; it does not "
        "certify a build, deployment, customer acceptance, or revenue."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
