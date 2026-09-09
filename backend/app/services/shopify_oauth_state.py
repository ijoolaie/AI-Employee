import base64
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.models.shopify_oauth_state import ShopifyOAuthState


def normalize_shop_domain(shop: str) -> str:
    value = str(shop or "").strip().lower()
    for prefix in ("https://", "http://"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
            break
    return value.rstrip("/")


def _sign(raw: str) -> str:
    return hmac.new(get_settings().secret_key.encode(), raw.encode(), hashlib.sha256).hexdigest()


def _encode(raw: str, signature: str) -> str:
    return base64.urlsafe_b64encode(f"{raw}:{signature}".encode()).decode()


def _hash_state(state: str) -> str:
    return hashlib.sha256(state.encode()).hexdigest()


async def issue_state(db: AsyncSession, tenant_id: uuid.UUID, shop: str) -> str:
    shop_domain = normalize_shop_domain(shop)
    if not shop_domain:
        raise ValidationAppError("Shopify OAuth requires a shop domain")
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=10)
    nonce = secrets.token_urlsafe(24)
    raw = f"{tenant_id}:{shop_domain}:{int(now.timestamp())}:{nonce}"
    state = _encode(raw, _sign(raw))
    db.add(
        ShopifyOAuthState(
            tenant_id=tenant_id,
            state_hash=_hash_state(state),
            shop_domain=shop_domain,
            expires_at=expires_at,
        )
    )
    await db.flush()
    return state


def _parse(state: str) -> tuple[uuid.UUID, str]:
    try:
        decoded = base64.urlsafe_b64decode(state.encode()).decode()
        tenant_raw, shop_domain, timestamp_raw, nonce, signature = decoded.rsplit(":", 4)
        raw = f"{tenant_raw}:{shop_domain}:{timestamp_raw}:{nonce}"
        expected = _sign(raw)
        if not hmac.compare_digest(signature, expected):
            raise ValidationAppError("Invalid Shopify OAuth state")
        tenant_id = uuid.UUID(tenant_raw)
        issued_at = datetime.fromtimestamp(int(timestamp_raw), timezone.utc)
    except ValidationAppError:
        raise
    except Exception as exc:
        raise ValidationAppError("Invalid Shopify OAuth state") from exc
    if datetime.now(timezone.utc) - issued_at > timedelta(minutes=10):
        raise ValidationAppError("Expired Shopify OAuth state")
    if datetime.now(timezone.utc) < issued_at - timedelta(minutes=1):
        raise ValidationAppError("Invalid Shopify OAuth state")
    return tenant_id, normalize_shop_domain(shop_domain)


async def consume_state(db: AsyncSession, state: str, callback_shop: str) -> uuid.UUID:
    tenant_id, state_shop = _parse(state)
    callback_domain = normalize_shop_domain(callback_shop)
    if not callback_domain or not hmac.compare_digest(state_shop, callback_domain):
        raise ValidationAppError("Shopify OAuth state shop mismatch")

    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(ShopifyOAuthState)
        .where(
            ShopifyOAuthState.state_hash == _hash_state(state),
            ShopifyOAuthState.tenant_id == tenant_id,
            ShopifyOAuthState.shop_domain == state_shop,
            ShopifyOAuthState.used_at.is_(None),
            ShopifyOAuthState.expires_at > now,
        )
        .values(used_at=now)
    )
    if result.rowcount != 1:
        raise ValidationAppError("Shopify OAuth state is invalid, expired, or already used")
    return tenant_id
