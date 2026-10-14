"""Read-only, tenant-mapped website health checks.

The target URL is operator configuration, never supplied by the tool caller.
Requests are HTTPS-only, bounded by a timeout, and redirects are not followed.
"""
from __future__ import annotations

import ipaddress
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.core.config import get_settings


@dataclass(frozen=True)
class WebsiteHealthResult:
    site: str
    provider_execution: str
    healthy: bool | None
    status_code: int | None
    content_type: str | None
    checked_at: str
    reason: str

    def as_dict(self) -> dict:
        return asdict(self)


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _validate_target(value: object) -> str | None:
    if not isinstance(value, str) or not value or len(value) > 2048:
        return "Configured target URL is missing or invalid"
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return "Configured target URL is malformed"
    if parsed.scheme != "https" or not hostname:
        return "Configured target URL must use HTTPS"
    if any(character.isspace() for character in hostname):
        return "Configured target URL hostname is malformed"
    if parsed.username or parsed.password or parsed.fragment:
        return "Configured target URL must not contain credentials or a fragment"
    if port not in (None, 443):
        return "Configured target URL must use the default HTTPS port"
    normalized_host = hostname.rstrip(".").lower()
    if normalized_host == "localhost" or normalized_host.endswith(".localhost") or normalized_host.endswith(".local"):
        return "Configured target hostname is not allowed"
    try:
        address = ipaddress.ip_address(normalized_host)
    except ValueError:
        address = None
    if address is not None and (not address.is_global):
        return "Configured target IP address must be globally routable"
    return None


def check_website_health(*, tenant_id: str, site: str | None) -> dict:
    """Read the operator-mapped URL for a tenant/site alias and return bounded health evidence."""
    now = datetime.now(timezone.utc).isoformat()
    settings = get_settings()
    targets = settings.website_health_targets.get(str(tenant_id), {})
    if not isinstance(site, str) or not site.strip() or len(site) > 255:
        return WebsiteHealthResult(
            site=str(site or ""),
            provider_execution="not_configured",
            healthy=None,
            status_code=None,
            content_type=None,
            checked_at=now,
            reason="A configured site alias is required",
        ).as_dict()
    target = targets.get(site.strip()) if isinstance(targets, dict) else None
    if not target:
        return WebsiteHealthResult(
            site=site.strip(),
            provider_execution="not_configured",
            healthy=None,
            status_code=None,
            content_type=None,
            checked_at=now,
            reason="No operator-configured website target exists for this tenant/site alias",
        ).as_dict()
    invalid_reason = _validate_target(target)
    if invalid_reason:
        return WebsiteHealthResult(
            site=site.strip(),
            provider_execution="not_configured",
            healthy=None,
            status_code=None,
            content_type=None,
            checked_at=now,
            reason=invalid_reason,
        ).as_dict()

    timeout = float(settings.website_health_timeout_seconds)
    try:
        request = Request(
            target,
            headers={"Accept": "text/html,application/json,*/*", "User-Agent": "AI-Employee-WebsiteHealth/1.0"},
            method="GET",
        )
        opener = build_opener(_NoRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            status_code = response.getcode()
            if not isinstance(status_code, int) or isinstance(status_code, bool) or not 100 <= status_code <= 599:
                return WebsiteHealthResult(
                    site=site.strip(), provider_execution="provider_error", healthy=None,
                    status_code=None, content_type=None, checked_at=now,
                    reason="Website provider returned an invalid HTTP status",
                ).as_dict()
            content_type = response.headers.get("Content-Type") if response.headers else None
            return WebsiteHealthResult(
                site=site.strip(),
                provider_execution="read_verified",
                healthy=200 <= status_code < 400,
                status_code=status_code,
                content_type=content_type,
                checked_at=now,
                reason="HTTP health check completed",
            ).as_dict()
    except HTTPError as exc:
        # HTTPError is also raised for redirects because redirects are disabled.
        return WebsiteHealthResult(
            site=site.strip(),
            provider_execution="read_verified",
            healthy=False,
            status_code=int(exc.code) if isinstance(exc.code, int) and not isinstance(exc.code, bool) else None,
            content_type=exc.headers.get("Content-Type") if exc.headers else None,
            checked_at=now,
            reason="Website returned a non-success HTTP status",
        ).as_dict()
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return WebsiteHealthResult(
            site=site.strip(),
            provider_execution="provider_error",
            healthy=None,
            status_code=None,
            content_type=None,
            checked_at=now,
            reason=f"Website health check failed: {type(exc).__name__}",
        ).as_dict()
