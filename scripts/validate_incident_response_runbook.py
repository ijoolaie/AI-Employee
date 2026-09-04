from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "docs/current/PHASE_14_INCIDENT_RESPONSE.md"

REQUIRED_SECTIONS = (
    "## Incident taxonomy",
    "## Severity model",
    "## Ownership boundaries",
    "## Standard response flow",
    "## Rollback and recovery decision rules",
    "## Evidence capture contract",
    "## Operational exercises",
    "## Closure and post-incident review",
    "## Evidence boundary",
)

REQUIRED_REFERENCES = (
    "Phase 14.6",
    "backup integrity",
    "tenant-isolation",
    "secret",
    "commit SHA",
)


def main() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    missing = [item for item in (*REQUIRED_SECTIONS, *REQUIRED_REFERENCES) if item not in text]
    if missing:
        raise SystemExit(f"incident runbook missing required contract fragments: {missing}")

    print("INCIDENT_RESPONSE_RUNBOOK_CONTRACT=PASS")


if __name__ == "__main__":
    main()
