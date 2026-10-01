from __future__ import annotations

import pytest

from app.services.workforce_engineering_providers import (
    ContractTestEngineeringProvider,
    GitHubEngineeringProvider,
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
    from app.services.workforce_engineering_providers import provider_contract_snapshot
    assert provider_contract_snapshot(provider)["external_execution"] is False


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
async def test_engineering_domain_exposes_provider_boundary(monkeypatch):
    from app.services import workforce_engineering_providers as providers
    class FakeSettings:
        engineering_provider_name = "none"
    monkeypatch.setattr(providers, "get_settings", lambda: FakeSettings())
    result = await execute_engineering({"_operation": "workspace_test"}, tenant_id="tenant-a")
    assert result["provider"]["provider"] == "none"
    assert result["provider_execution"] == "not_configured"
    assert result["executed"] is False


@pytest.mark.asyncio
async def test_real_provider_path_remains_not_configured(monkeypatch):
    from app.services import workforce_engineering_providers as providers
    class FakeSettings:
        engineering_provider_name = "none"
    monkeypatch.setattr(providers, "get_settings", lambda: FakeSettings())
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


def test_github_readonly_provider_reads_operator_configured_status_without_execution(monkeypatch):
    from app.services.workforce_engineering_providers import GitHubReadOnlyEngineeringProvider

    class FakeSettings:
        engineering_github_repositories = {"tenant-a": "ijoolaie/AI-Employee"}
        engineering_github_token = "secret-token"
        engineering_github_timeout_seconds = 2.5

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"state":"success","total_count":3}'

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.workforce_engineering_providers.get_settings",
        lambda: FakeSettings(),
    )
    monkeypatch.setattr(
        "app.services.workforce_engineering_providers.urlopen",
        fake_urlopen,
    )

    result = GitHubReadOnlyEngineeringProvider().execute(
        "ci_status",
        tenant_id="tenant-a",
        arguments={"commit_sha": "0123456789abcdef0123456789abcdef01234567", "repository": "attacker/repo", "token": "attacker-token"},
    )

    assert result.status == "read_verified"
    assert result.executed is False
    assert result.reason == '{"state": "success", "total_count": 3}'
    assert captured["url"] == "https://api.github.com/repos/ijoolaie/AI-Employee/commits/0123456789abcdef0123456789abcdef01234567/status"
    assert captured["authorization"] == "Bearer secret-token"
    assert captured["timeout"] == 2.5
    invalid = GitHubReadOnlyEngineeringProvider().execute(
        "ci_status",
        tenant_id="tenant-a",
        arguments={"commit_sha": "abc123"},
    )
    assert invalid.status == "not_configured"
    assert "40-character hexadecimal" in invalid.reason


def test_github_readonly_provider_is_operator_configured_and_read_only(monkeypatch):
    from app.services.workforce_engineering_providers import GitHubReadOnlyEngineeringProvider

    class FakeSettings:
        engineering_github_repositories = {"tenant-a": "ijoolaie/AI-Employee"}
        engineering_github_token = None
        engineering_github_timeout_seconds = 1.0

    monkeypatch.setattr(
        "app.services.workforce_engineering_providers.get_settings",
        lambda: FakeSettings(),
    )
    provider = GitHubReadOnlyEngineeringProvider()
    from app.services.workforce_engineering_providers import provider_contract_snapshot
    assert provider_contract_snapshot(provider)["external_execution"] is False
    result = provider.execute("ci_status", tenant_id="tenant-a", arguments={"commit_sha": "abc"})
    assert result.status == "not_configured"
    unsupported = provider.execute("git_branch", tenant_id="tenant-a", arguments={})
    assert unsupported.status == "not_configured"


@pytest.mark.asyncio
async def test_git_branch_is_external_side_effect():
    result = await execute_engineering(
        {"_operation": "git_branch"},
        tenant_id="tenant-a",
    )
    assert result["external_side_effect"] is True
    assert result["approval_required"] is True


def test_developer_approval_operations_are_not_routine():
    from app.services.ai_workforce_roles import get_workforce_role, get_workforce_capability_contract
    role = get_workforce_role("ai_software_developer")
    assert set(role.allowed_routine_operations).isdisjoint(role.approval_required_operations)
    for operation in role.approval_required_operations:
        assert get_workforce_capability_contract("ai_software_developer", operation).approval_required is True


def test_ci_status_tool_accepts_commit_sha():
    from app.ai.tool_registry import registry

    tool = registry.get("workforce_ci_status")
    properties = tool.input_schema["properties"]
    assert properties["commit_sha"] == {"type": "string", "maxLength": 100}
    assert tool.input_schema["required"] == ["commit_sha"]


@pytest.mark.asyncio
async def test_ci_status_semantic_result_exposes_execution_state(monkeypatch):
    from app.services import workforce_engineering_providers as providers
    from app.services.workforce_engineering_providers import GitHubReadOnlyEngineeringProvider

    class FakeSettings:
        engineering_provider_name = "github-readonly"
        engineering_github_repositories = {"tenant-a": "ijoolaie/AI-Employee"}
        engineering_github_token = "secret-token"
        engineering_github_timeout_seconds = 2.5

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self):
            return b'{"state":"success","total_count":1}'

    monkeypatch.setattr(providers, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(providers, "urlopen", lambda request, timeout: FakeResponse())

    result = await execute_engineering(
        {"_operation": "ci_status", "commit_sha": "0123456789abcdef0123456789abcdef01234567"},
        tenant_id="tenant-a",
    )
    assert result["status"] == "read_verified"
    assert result["executed"] is False
    assert result["provider_execution"] == "read_verified"
    assert result["approval_required"] is False
    assert result["external_side_effect"] is False


def test_github_branch_provider_is_operator_bound_and_idempotent(monkeypatch):
    class FakeSettings:
        engineering_github_repositories = {"tenant-a": "ijoolaie/AI-Employee"}
        engineering_github_token = "secret-token"
        engineering_github_timeout_seconds = 2.5

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return self.payload

    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.method, request.full_url, request.data, request.get_header("Authorization"), timeout))
        if request.method == "GET":
            return FakeResponse(b'{"object":{"sha":"0123456789abcdef0123456789abcdef01234567"}}')
        raise AssertionError("POST must not run when branch already exists at requested SHA")

    monkeypatch.setattr("app.services.workforce_engineering_providers.get_settings", lambda: FakeSettings())
    monkeypatch.setattr("app.services.workforce_engineering_providers.urlopen", fake_urlopen)

    provider = GitHubEngineeringProvider()
    result = provider.execute(
        "git_branch",
        tenant_id="tenant-a",
        arguments={
            "branch_name": "ai/test-branch",
            "source_sha": "0123456789abcdef0123456789abcdef01234567",
            "repository": "attacker/repo",
            "token": "attacker-token",
        },
    )
    assert result.status == "already_exists"
    assert result.executed is False
    assert provider.operations == frozenset({"ci_status", "git_branch"})
    assert provider.external_execution is True
    assert calls[0][1] == "https://api.github.com/repos/ijoolaie/AI-Employee/git/refs/heads/ai/test-branch"
    assert calls[0][3] == "Bearer secret-token"
    assert calls[0][4] == 2.5


@pytest.mark.asyncio
async def test_git_branch_semantic_result_is_external_and_approval_gated(monkeypatch):
    from app.services import workforce_engineering_providers as providers

    class FakeSettings:
        engineering_provider_name = "github"

    monkeypatch.setattr(providers, "get_settings", lambda: FakeSettings())
    result = await execute_engineering(
        {
            "_operation": "git_branch",
            "branch_name": "ai/test-branch",
            "source_sha": "0123456789abcdef0123456789abcdef01234567",
        },
        tenant_id="tenant-a",
    )
    assert result["provider"]["provider"] == "github"
    assert result["provider"]["external_execution"] is True
    assert result["approval_required"] is True
    assert result["external_side_effect"] is True


def test_github_branch_provider_creates_missing_branch(monkeypatch):
    from urllib.error import HTTPError

    class FakeSettings:
        engineering_github_repositories = {"tenant-a": "ijoolaie/AI-Employee"}
        engineering_github_token = "secret-token"
        engineering_github_timeout_seconds = 2.5

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return self.payload

    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.method, request.full_url, request.data, request.get_header("Authorization"), timeout))
        if request.method == "GET":
            raise HTTPError(request.full_url, 404, "not found", {}, None)
        assert request.method == "POST"
        return FakeResponse(b'{"ref":"refs/heads/ai/test-branch","object":{"sha":"0123456789abcdef0123456789abcdef01234567"}}')

    monkeypatch.setattr("app.services.workforce_engineering_providers.get_settings", lambda: FakeSettings())
    monkeypatch.setattr("app.services.workforce_engineering_providers.urlopen", fake_urlopen)

    result = GitHubEngineeringProvider().execute(
        "git_branch",
        tenant_id="tenant-a",
        arguments={
            "branch_name": "ai/test-branch",
            "source_sha": "0123456789abcdef0123456789abcdef01234567",
        },
    )
    assert result.status == "executed"
    assert result.executed is True
    assert calls[1][1] == "https://api.github.com/repos/ijoolaie/AI-Employee/git/refs"
    assert calls[1][3] == "Bearer secret-token"
    assert b'"ref": "refs/heads/ai/test-branch"' in calls[1][2]
    assert b'"sha": "0123456789abcdef0123456789abcdef01234567"' in calls[1][2]


def test_github_branch_provider_rejects_unsafe_inputs_without_network(monkeypatch):
    class FakeSettings:
        engineering_github_repositories = {"tenant-a": "ijoolaie/AI-Employee"}
        engineering_github_token = "secret-token"
        engineering_github_timeout_seconds = 2.5

    monkeypatch.setattr("app.services.workforce_engineering_providers.get_settings", lambda: FakeSettings())
    monkeypatch.setattr(
        "app.services.workforce_engineering_providers.urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network must not be called")),
    )

    provider = GitHubEngineeringProvider()
    invalid_branch = provider.execute(
        "git_branch",
        tenant_id="tenant-a",
        arguments={"branch_name": "../main", "source_sha": "0123456789abcdef0123456789abcdef01234567"},
    )
    invalid_sha = provider.execute(
        "git_branch",
        tenant_id="tenant-a",
        arguments={"branch_name": "ai/test", "source_sha": "abc123"},
    )
    assert invalid_branch.status == "not_configured"
    assert invalid_sha.status == "not_configured"
