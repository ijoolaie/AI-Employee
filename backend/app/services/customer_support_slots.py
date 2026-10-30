"""Validated, provenance-bearing support slots for customer conversations.

Only explicitly labelled values are extracted. Free-form transcript text and
assistant/model output are never treated as authoritative slot sources.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import CustomerConversation, CustomerMessage
from app.models.customer_conversation_slot import CustomerConversationSlot
from app.services.support_slot_filling import find_trusted_shipping_city

ALLOWED_SLOT_NAMES = frozenset({
    "city", "order_id", "payment_reference", "product", "color", "size",
    "quantity", "reason", "issue_details",
})
_SLOT_TTLS = {
    "city": timedelta(days=30),
    "order_id": timedelta(hours=24),
    "payment_reference": timedelta(hours=24),
    "product": timedelta(days=30),
    "color": timedelta(days=30),
    "size": timedelta(days=30),
    "quantity": timedelta(hours=24),
    "reason": timedelta(days=7),
    "issue_details": timedelta(days=7),
}
_LABELS = {
    "order_id": r"(?:شماره\s*سفارش|کد\s*سفارش|order\s*(?:id|number))",
    "payment_reference": r"(?:شماره\s*پیگیری|کد\s*پیگیری|payment\s*reference|transaction\s*id)",
    "product": r"(?:محصول|کالا|product)",
    "color": r"(?:رنگ|color)",
    "size": r"(?:سایز|اندازه|size)",
    "quantity": r"(?:تعداد|quantity|qty)",
    "reason": r"(?:دلیل\s*(?:مرجوعی|تعویض)?|reason)",
    "issue_details": r"(?:شرح\s*مشکل|توضیح\s*مشکل|issue\s*details)",
}
_MAX_VALUE_LENGTH = 500


def _normalize_digits(value: str) -> str:
    return value.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))


def _clean_value(value: str) -> str | None:
    value = " ".join(value.strip().strip(" \t\r\n:：،,؛;.!؟?").split())
    if not value or len(value) > _MAX_VALUE_LENGTH:
        return None
    return value


def _labelled_values(message: str, label_pattern: str) -> list[str]:
    pattern = re.compile(
        rf"(?:^|[\n،,;；])\s*{label_pattern}\s*[:：=\-]?\s*(.+?)(?=$|[\n،,;；])",
        re.IGNORECASE,
    )
    return [
        value for match in pattern.finditer(message)
        if (value := _clean_value(match.group(1))) is not None
    ]


def extract_explicit_customer_slots(
    message: str,
    *,
    support_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract only conservative, explicitly supplied values from one user turn."""
    if not isinstance(message, str) or not message.strip():
        return {}
    candidates: dict[str, Any] = {}
    policy = support_policy if isinstance(support_policy, dict) else {}
    shipping = policy.get("shipping") if isinstance(policy.get("shipping"), dict) else {}
    rates = shipping.get("rates_by_city", {})
    known = {item for item in rates.keys() if isinstance(item, str)} if isinstance(rates, dict) else set()
    cities = shipping.get("cities", shipping.get("known_cities", []))
    if isinstance(cities, list):
        known.update(item for item in cities if isinstance(item, str))

    city = find_trusted_shipping_city(message, shipping)
    if city and known:
        # If the message names multiple configured cities, it is ambiguous.
        matches = {
            item for item in known
            if re.search(rf"(?<![\w]){re.escape(item)}(?![\w])", message, re.UNICODE)
        }
        if len(matches) == 1:
            candidates["city"] = next(iter(matches))
        elif len(matches) > 1:
            candidates["city"] = None

    if "city" not in candidates and known:
        explicit_destination = re.search(
            r"(?:به|برای)\s+(?!کدوم\s+شهر|چه\s+شهری|همون\s+شهر|همان\s+شهر|همون\s+مقصد|همان\s+مقصد)([\w‌-]+)",
            message,
            re.UNICODE,
        )
        if explicit_destination:
            # A new but unconfigured destination invalidates an older city.
            candidates["city"] = None

    for slot_name, label in _LABELS.items():
        values = _labelled_values(message, label)
        if not values:
            continue
        unique_values = set(values)
        if len(unique_values) != 1:
            candidates[slot_name] = None
            continue
        value = next(iter(unique_values))
        if slot_name in {"order_id", "payment_reference"}:
            token = re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]{2,63}", value)
            if token is None:
                candidates[slot_name] = None
                continue
            value = token.group(0)
        if slot_name == "quantity":
            normalized = _normalize_digits(value)
            number = re.fullmatch(r"(\d{1,6})(?:\s*(?:عدد|pcs|items?))?", normalized, re.IGNORECASE)
            quantity = int(number.group(1)) if number else 0
            candidates[slot_name] = quantity if 1 <= quantity <= 1_000_000 else None
        else:
            candidates[slot_name] = value
    return {key: value for key, value in candidates.items() if key in ALLOWED_SLOT_NAMES}


async def upsert_customer_conversation_slots(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    conversation_id: uuid.UUID,
    source_message_id: uuid.UUID,
    candidates: dict[str, Any],
    now: datetime | None = None,
) -> int:
    """Upsert allowlisted values from a verified customer-authored source turn."""
    if not candidates:
        return 0
    captured_at = now or datetime.now(timezone.utc)
    source = (await db.execute(
        select(CustomerMessage).where(
            CustomerMessage.id == source_message_id,
            CustomerMessage.tenant_id == tenant_id,
            CustomerMessage.conversation_id == conversation_id,
            CustomerMessage.role == "user",
        )
    )).scalar_one_or_none()
    if source is None:
        raise ValueError("Support slot source must be a customer-authored message in this tenant conversation")
    conversation = (await db.execute(
        select(CustomerConversation).where(
            CustomerConversation.id == conversation_id,
            CustomerConversation.tenant_id == tenant_id,
        )
    )).scalar_one_or_none()
    if conversation is None:
        raise ValueError("Support slot conversation does not belong to tenant")

    written = 0
    for slot_name, value in candidates.items():
        if slot_name not in ALLOWED_SLOT_NAMES:
            continue
        if isinstance(value, str):
            value = _clean_value(value)
            if value is None:
                continue
            if value.casefold() not in (source.content or "").casefold():
                raise ValueError("Support slot value must be present in its source customer message")
        elif value is not None and slot_name == "quantity":
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 1_000_000:
                value = None
            elif str(value) not in _normalize_digits(source.content or ""):
                raise ValueError("Support slot quantity must be present in its source customer message")
        elif value is not None:
            continue

        existing = (await db.execute(
            select(CustomerConversationSlot).where(
                CustomerConversationSlot.tenant_id == tenant_id,
                CustomerConversationSlot.conversation_id == conversation_id,
                CustomerConversationSlot.slot_name == slot_name,
            ).with_for_update()
        )).scalar_one_or_none()
        if value is None:
            if existing is not None:
                await db.delete(existing)
                written += 1
            continue
        expires_at = captured_at + _SLOT_TTLS[slot_name]
        if existing is None:
            db.add(CustomerConversationSlot(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                source_message_id=source_message_id,
                slot_name=slot_name,
                value=value,
                captured_at=captured_at,
                expires_at=expires_at,
            ))
        else:
            # A later explicit customer turn supersedes the prior value.
            existing.source_message_id = source_message_id
            existing.value = value
            existing.captured_at = captured_at
            existing.expires_at = expires_at
        written += 1
    if written:
        await db.flush()
    return written


async def load_valid_customer_conversation_slots(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    conversation_id: uuid.UUID,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Load unexpired slots only when their source is still a user message."""
    current = now or datetime.now(timezone.utc)
    result = await db.execute(
        select(CustomerConversationSlot)
        .join(
            CustomerMessage,
            (CustomerMessage.id == CustomerConversationSlot.source_message_id)
            & (CustomerMessage.tenant_id == CustomerConversationSlot.tenant_id)
            & (CustomerMessage.conversation_id == CustomerConversationSlot.conversation_id)
            & (CustomerMessage.role == "user"),
        )
        .where(
            CustomerConversationSlot.tenant_id == tenant_id,
            CustomerConversationSlot.conversation_id == conversation_id,
            CustomerConversationSlot.slot_name.in_(ALLOWED_SLOT_NAMES),
            CustomerConversationSlot.expires_at > current,
        )
    )
    rows = result.scalars().all()
    return {
        row.slot_name: row.value
        for row in rows
        if row.slot_name in ALLOWED_SLOT_NAMES and row.value is not None
    }
