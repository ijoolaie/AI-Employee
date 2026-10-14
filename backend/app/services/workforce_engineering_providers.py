"""Explicit provider boundary for the W2 engineering workforce.

No generic shell execution lives here. Providers are named adapters with an
explicit capability set. Production defaults to the fail-closed none
provider until an operator configures a real adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from http.client import HTTPException
import json
import re
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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
    external_execution: bool
    def execute(self, operation: str, *, tenant_id: str, arguments: dict[str, Any]) -> ProviderResult: ...

@dataclass(frozen=True)
class UnconfiguredEngineeringProvider:
    """Fail-closed provider used when no operator-controlled adapter is configured."""
    name: str = "none"
    operations: frozenset[str] = ENGINEERING_PROVIDER_OPERATIONS
    external_execution: bool = False

    def execute(self, operation: str, *, tenant_id: str, arguments: dict[str, Any]) -> ProviderResult:
        if operation not in self.operations:
            raise ValueError(f"Engineering provider does not support operation: {operation}")
        return ProviderResult(self.name, operation, False, "not_configured", "No operator-configured engineering provider is available")

@dataclass(frozen=True)
class ContractTestEngineeringProvider:
    """Deterministic contract adapter for tests; it never mutates external systems."""
    name: str = "contract-test"
    operations: frozenset[str] = ENGINEERING_PROVIDER_OPERATIONS
    external_execution: bool = False

    def execute(self, operation: str, *, tenant_id: str, arguments: dict[str, Any]) -> ProviderResult:
        if operation not in self.operations:
            raise ValueError(f"Engineering provider does not support operation: {operation}")
        return ProviderResult(self.name, operation, False, "contract_verified", "Deterministic provider contract; no external side effect is performed")


@dataclass(frozen=True)
class GitHubReadOnlyEngineeringProvider:
    """Operator-configured, read-only GitHub adapter.

    Repository identity is resolved from operator configuration by tenant.
    Tool arguments cannot choose the repository, URL, token, or headers.
    Only CI/status reads are implemented; every other engineering operation
    remains explicitly unconfigured.
    """
    name: str = "github-readonly"
    operations: frozenset[str] = frozenset({"ci_status"})
    external_execution: bool = False

    def execute(self, operation: str, *, tenant_id: str, arguments: dict[str, Any]) -> ProviderResult:
        if operation != "ci_status":
            return ProviderResult(self.name, operation, False, "not_configured", "GitHub read-only adapter does not execute this operation")
        settings = get_settings()
        repository = settings.engineering_github_repositories.get(tenant_id)
        token = settings.engineering_github_token
        if not repository or not token:
            return ProviderResult(self.name, operation, False, "not_configured", "GitHub repository/token is not configured for this tenant")
        commit_sha = str(arguments.get("commit_sha", "")).strip()
        if not commit_sha:
            return ProviderResult(self.name, operation, False, "not_configured", "ci_status requires a commit_sha")
        if not re.fullmatch(r"[0-9a-fA-F]{40}", commit_sha):
            return ProviderResult(self.name, operation, False, "not_configured", "ci_status requires a 40-character hexadecimal commit SHA")
        url = f"https://api.github.com/repos/{repository}/commits/{commit_sha}/status"
        request = Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AI-Employee-Engineering-Provider",
        }, method="GET")
        try:
            with urlopen(request, timeout=settings.engineering_github_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError, ValueError, HTTPException) as exc:
            return ProviderResult(self.name, operation, False, "provider_error", f"GitHub status read failed: {type(exc).__name__}")
        # Treat syntactically valid JSON with the wrong shape as a provider
        # contract failure too; never turn malformed upstream data into a
        # successful read or leak an AttributeError to the caller.
        if (
            not isinstance(payload, dict)
            or not isinstance(payload.get("state"), str)
            or payload.get("state") not in {"pending", "success", "failure", "error"}
            or not isinstance(payload.get("total_count"), int)
            or isinstance(payload.get("total_count"), bool)
            or payload.get("total_count") < 0
        ):
            return ProviderResult(
                self.name, operation, False, "provider_error",
                "GitHub status read failed: invalid response contract",
            )
        # Read-only provider never reports external execution.
        return ProviderResult(
            self.name,
            operation,
            False,
            "read_verified",
            json.dumps({"state": payload["state"], "total_count": payload["total_count"]}, sort_keys=True),
        )


_GITHUB_SHA_RE = re.compile(r"[0-9a-fA-F]{40}")
_GITHUB_BRANCH_RE = re.compile(r"[A-Za-z0-9._/-]{1,255}")


def _validate_github_branch_name(branch_name: str) -> str | None:
    name = branch_name.strip()
    components = name.split("/")
    if (
        not name
        or not _GITHUB_BRANCH_RE.fullmatch(name)
        or name.startswith("/")
        or name.endswith("/")
        or name.startswith(".")
        or name.endswith(".")
        or name.startswith("-")
        or name.endswith("-")
        or ".." in name
        or "//" in name
        or "@{" in name
        or name.startswith("refs/")
        or any(
            component.startswith(".")
            or component.endswith(".")
            or component.lower().endswith(".lock")
            or component == "@"
            for component in components
        )
    ):
        return None
    return name


@dataclass(frozen=True)
class GitHubEngineeringProvider:
    """Operator-configured GitHub provider for narrowly-scoped engineering writes."""
    name: str = "github"
    operations: frozenset[str] = frozenset({"ci_status", "git_branch"})
    external_execution: bool = True

    def execute(self, operation: str, *, tenant_id: str, arguments: dict[str, Any]) -> ProviderResult:
        if operation not in self.operations:
            return ProviderResult(self.name, operation, False, "not_configured", "GitHub provider does not execute this operation")
        settings = get_settings()
        repository = settings.engineering_github_repositories.get(tenant_id)
        token = settings.engineering_github_token
        if not repository or not token:
            return ProviderResult(self.name, operation, False, "not_configured", "GitHub repository/token is not configured for this tenant")
        if operation == "ci_status":
            return GitHubReadOnlyEngineeringProvider().execute(
                operation, tenant_id=tenant_id, arguments=arguments
            )

        branch_name = _validate_github_branch_name(str(arguments.get("branch_name", "")))
        source_sha = str(arguments.get("source_sha", "")).strip()
        if branch_name is None:
            return ProviderResult(self.name, operation, False, "not_configured", "git_branch requires a safe branch_name")
        if not _GITHUB_SHA_RE.fullmatch(source_sha):
            return ProviderResult(self.name, operation, False, "not_configured", "git_branch requires a 40-character hexadecimal source_sha")

        base_url = f"https://api.github.com/repos/{repository}/git/ref/heads/{branch_name}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AI-Employee-Engineering-Provider",
        }
        try:
            request = Request(base_url, headers=headers, method="GET")
            with urlopen(request, timeout=settings.engineering_github_timeout_seconds) as response:
                existing = json.loads(response.read().decode("utf-8"))
            existing_ref = existing.get("ref") if isinstance(existing, dict) else None
            existing_object = existing.get("object") if isinstance(existing, dict) else None
            existing_sha = existing_object.get("sha") if isinstance(existing_object, dict) else None
            expected_ref = f"refs/heads/{branch_name}"
            if (
                existing_ref != expected_ref
                or not isinstance(existing_sha, str)
                or not _GITHUB_SHA_RE.fullmatch(existing_sha)
            ):
                return ProviderResult(
                    self.name, operation, False, "provider_error",
                    "GitHub branch lookup failed: invalid response contract",
                )
            if existing_sha == source_sha:
                return ProviderResult(
                    self.name, operation, False, "already_exists",
                    json.dumps({"branch": branch_name, "sha": source_sha}, sort_keys=True),
                )
            return ProviderResult(
                self.name, operation, False, "conflict",
                "Branch already exists at a different commit",
            )
        except HTTPError as exc:
            if exc.code != 404:
                return ProviderResult(self.name, operation, False, "provider_error", f"GitHub branch lookup failed: HTTP {exc.code}")
        except (URLError, OSError, ValueError, HTTPException) as exc:
            return ProviderResult(self.name, operation, False, "provider_error", f"GitHub branch lookup failed: {type(exc).__name__}")

        def reconcile_unknown_create(original_reason: str) -> ProviderResult:
            """Read once after an ambiguous POST; never repeat the mutation."""
            try:
                lookup = Request(base_url, headers=headers, method="GET")
                with urlopen(lookup, timeout=settings.engineering_github_timeout_seconds) as response:
                    current = json.loads(response.read().decode("utf-8"))
                current_ref = current.get("ref") if isinstance(current, dict) else None
                current_object = current.get("object") if isinstance(current, dict) else None
                current_sha = current_object.get("sha") if isinstance(current_object, dict) else None
                expected_ref = f"refs/heads/{branch_name}"
                if (
                    current_ref != expected_ref
                    or not isinstance(current_sha, str)
                    or not _GITHUB_SHA_RE.fullmatch(current_sha)
                ):
                    return ProviderResult(
                        self.name, operation, False, "outcome_unknown",
                        f"{original_reason}; reconciliation read was invalid or did not identify the requested ref",
                    )
                if current_sha == source_sha:
                    return ProviderResult(
                        self.name, operation, False, "reconciled",
                        json.dumps({"branch": branch_name, "sha": source_sha, "prior_outcome": "unknown"}, sort_keys=True),
                    )
                return ProviderResult(
                    self.name, operation, False, "conflict",
                    "GitHub branch exists after ambiguous creation but points to a different commit",
                )
            except (HTTPError, URLError, OSError, ValueError, HTTPException) as exc:
                # A 404 or failed read does not prove that the POST was rejected;
                # GitHub state may be temporarily unavailable or not yet visible.
                return ProviderResult(
                    self.name, operation, False, "outcome_unknown",
                    f"{original_reason}; reconciliation unavailable: {type(exc).__name__}",
                )

        payload = json.dumps({"ref": f"refs/heads/{branch_name}", "sha": source_sha}).encode("utf-8")
        request = Request(
            f"https://api.github.com/repos/{repository}/git/refs",
            data=payload,
            headers={**headers, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=settings.engineering_github_timeout_seconds) as response:
                created = json.loads(response.read().decode("utf-8"))
            created_object = created.get("object") if isinstance(created, dict) else None
            created_sha = created_object.get("sha") if isinstance(created_object, dict) else None
            if not isinstance(created_sha, str) or not _GITHUB_SHA_RE.fullmatch(created_sha):
                return reconcile_unknown_create("GitHub branch creation outcome unknown: invalid response contract")
            if created_sha != source_sha:
                return reconcile_unknown_create("GitHub branch creation outcome unknown: returned SHA does not match requested source SHA")
        except HTTPError as exc:
            if exc.code == 422:
                return ProviderResult(self.name, operation, False, "conflict", "GitHub rejected branch creation; the branch may have been created concurrently")
            if exc.code >= 500:
                return reconcile_unknown_create(f"GitHub branch creation outcome unknown: HTTP {exc.code}")
            return ProviderResult(self.name, operation, False, "provider_error", f"GitHub branch creation failed: HTTP {exc.code}")
        except (URLError, OSError, ValueError, HTTPException) as exc:
            # The POST may have succeeded despite an unreadable response. Make
            # one read-only reconciliation attempt; never retry the write here.
            return reconcile_unknown_create(f"GitHub branch creation outcome unknown: {type(exc).__name__}")

        return ProviderResult(
            self.name, operation, True, "executed",
            json.dumps({"branch": branch_name, "sha": created_sha}, sort_keys=True),
        )

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
    if name == "github-readonly":
        return GitHubReadOnlyEngineeringProvider()
    if name == "github":
        return GitHubEngineeringProvider()
    raise ValueError(f"Unknown engineering provider: {name}")

def provider_contract_snapshot(provider: EngineeringProvider) -> dict[str, Any]:
    return {"provider": provider.name, "operations": sorted(provider.operations), "external_execution": provider.external_execution}

def get_configured_engineering_provider() -> EngineeringProvider:
    """Resolve the operator-configured runtime provider; never from tool input."""
    name = get_settings().engineering_provider_name
    return get_engineering_provider(provider_name=name)
