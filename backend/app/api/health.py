from __future__ import annotations
from typing import Any

async def health() -> dict[str, Any]:
    return {"status": "ok"}

async def readiness(checks: dict[str, bool]) -> dict[str, Any]:
    failed = [name for name, ok in checks.items() if not ok]
    return {
        "status": "ready" if not failed else "not_ready",
        "checks": checks,
        "failed": failed,
    }
