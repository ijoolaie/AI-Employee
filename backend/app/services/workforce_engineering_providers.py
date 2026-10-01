"""Explicit provider boundary for the W2 engineering workforce.

No generic shell execution lives here. Providers are named adapters with an
explicit capability set. Production defaults to the fail-closed none
provider until an operator configures a real adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.core.config import get_settings

ENGINEERING_PROVIDER_OPERATIONS = frozenset(
    {
        "workspace_test", "workspace_lint", "workspace_build",
        "git_branch", "git_commit_proposal", "git_pr_proposal", "ci_status",
        "deploy_proposal", "health_check", "rollback_proposal",
    }
)

@dataclass(frozen=True)
class ProviderResult:
    provider: str
    operation: str
    executed: bool
    status: str
    reason: str

class EngineeringProvider(Protocol):
    name: str
    operations: frozenset[str]
    def execute(self, operation: str, *, tenant_id: str, arguments: dict[str, Any]) -> ProviderResult: ...

@dataclass(frozen=True)
class UnconfiguredEngineeringProvider:
    """Fail-closed provider used when no operator-controlled adapter is configured."""
    name: str = "none"
    operations: frozenset[str] = ENGINEERING_PROVIDER_OPERATIONS

    def execute(self, operation: str, *, tenant_id: str, arguments: dict[str, Any]) -> ProviderResult:
        if operation not in self.operations:
            raise ValueError(f"Engineering provider does not support operation: {operation}")
        return ProviderResult(self.name, operation, False, "not_configured", "No operator-configured engineering provider is available")

@dataclass(frozen=True)
class ContractTestEngineeringProvider:
    """Deterministic contract adapter for tests; it never mutates external systems."""
    name: str = "contract-test"
    operations: frozenset[str] = ENGINEERING_PROVIDER_OPERATIONS

    def execute(self, operation: str, *, tenant_id: str, arguments: dict[str, Any]) -> ProviderResult:
        if operation not in self.operations:
            raise ValueError(f"Engineering provider does not support operation: {operation}")
        return ProviderResult(self.name, operation, False, "contract_verified", "Deterministic provider contract; no external side effect is performed")

def get_engineering_provider(*, provider_name: str | None = None) -> EngineeringProvider:
    """Resolve an explicit provider name; unknown names fail closed.

    ``provider_name`` is intended for deterministic tests and controlled
    bootstrap code. Runtime semantic execution must use
    ``get_configured_engineering_provider`` so the agent cannot select its own
    external provider.
    """
    name = (provider_name or "none").strip().lower()
    if name == "none":
        return UnconfiguredEngineeringProvider()
    if name == "contract-test":
        return ContractTestEngineeringProvider()
    raise ValueError(f"Unknown engineering provider: {name}")

def provider_contract_snapshot(provider: EngineeringProvider) -> dict[str, Any]:
    return {"provider": provider.name, "operations": sorted(provider.operations), "external_execution": provider.name != "contract-test"}

def get_configured_engineering_provider() -> EngineeringProvider:
    """Resolve the operator-configured runtime provider; never from tool input."""
    name = get_settings().engineering_provider_name
    return get_engineering_provider(provider_name=name)
