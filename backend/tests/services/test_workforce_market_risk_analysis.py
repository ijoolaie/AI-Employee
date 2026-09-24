from types import SimpleNamespace

import pytest

from app.core.exceptions import ValidationAppError
from app.services import workforce_market_risk_analysis_service as service


def _settings(**overrides):
    values = {
        "market_data_provider_base_url": None,
        "market_data_provider_api_key": None,
        "market_data_provider_timeout_seconds": 10.0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_provider_missing_fails_closed(monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: _settings())
    with pytest.raises(ValidationAppError, match="not configured"):
        await service.risk_analysis(
            tenant_id="tenant-1",
            symbols=["AAPL"],
        )


@pytest.mark.asyncio
async def test_provider_boundary_is_tenant_safe_and_normalizes_response(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: _settings(
            market_data_provider_base_url="https://market.example",
            market_data_provider_api_key="secret",
        ),
    )
    calls = []

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "provider": "operator-provider",
                "as_of": "2026-09-24T08:00:00Z",
                "results": [{"symbol": "AAPL", "risk": "medium"}],
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            assert kwargs["follow_redirects"] is False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, endpoint, **kwargs):
            calls.append((endpoint, kwargs))
            return FakeResponse()

    monkeypatch.setattr(service.httpx, "AsyncClient", FakeClient)

    result = await service.risk_analysis(
        tenant_id="tenant-1",
        symbols=[" aapl "],
        horizon_days=14,
    )

    assert result["symbols"] == ["AAPL"]
    assert result["horizon_days"] == 14
    assert result["results"][0]["risk"] == "medium"
    assert calls[0][0] == "https://market.example/v1/market/risk-analysis"
    assert calls[0][1]["params"] == {"symbols": "AAPL", "horizon_days": 14}
    assert calls[0][1]["headers"]["Authorization"] == "Bearer secret"
    assert "tenant_id" not in calls[0][1]["params"]


@pytest.mark.asyncio
async def test_invalid_provider_response_fails_closed(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: _settings(market_data_provider_base_url="https://market.example"),
    )

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"unexpected": []}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, endpoint, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(service.httpx, "AsyncClient", FakeClient)

    with pytest.raises(ValidationAppError, match="semantic tool contract"):
        await service.risk_analysis(tenant_id="tenant-1", symbols=["AAPL"])
