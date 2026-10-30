from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.customer_support_slots import (
    ALLOWED_SLOT_NAMES,
    extract_explicit_customer_slots,
    load_valid_customer_conversation_slots,
    upsert_customer_conversation_slots,
)


def test_extracts_only_allowlisted_explicit_customer_fields_and_normalizes_digits():
    slots = extract_explicit_customer_slots(
        "شماره سفارش: ORD-123\nشماره پیگیری: PAY-456\nتعداد: ۱۲\nرنگ: آبی",
        support_policy={},
    )
    assert slots == {
        "order_id": "ORD-123",
        "payment_reference": "PAY-456",
        "quantity": 12,
        "color": "آبی",
    }
    assert set(slots).issubset(ALLOWED_SLOT_NAMES)


def test_city_is_extracted_only_from_current_turn_and_trusted_tenant_policy():
    policy = {"shipping": {"cities": ["تهران", "شیراز"], "rates_by_city": {"تهران": 50000}}}
    assert extract_explicit_customer_slots(
        "هزینه ارسال به تهران چقدر است؟", support_policy=policy
    ) == {"city": "تهران"}
    assert extract_explicit_customer_slots(
        "هزینه ارسال به اصفهان چقدر است؟", support_policy=policy
    ) == {"city": None}


def test_ambiguous_multiple_configured_cities_are_not_persisted():
    policy = {"shipping": {"cities": ["تهران", "شیراز"]}}
    assert extract_explicit_customer_slots(
        "ارسال از تهران به شیراز چقدر می‌شود؟", support_policy=policy
    ) == {"city": None}


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _SourceOnlyDB:
    def __init__(self, source):
        self.source = source
        self.calls = 0

    async def execute(self, statement):
        self.calls += 1
        if self.calls == 1:
            return _Result(self.source if getattr(self.source, "role", None) == "user" else None)
        return _Result(SimpleNamespace())


@pytest.mark.asyncio
async def test_upsert_rejects_assistant_message_as_slot_provenance():
    tenant_id, conversation_id, message_id = uuid4(), uuid4(), uuid4()
    db = _SourceOnlyDB(SimpleNamespace(role="assistant"))
    with pytest.raises(ValueError, match="customer-authored"):
        await upsert_customer_conversation_slots(
            db,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            source_message_id=message_id,
            candidates={"city": "تهران"},
            now=datetime(2026, 10, 30, tzinfo=timezone.utc),
        )
    assert db.calls == 1


class _Rows:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return self

    def all(self):
        return self.rows


class _LoadSlotsDB:
    def __init__(self, rows):
        self.rows = rows

    async def execute(self, statement):
        return _Rows(self.rows)


@pytest.mark.asyncio
async def test_load_valid_slots_filters_unknown_names_and_null_values():
    db = _LoadSlotsDB([
        SimpleNamespace(slot_name="city", value="تهران"),
        SimpleNamespace(slot_name="invented", value="untrusted"),
        SimpleNamespace(slot_name="order_id", value=None),
    ])
    result = await load_valid_customer_conversation_slots(
        db, tenant_id=uuid4(), conversation_id=uuid4(),
        now=datetime(2026, 10, 30, tzinfo=timezone.utc),
    )
    assert result == {"city": "تهران"}


def test_conflicting_explicit_order_references_invalidate_instead_of_overwrite():
    slots = extract_explicit_customer_slots(
        "شماره سفارش: ORD-123، شماره سفارش: ORD-456",
        support_policy={},
    )
    assert slots == {"order_id": None}


class _SequenceDB:
    def __init__(self, values):
        self.values = list(values)
        self.deleted = []
        self.flushed = False

    async def execute(self, statement):
        return _Result(self.values.pop(0))

    async def delete(self, value):
        self.deleted.append(value)

    async def flush(self):
        self.flushed = True


@pytest.mark.asyncio
async def test_explicit_conflict_deletes_old_slot_instead_of_reusing_it():
    tenant_id, conversation_id, message_id = uuid4(), uuid4(), uuid4()
    existing = SimpleNamespace(slot_name="order_id", value="ORD-OLD")
    db = _SequenceDB([
        SimpleNamespace(role="user"),
        SimpleNamespace(id=conversation_id, tenant_id=tenant_id),
        existing,
    ])
    written = await upsert_customer_conversation_slots(
        db,
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        source_message_id=message_id,
        candidates={"order_id": None},
        now=datetime(2026, 10, 30, tzinfo=timezone.utc),
    )
    assert written == 1
    assert db.deleted == [existing]
    assert db.flushed


@pytest.mark.asyncio
async def test_upsert_rejects_slot_value_not_present_in_source_message():
    tenant_id, conversation_id, message_id = uuid4(), uuid4(), uuid4()
    db = _SourceOnlyDB(SimpleNamespace(role="user", content="هزینه ارسال به تهران"))
    with pytest.raises(ValueError, match="present in its source"):
        await upsert_customer_conversation_slots(
            db,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            source_message_id=message_id,
            candidates={"city": "شیراز"},
            now=datetime(2026, 10, 30, tzinfo=timezone.utc),
        )
    assert db.calls == 1


def test_alternative_configured_and_unconfigured_destinations_invalidate_city():
    policy = {"shipping": {"cities": ["تهران"], "rates_by_city": {"تهران": 50000}}}
    assert extract_explicit_customer_slots(
        "هزینه ارسال به تهران یا اصفهان؟", support_policy=policy
    ) == {"city": None}
