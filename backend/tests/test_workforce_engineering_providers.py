from __future__ import annotations

import pytest

from app.services.workforce_engineering_providers import (
    ContractTestEngineeringProvider,
    UnconfiguredEngineeringProvider,
    get_engineering_provider,
)
from app.services.workforce_semantic_domains import execute_engineering


def test_provider_defaults_to_fail_closed_none():
    provider = get_engineering_provider()
    assert isinstance(provider, UnconfiguredEngineeringProvider)
    result = provider.execute("git_branch", tenant_id="tenant-a", arguments={})
    assert result.executed is False
    assert result.status == "not_configured"


def test_contract_provider_is_deterministic_and_non_mutating():
    provider = get_engineering_provider(provider_name="contract-test")
    assert isinstance(provider, ContractTestEngineeringProvider)
    result = provider.execute("git_branch", tenant_id="tenant-a", arguments={})
    assert result.executed is False
    assert result.status == "contract_verified"


def test_unknown_provider_fails_closed():
    with pytest.raises(ValueError):
        get_engineering_provider(provider_name="arbitrary-shell")


@pytest.mark.asyncio
async def test_engineering_domain_exposes_provider_boundary():
    result = await execute_engineering({"_operation": "workspace_test"}, tenant_id="tenant-a")
    assert result["provider"]["provider"] == "none"
    assert result["provider_execution"] == "not_configured"
    assert result["executed"] is False


@pytest.mark.asyncio
async def test_real_provider_path_remains_not_configured():
    result = await execute_engineering(
        {"_operation": "deploy_proposal"},
        tenant_id="tenant-a",
    )
    assert result["provider"]["provider"] == "none"
    assert result["provider_execution"] == "not_configured"
    assert result["approval_required"] is True
    assert result["external_side_effect"] is True

def test_runtime_provider_is_operator_configured(monkeypatch):
    from app.services import workforce_engineering_providers as providers
    class FakeSettings:
        engineering_provider_name = "contract-test"
    monkeypatch.setattr(providers, "get_settings", lambda: FakeSettings())
    assert providers.get_configured_engineering_provider().name == "contract-test"


@pytest.mark.asyncio
async def test_runtime_context_cannot_select_engineering_provider(monkeypatch):
    from app.services import workforce_engineering_providers as providers

    class FakeSettings:
        engineering_provider_name = "none"

    monkeypatch.setattr(providers, "get_settings", lambda: FakeSettings())
    result = await execute_engineering(
        {"_operation": "git_branch"},
        tenant_id="tenant-a",
        engineering_provider="contract-test",
    )
    assert result["provider"]["provider"] == "none"
    assert result["provider_execution"] == "not_configured"


def test_engineering_registry_matches_role_side_effect_contract():
    from app.ai.tool_registry import registry

    branch = registry.get("workforce_git_branch")
    commit = registry.get("workforce_git_commit_proposal")
    assert branch.external_side_effects is True
    assert branch.requires_approval is True
    assert commit.external_side_effects is True
    assert commit.requires_approval is True
