from __future__ import annotations

from types import SimpleNamespace
from urllib.error import HTTPError
from email.message import Message

import pytest

from app.services import workforce_website_health_provider as provider


class FakeResponse:
    def __init__(self, status=200, content_type="text/html; charset=utf-8"):
        self._status = status
        self.headers = Message()
        if content_type:
            self.headers["Content-Type"] = content_type

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getcode(self):
        return self._status


def _settings(targets=None, timeout=2.5):
    return SimpleNamespace(
        website_health_targets=targets or {},
        website_health_timeout_seconds=timeout,
    )


def test_health_check_fails_closed_without_tenant_site_mapping(monkeypatch):
    monkeypatch.setattr(provider, "get_settings", lambda: _settings())
    result = provider.check_website_health(tenant_id="tenant-a", site="primary")
    assert result["provider_execution"] == "not_configured"
    assert result["healthy"] is None
    assert result["status_code"] is None


@pytest.mark.parametrize(
    "target",
    [
        "http://example.com",
        "https://user:password@example.com",
        "https://localhost/health",
        "https://service.local/health",
        "https://127.0.0.1/health",
        "https://10.0.0.8/health",
        "https://example.com:8443/health",
        "https://example.com/health#fragment",
    ],
)
def test_health_check_rejects_unsafe_operator_targets(monkeypatch, target):
    monkeypatch.setattr(
        provider,
        "get_settings",
        lambda: _settings({"tenant-a": {"primary": target}}),
    )
    monkeypatch.setattr(
        provider,
        "build_opener",
        lambda *args, **kwargs: pytest.fail("unsafe target must not trigger a request"),
    )
    result = provider.check_website_health(tenant_id="tenant-a", site="primary")
    assert result["provider_execution"] == "not_configured"
    assert result["healthy"] is None
    assert result["status_code"] is None


def test_health_check_uses_tenant_mapped_url_timeout_and_no_redirects(monkeypatch):
    monkeypatch.setattr(
        provider,
        "get_settings",
        lambda: _settings({"tenant-a": {"primary": "https://example.com/health"}}, timeout=2.5),
    )
    captured = {}

    class FakeOpener:
        def open(self, request, timeout):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["timeout"] = timeout
            return FakeResponse(status=200)

    def fake_build_opener(*handlers):
        captured["handlers"] = handlers
        return FakeOpener()

    monkeypatch.setattr(provider, "build_opener", fake_build_opener)
    result = provider.check_website_health(tenant_id="tenant-a", site="primary")

    assert result["provider_execution"] == "read_verified"
    assert result["healthy"] is True
    assert result["status_code"] == 200
    assert result["content_type"] == "text/html; charset=utf-8"
    assert captured["url"] == "https://example.com/health"
    assert captured["method"] == "GET"
    assert captured["timeout"] == 2.5
    assert any(isinstance(handler, provider._NoRedirectHandler) for handler in captured["handlers"])


def test_health_check_does_not_allow_caller_to_choose_another_tenant_target(monkeypatch):
    monkeypatch.setattr(
        provider,
        "get_settings",
        lambda: _settings({"tenant-a": {"primary": "https://example.com/health"}}),
    )
    result = provider.check_website_health(tenant_id="tenant-b", site="primary")
    assert result["provider_execution"] == "not_configured"
    assert result["healthy"] is None


def test_health_check_records_http_error_as_unhealthy_response(monkeypatch):
    monkeypatch.setattr(
        provider,
        "get_settings",
        lambda: _settings({"tenant-a": {"primary": "https://example.com/health"}}),
    )

    class FakeOpener:
        def open(self, request, timeout):
            raise HTTPError(request.full_url, 503, "Service unavailable", Message(), None)

    monkeypatch.setattr(provider, "build_opener", lambda *args, **kwargs: FakeOpener())
    result = provider.check_website_health(tenant_id="tenant-a", site="primary")
    assert result["provider_execution"] == "read_verified"
    assert result["healthy"] is False
    assert result["status_code"] == 503


def test_health_check_reports_transport_failure_without_claiming_health(monkeypatch):
    monkeypatch.setattr(
        provider,
        "get_settings",
        lambda: _settings({"tenant-a": {"primary": "https://example.com/health"}}),
    )

    class FakeOpener:
        def open(self, request, timeout):
            raise TimeoutError("fixture timeout")

    monkeypatch.setattr(provider, "build_opener", lambda *args, **kwargs: FakeOpener())
    result = provider.check_website_health(tenant_id="tenant-a", site="primary")
    assert result["provider_execution"] == "provider_error"
    assert result["healthy"] is None
    assert result["status_code"] is None


def test_health_check_rejects_malformed_http_status(monkeypatch):
    monkeypatch.setattr(
        provider,
        "get_settings",
        lambda: _settings({"tenant-a": {"primary": "https://example.com/health"}}),
    )

    class FakeOpener:
        def open(self, request, timeout):
            return FakeResponse(status="200")

    monkeypatch.setattr(provider, "build_opener", lambda *args, **kwargs: FakeOpener())
    result = provider.check_website_health(tenant_id="tenant-a", site="primary")
    assert result["provider_execution"] == "provider_error"
    assert result["healthy"] is None
    assert result["status_code"] is None
