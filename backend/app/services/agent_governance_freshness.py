"""Deterministic freshness proofs for execution authority decisions."""
from __future__ import annotations

import hashlib
import json
from typing import Any


FINGERPRINT_KEY = "_governance_fingerprint"


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _canonical(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    return value


def execution_authority_fingerprint(
    *,
    tenant_id: Any,
    template_id: Any,
    template_version: int,
    agent_definition_id: Any,
    risk_tier: int,
    capability_contract: dict | None,
    permission_policy: dict | None,
    approval_policy: dict | None,
    install_policy: dict | None,
    configuration: dict | None,
    max_concurrency: int = 1,
    budget_policy: dict | None = None,
) -> str:
    """Hash every execution-relevant governance input used by activation."""
    payload = {
        "tenant_id": str(tenant_id),
        "template_id": str(template_id),
        "template_version": template_version,
        "agent_definition_id": str(agent_definition_id),
        "risk_tier": risk_tier,
        "capability_contract": capability_contract or {},
        "permission_policy": permission_policy or {},
        "approval_policy": approval_policy or {},
        "install_policy": install_policy or {},
        "configuration": configuration or {},
        "max_concurrency": max_concurrency,
        "budget_policy": budget_policy or {},
    }
    encoded = json.dumps(_canonical(payload), ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
