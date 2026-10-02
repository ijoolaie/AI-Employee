"""Provider-backed inbound adapter for Sales Employee responses.

The adapter is deliberately narrow: provider selection and webhook secrets are
operator-owned configuration. Runtime payloads cannot choose a provider or a
tenant. The contract-test provider is only a deterministic certification
adapter; real provider integration remains a separate configuration/evidence
boundary.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError


@dataclass(frozen=True)
class SalesInboundResponse:
    tenant_id: uuid.UUID
    event_key: str
    provider_message_id: str
    response_text: str
    provider: str


def _secret_for_tenant(tenant_id: uuid.UUID) -> str | None:
    configured = get_settings().sales_inbound_webhook_secrets or {}
    secret = configured.get(str(tenant_id))
    if secret is None and (get_settings().sales_inbound_provider_name or "").strip().lower() == "contract-test":
        # Deterministic certification fixture only; production providers must
        # use an explicit tenant-scoped secret.
        secret = configured.get("*")
    return secret


def verify_signature(*, body: bytes, signature: str | None, secret: str | None) -> bool:
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def parse_and_verify(
    *,
    tenant_id: uuid.UUID,
    body: bytes,
    event_id: str | None,
    provider_message_id: str | None,
    signature: str | None,
) -> SalesInboundResponse:
    settings = get_settings()
    provider = (settings.sales_inbound_provider_name or "none").strip().lower()

    if provider not in {"contract-test", "generic-webhook"}:
        raise ValidationAppError(
            "Sales inbound response provider is not configured",
            details={"provider_execution": "not_configured"},
        )

    if len(body) > settings.webhook_max_payload_bytes:
        raise ValidationAppError("Sales inbound response payload is too large")
    if not event_id or len(event_id) > 255:
        raise ValidationAppError("Missing or invalid sales inbound event id")
    if not provider_message_id or len(provider_message_id) > 255:
        raise ValidationAppError("Missing or invalid provider message id")

    secret = _secret_for_tenant(tenant_id)
    if not verify_signature(body=body, signature=signature, secret=secret):
        raise ValidationAppError("Invalid sales inbound provider signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationAppError("Invalid sales inbound provider JSON") from exc

    if not isinstance(payload, dict):
        raise ValidationAppError("Sales inbound provider payload must be an object")

    response_text = payload.get("response_text")
    if not isinstance(response_text, str) or not response_text.strip():
        raise ValidationAppError("Sales inbound provider response_text is required")
    if len(response_text) > 8000:
        raise ValidationAppError("Sales inbound provider response_text is too long")

    payload_provider_message_id = payload.get("provider_message_id")
    if payload_provider_message_id and payload_provider_message_id != provider_message_id:
        raise ValidationAppError("Provider message id mismatch")

    return SalesInboundResponse(
        tenant_id=tenant_id,
        event_key=f"provider:{provider}:{event_id}",
        provider_message_id=provider_message_id,
        response_text=response_text.strip(),
        provider=provider,
    )
