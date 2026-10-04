"""Explicit provider boundary for installed SkillPackage execution."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.core.config import get_settings


@dataclass(frozen=True)
class SkillProviderResult:
    provider: str
    executed: bool
    status: str
    result: dict[str, Any]


class SkillProviderError(RuntimeError):
    """Raised when a configured Skill provider cannot safely execute."""


class SkillProvider:
    name: str = "none"
    external_execution: bool = False

    def execute(
        self,
        *,
        tenant_id: str,
        employee_id: str,
        skill_package_id: str,
        skill_slug: str,
        skill_version: int,
        input_data: dict[str, Any],
        request_id: str,
    ) -> SkillProviderResult:
        raise NotImplementedError


class UnconfiguredSkillProvider(SkillProvider):
    name = "none"
    external_execution = False

    def execute(self, **kwargs: Any) -> SkillProviderResult:
        raise SkillProviderError("No operator-configured skill provider is available")


class HttpSkillProvider(SkillProvider):
    """Operator-configured HTTP provider.

    Endpoint selection is server-side by tenant. Runtime tool arguments cannot
    choose the provider, URL, authorization header or endpoint.
    """

    name = "http"
    external_execution = True
    MAX_RESPONSE_BYTES = 262_144

    class _NoRedirectHandler(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
            raise SkillProviderError("Skill provider redirects are not permitted")

    def execute(
        self,
        *,
        tenant_id: str,
        employee_id: str,
        skill_package_id: str,
        skill_slug: str,
        skill_version: int,
        input_data: dict[str, Any],
        request_id: str,
    ) -> SkillProviderResult:
        settings = get_settings()
        endpoint = settings.skill_provider_base_url
        api_key = settings.skill_provider_api_key
        if not endpoint or not api_key:
            raise SkillProviderError("Skill provider endpoint or API key is not configured for this tenant")

        payload = json.dumps(
            {
                "tenant_id": tenant_id,
                "employee_id": employee_id,
                "skill_package_id": skill_package_id,
                "skill": {"slug": skill_slug, "version": skill_version},
                "input": input_data,
                "request_id": request_id,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        request = Request(
            endpoint,
            data=payload,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-AI-Employee-Skill-Provider": "1",
                "X-AI-Employee-Request-Id": request_id,
            },
            method="POST",
        )
        opener = build_opener(self._NoRedirectHandler)
        try:
            with opener.open(request, timeout=settings.skill_provider_timeout_seconds) as response:
                raw = response.read(self.MAX_RESPONSE_BYTES + 1)
                if len(raw) > self.MAX_RESPONSE_BYTES:
                    raise SkillProviderError("Skill provider response exceeds the configured size limit")
                data = json.loads(raw.decode("utf-8"))
        except SkillProviderError:
            raise
        except HTTPError as exc:
            raise SkillProviderError(f"Skill provider request failed: HTTP {exc.code}") from exc
        except (URLError, TimeoutError, ValueError, UnicodeDecodeError) as exc:
            raise SkillProviderError(
                f"Skill provider request failed: {type(exc).__name__}"
            ) from exc

        if not isinstance(data, dict):
            raise SkillProviderError("Skill provider response must be a JSON object")

        return SkillProviderResult(
            provider=self.name,
            executed=True,
            status="executed",
            result=data,
        )


def get_skill_provider(provider_name: str | None = None) -> SkillProvider:
    name = (provider_name or "none").strip().lower()
    if name == "none":
        return UnconfiguredSkillProvider()
    if name == "http":
        return HttpSkillProvider()
    raise ValueError(f"Unknown skill provider: {name}")


def get_configured_skill_provider() -> SkillProvider:
    return get_skill_provider(get_settings().skill_provider_name)
