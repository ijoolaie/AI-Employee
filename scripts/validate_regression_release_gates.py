from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(path: str, *fragments: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        raise SystemExit(f"{path}: missing required gate fragments: {missing}")


def main() -> None:
    require(
        ".github/workflows/ci.yml",
        "branches: [main, phase8/workitem-execution-foundation]",
        "'backend/**'",
        "'frontend/**'",
        "'scripts/**'",
        "'docs/releases/**'",
        "'docker-compose*.yml'",
        "Validate Alembic graph traversal",
        "Backend tests",
        "Production build",
    )
    require(
        ".github/workflows/release-artifact.yml",
        "workflow_dispatch:",
        "ref:",
        "Checkout exact release ref",
        "Verify checked-out commit identity",
        "release_commit=$checked_out_sha",
        "Verify base package checksum",
        "Verify Vendor, Reseller and Customer packages",
        "if-no-files-found: error",
    )

    # Keep release validation bound to the exact source identity carried into
    # edition packages. This is a source-level contract check, not production
    # certification or evidence of a deployed release.
    require(
        "scripts/build_edition_packages.py",
        "commit_sha",
    )
    require(
        "scripts/validate_edition_packages.py",
        "commit_sha",
        "checksum mismatch",
    )

    print("REGRESSION_RELEASE_GATE_CONTRACT=PASS")


if __name__ == "__main__":
    main()
