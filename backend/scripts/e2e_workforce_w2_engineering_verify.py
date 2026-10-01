"""Real-stack W2 Engineering Employee semantic certification.

Evidence only: validates tenant-safe workspace artifacts, durable change sets,
provider fail-closed behavior, and approval-gated external delivery semantics.
"""
from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import asyncio

from app.services.workforce_semantic_domains import execute_engineering


async def run() -> None:
    created = await execute_engineering(
        {"_operation": "workspace_create_file", "path": "src/w2.py", "content": "print('w2')"},
        tenant_id="w2-tenant-a",
    )
    assert created["storage_key"].startswith("w2-tenant-a/")
    assert created["path"] == "src/w2.py"

    listed = await execute_engineering({"_operation": "workspace_list"}, tenant_id="w2-tenant-a")
    assert created["storage_key"] in listed["storage_keys"]

    updated = await execute_engineering(
        {
            "_operation": "workspace_edit_file",
            "storage_key": created["storage_key"],
            "content": "print('w2-updated')",
        },
        tenant_id="w2-tenant-a",
    )
    assert updated["updated"] is True

    try:
        await execute_engineering(
            {"_operation": "workspace_read", "storage_key": created["storage_key"]},
            tenant_id="w2-tenant-b",
        )
    except Exception as exc:
        assert "Cross-tenant" in str(exc)
    else:
        raise AssertionError("Cross-tenant workspace read was not rejected")

    first = await execute_engineering(
        {"_operation": "workspace_change_set", "title": "W2 first", "changes": [{"path": "src/w2.py"}]},
        tenant_id="w2-tenant-a",
    )
    second = await execute_engineering(
        {"_operation": "workspace_change_set", "title": "W2 second", "changes": [{"path": "src/w2.py"}]},
        tenant_id="w2-tenant-a",
    )
    assert first["change_set_id"] != second["change_set_id"]
    assert first["storage_key"] != second["storage_key"]

    for operation in ("workspace_test", "workspace_lint", "workspace_build"):
        result = await execute_engineering({"_operation": operation}, tenant_id="w2-tenant-a")
        assert result["executed"] is False
        assert result["provider_required"] is True
        assert result["provider_execution"] == "not_configured"

    deploy = await execute_engineering({"_operation": "deploy_proposal"}, tenant_id="w2-tenant-a")
    contract = await execute_engineering({"_operation": "workspace_test"}, tenant_id="w2-tenant-a")
    assert contract["provider"]["provider"] == "contract-test"
    assert contract["provider_execution"] == "contract_verified"
    assert contract["executed"] is False
    assert deploy["status"] == "proposal"
    assert deploy["approval_required"] is True
    assert deploy["external_side_effect"] is True

    print("W2 TENANT WORKSPACE PASS")
    print("W2 CROSS-TENANT ISOLATION PASS")
    print("W2 DURABLE CHANGE-SET PASS")
    print("W2 PROVIDER FAIL-CLOSED PASS")
    print("W2 DEPLOY APPROVAL GATE PASS")
    print("W2 PROVIDER CONFIGURATION BOUNDARY PASS")
    print("WORKFORCE W2 ENGINEERING SEMANTIC REAL-STACK PASS")


def main() -> None:
    try:
        asyncio.run(run())
    except Exception as exc:
        print(f"WORKFORCE W2 ENGINEERING SEMANTIC REAL-STACK FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
