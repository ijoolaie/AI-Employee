from types import SimpleNamespace

import httpx
import pytest

from app.core.exceptions import ValidationAppError
from app.services import workforce_market_research_service as service


@pytest.mark.asyncio
async def test_market_research_fails_closed_without_provider(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            market_data_provider_base_url=None,
            market_data_provider_api_key=None,
            market_data_provider_timeout_seconds=10.0,
        ),
    )

    with pytest.raises(ValidationAppError, match="not configured"):
        await service.market_research(
            tenant_id="tenant-a",
            symbols=["BTCUSDT"],
        )


@pytest.mark.asyncio
async def test_market_research_uses_operator_configured_endpoint(monkeypatch):
    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["follow_redirects"] is False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, endpoint, *, params, headers):
            assert endpoint == "https://market.example/v1/market/research"
            assert params == {"symbols": "BTCUSDT,ETHUSDT", "horizon_days": 30}
            assert headers["Authorization"] == "Bearer secret"
            return httpx.Response(
                200,
                json={
                    "provider": "test-provider",
                    "as_of": "2026-09-24T00:00:00Z",
                    "results": [{"symbol": "BTCUSDT", "signal": "neutral"}],
                },
                request=httpx.Request("GET", endpoint),
            )

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            market_data_provider_base_url="https://market.example",
            market_data_provider_api_key="secret",
            market_data_provider_timeout_seconds=10.0,
        ),
    )
    monkeypatch.setattr(service.httpx, "AsyncClient", FakeClient)

    result = await service.market_research(
        tenant_id="tenant-a",
        symbols=["btcusdt", "ethusdt"],
    )

    assert result["provider"] == "test-provider"
    assert result["symbols"] == ["BTCUSDT", "ETHUSDT"]
    assert result["results"][0]["signal"] == "neutral"


@pytest.mark.asyncio
async def test_market_research_rejects_missing_tenant():
    with pytest.raises(ValidationAppError, match="tenant Run context"):
        await service.market_research(tenant_id=None, symbols=["BTCUSDT"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("symbols", "horizon_days", "message"),
    [
        (["BTCUSDT"] * 21, 30, "between 1 and 20"),
        (["BTCUSDT"], 0, "horizon_days"),
        (["BTCUSDT"], 366, "horizon_days"),
        (["BTCUSDT", "BTCUSDT"], 30, "unique"),
        (["BTC/USDT"], 30, "symbol is invalid"),
    ],
)
async def test_market_research_validates_inputs_before_provider_call(
    monkeypatch, symbols, horizon_days, message
):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            market_data_provider_base_url="https://market.example",
            market_data_provider_api_key=None,
            market_data_provider_timeout_seconds=10.0,
        ),
    )

    class FailClient:
        def __init__(self, **kwargs):
            raise AssertionError("provider must not be contacted for invalid input")

    monkeypatch.setattr(service.httpx, "AsyncClient", FailClient)

    with pytest.raises(ValidationAppError, match=message):
        await service.market_research(
            tenant_id="tenant-a",
            symbols=symbols,
            horizon_days=horizon_days,
        )
