from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.exceptions import ValidationAppError
from app.services.workforce_market_trading_plan_service import prepare_trading_plan


@pytest.mark.asyncio
async def test_trading_plan_fails_closed_without_provider(monkeypatch):
    class Settings:
        market_data_provider_base_url = ""
        market_data_provider_api_key = None
        market_data_provider_timeout_seconds = 5

    monkeypatch.setattr(
        "app.services.workforce_market_trading_plan_service.get_settings",
        lambda: Settings(),
    )

    with pytest.raises(ValidationAppError, match="not configured"):
        await prepare_trading_plan(tenant_id="tenant", symbols=["AAPL"])


@pytest.mark.asyncio
async def test_trading_plan_normalizes_provider_response(monkeypatch):
    class Settings:
        market_data_provider_base_url = "https://provider.example"
        market_data_provider_api_key = "secret"
        market_data_provider_timeout_seconds = 5

    monkeypatch.setattr(
        "app.services.workforce_market_trading_plan_service.get_settings",
        lambda: Settings(),
    )

    response = httpx.Response(
        200,
        json={
            "provider": "test-provider",
            "as_of": "2026-09-24T00:00:00Z",
            "plan": {"actions": [{"symbol": "AAPL", "action": "watch"}]},
        },
        request=httpx.Request("GET", "https://provider.example/v1/market/trading-plan"),
    )
    mock_client = AsyncMock()
    mock_client.get.return_value = response

    class ClientContext:
        async def __aenter__(self):
            return mock_client
        async def __aexit__(self, *args):
            return False

    with patch(
        "app.services.workforce_market_trading_plan_service.httpx.AsyncClient",
        return_value=ClientContext(),
    ):
        result = await prepare_trading_plan(
            tenant_id="tenant",
            symbols=["aapl"],
            horizon_days=14,
            objective="BALANCED",
        )

    assert result["symbols"] == ["AAPL"]
    assert result["horizon_days"] == 14
    assert result["objective"] == "balanced"
    assert result["plan"]["actions"][0]["symbol"] == "AAPL"
    assert mock_client.get.await_args.kwargs["params"]["objective"] == "balanced"


@pytest.mark.asyncio
async def test_trading_plan_rejects_invalid_provider_payload(monkeypatch):
    class Settings:
        market_data_provider_base_url = "https://provider.example"
        market_data_provider_api_key = None
        market_data_provider_timeout_seconds = 5

    monkeypatch.setattr(
        "app.services.workforce_market_trading_plan_service.get_settings",
        lambda: Settings(),
    )

    response = httpx.Response(
        200,
        json={"results": []},
        request=httpx.Request("GET", "https://provider.example/v1/market/trading-plan"),
    )
    mock_client = AsyncMock()
    mock_client.get.return_value = response

    class ClientContext:
        async def __aenter__(self):
            return mock_client
        async def __aexit__(self, *args):
            return False

    with patch(
        "app.services.workforce_market_trading_plan_service.httpx.AsyncClient",
        return_value=ClientContext(),
    ):
        with pytest.raises(ValidationAppError, match="violates"):
            await prepare_trading_plan(tenant_id="tenant", symbols=["AAPL"])


def test_trading_plan_binding_is_explicit():
    from app.services.ai_workforce_roles import get_workforce_capability_contract

    contract = get_workforce_capability_contract("ai_trader", "prepare_trading_plan")
    assert contract.tool_names == ("workforce_market_trading_plan",)
    assert contract.approval_required is False
