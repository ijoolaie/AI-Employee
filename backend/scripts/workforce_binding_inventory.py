"""Generate a code-derived workforce binding inventory.

W0 source of truth: ai_workforce_roles.py + Tool Registry. This script never
treats documentation counts as authoritative.
"""
from __future__ import annotations

import json

from app.ai.tool_registry import registry
from app.services.ai_workforce_roles import WORKFORCE_ROLES


def build_inventory() -> dict:
    registered = {tool.name for tool in registry.list()}
    roles = []
    total_bindings = 0
    executable_bindings = 0
    for role in WORKFORCE_ROLES:
        operations = []
        for contract in role.capability_contract:
            if not contract.tool_names:
                status = "unbound"
            elif all(name in registered for name in contract.tool_names):
                status = "registered"
                executable_bindings += 1
            else:
                status = "missing_registered_tool"
            total_bindings += bool(contract.tool_names)
            operations.append({
                "operation": contract.operation,
                "capability_code": contract.capability_code,
                "tools": list(contract.tool_names),
                "approval_required": contract.approval_required,
                "status": status,
            })
        roles.append({"code": role.code, "name": role.name, "operations": operations})
    return {
        "source": ["app/services/ai_workforce_roles.py", "app/ai/tool_registry.py"],
        "role_count": len(WORKFORCE_ROLES),
        "registered_tool_count": len(registered),
        "explicit_binding_count": int(total_bindings),
        "registered_binding_count": executable_bindings,
        "roles": roles,
    }


def main() -> None:
    print(json.dumps(build_inventory(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
