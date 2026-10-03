"""ZarinPal adapter for governed one-time sales payments.

Provider selection is operator-controlled. This adapter only creates payment
requests; payment is considered revenue only after the callback handler calls
ZarinPal verification and the provider-neutral revenue reconciliation path.
"""

from __future__ import annotations

from decimal import Decimal
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

import httpx

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.services.workforce_sales_payment_provider import SalesPaymentResult


def _urls() -> tuple[str, str]:
    settings = get_settings()
    if settings.zarinpal_sandbox:
        base = "https://sandbox.zarinpal.com"
        return (
            f"{base}/pg/v4/payment/request.json",
            f"{base}/pg/StartPay/",
        )
    base = "https://api.zarinpal.com"
    return (
        f"{base}/pg/v4/payment/request.json",
        "https://www.zarinpal.com/pg/StartPay/",
    )


def _rial_amount(amount: Decimal, currency: str) -> int:
    normalized = currency.upper()
    if normalized == "IRT" or normalized in {"TOMAN", "IRTM"}:
        amount = amount * Decimal("10")
    elif normalized != "IRR":
        raise ValidationAppError("ZarinPal sales payment provider supports IRR/IRT only")
    value = amount.quantize(Decimal("1"))
    if value <= 0:
        raise ValidationAppError("ZarinPal payment amount must be positive")
    return int(value)


def _callback_url(deal_id) -> str:
    settings = get_settings()
    base = settings.zarinpal_callback_url
    parts = urlsplit(base)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["deal_id"] = str(deal_id)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


async def create_payment_request(
    *,
    tenant_id,
    deal_id,
    amount: Decimal,
    currency: str,
    customer_email: str | None,
    idempotency_key: str,
) -> SalesPaymentResult:
    settings = get_settings()
    if not settings.zarinpal_merchant_id:
        raise ValidationAppError("ZarinPal requires ZARINPAL_MERCHANT_ID")

    request_url, gateway_base = _urls()
    payload = {
        "merchant_id": settings.zarinpal_merchant_id,
        "amount": _rial_amount(amount, currency),
        "callback_url": _callback_url(deal_id),
        "description": f"AI Workforce commercial commitment {deal_id}",
        "metadata": {
            "email": customer_email or "",
            "tenant_id": str(tenant_id),
            "sales_deal_id": str(deal_id),
            "idempotency_key": idempotency_key,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=settings.zarinpal_timeout_seconds, follow_redirects=False) as client:
            response = await client.post(
                request_url,
                json=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            )
    except httpx.HTTPError as exc:
        raise ValidationAppError("ZarinPal payment request failed") from exc

    if response.status_code >= 400:
        raise ValidationAppError(f"ZarinPal payment request rejected: HTTP {response.status_code}")

    try:
        body = response.json()
    except ValueError as exc:
        raise ValidationAppError("ZarinPal returned an invalid payment response") from exc

    data = body.get("data") or {}
    code = data.get("code")
    authority = data.get("authority")
    if code != 100 or not authority:
        errors = body.get("errors") or {}
        message = errors.get("message") or f"provider code {code}"
        raise ValidationAppError(f"ZarinPal payment request rejected: {message}")

    return SalesPaymentResult(
        provider="zarinpal",
        provider_execution="accepted",
        executed=True,
        checkout_url=f"{gateway_base}{authority}",
        provider_payment_id=str(authority),
    )


async def verify_payment(*, authority: str, amount: Decimal, currency: str) -> dict:
    settings = get_settings()
    if not settings.zarinpal_merchant_id:
        raise ValidationAppError("ZarinPal requires ZARINPAL_MERCHANT_ID")

    _, _gateway_base = _urls()
    verify_url = (
        "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
        if settings.zarinpal_sandbox
        else "https://api.zarinpal.com/pg/v4/payment/verify.json"
    )
    payload = {
        "merchant_id": settings.zarinpal_merchant_id,
        "authority": authority,
        "amount": _rial_amount(amount, currency),
    }
    try:
        async with httpx.AsyncClient(timeout=settings.zarinpal_timeout_seconds, follow_redirects=False) as client:
            response = await client.post(
                verify_url,
                json=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            )
    except httpx.HTTPError as exc:
        raise ValidationAppError("ZarinPal payment verification failed") from exc

    if response.status_code >= 400:
        raise ValidationAppError(f"ZarinPal payment verification rejected: HTTP {response.status_code}")
    try:
        body = response.json()
    except ValueError as exc:
        raise ValidationAppError("ZarinPal returned an invalid verification response") from exc

    data = body.get("data") or {}
    code = data.get("code")
    if code not in {100, 101}:
        errors = body.get("errors") or {}
        message = errors.get("message") or f"provider code {code}"
        raise ValidationAppError(f"ZarinPal payment verification rejected: {message}")
    return data
