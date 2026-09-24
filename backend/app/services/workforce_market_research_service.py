"""Tenant-safe, read-only market research provider adapter for Workforce Trader."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import re

import httpx

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError


async def market_research(
    *,
    tenant_id,
    symbols: list[str],
    horizon_days: int = 30,
) -> dict[str, Any]:
    """Query the operator-configured read-only market research provider.

    The provider endpoint is configuration-owned and never supplied by the
    Workforce Agent. Tenant identity is enforced locally and is deliberately
    not forwarded to the external provider.
    """
    if tenant_id is None:
        raise ValidationAppError("market_research requires an active tenant Run context")

    settings = get_settings()
    base_url = (settings.market_data_provider_base_url or "").strip()
    if not base_url:
        raise ValidationAppError(
            "Market research provider is not configured; fail-closed",
            details={"tool": "workforce_market_research"},
        )

    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationAppError("Market research provider URL is invalid; fail-closed")

    if not isinstance(horizon_days, int) or isinstance(horizon_days, bool) or not 1 <= horizon_days <= 365:
        raise ValidationAppError("Market research horizon_days must be between 1 and 365")

    normalized_symbols = [symbol.strip().upper() for symbol in symbols]
    if not normalized_symbols or len(normalized_symbols) > 20:
        raise ValidationAppError("Market research requires between 1 and 20 symbols")
    if len(set(normalized_symbols)) != len(normalized_symbols):
        raise ValidationAppError("Market research symbols must be unique")
    symbol_pattern = re.compile(r"^[A-Z0-9][A-Z0-9._:-]{0,31}$")
    if any(not symbol_pattern.fullmatch(symbol) for symbol in normalized_symbols):
        raise ValidationAppError("Market research symbol is invalid")

    endpoint = base_url.rstrip("/") + "/v1/market/research"
    headers = {"Accept": "application/json"}
    if settings.market_data_provider_api_key:
        headers["Authorization"] = f"Bearer {settings.market_data_provider_api_key}"

    try:
        async with httpx.AsyncClient(
            timeout=settings.market_data_provider_timeout_seconds,
            follow_redirects=False,
        ) as client:
            response = await client.get(
                endpoint,
                params={
                    "symbols": ",".join(normalized_symbols),
                    "horizon_days": horizon_days,
                },
                headers=headers,
            )
    except httpx.HTTPError as exc:
        raise ValidationAppError(
            "Market research provider request failed",
            details={"tool": "workforce_market_research"},
        ) from exc

    if response.status_code >= 400:
        raise ValidationAppError(
            "Market research provider returned an error",
            details={"tool": "workforce_market_research", "status_code": response.status_code},
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise ValidationAppError(
            "Market research provider returned invalid JSON",
            details={"tool": "workforce_market_research"},
        ) from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValidationAppError(
            "Market research provider response violates the semantic tool contract",
            details={"tool": "workforce_market_research"},
        )

    return {
        "provider": payload.get("provider", "configured"),
        "as_of": payload.get("as_of"),
        "symbols": normalized_symbols,
        "horizon_days": horizon_days,
        "results": payload["results"],
    }
