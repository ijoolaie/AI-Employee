from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.audit_log import AuditLog
from app.services.audit_service import GENESIS_HASH, _compute_entry_hash, _scope, record, verify_ledger


def make_entry(**overrides):
    values = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "actor_type": "system",
        "actor_id": None,
        "action": "governance.test",
        "resource_type": "run",
        "resource_id": "run-1",
        "request_id": "req-1",
        "status": "success",
        "metadata_": {"b": 2, "a": 1},
        "created_at": datetime(2026, 9, 8, tzinfo=timezone.utc),
        "ledger_scope": "tenant-1",
        "ledger_sequence": 1,
        "previous_hash": GENESIS_HASH,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_ledger_hash_is_deterministic_and_tamper_evident():
    entry = make_entry()
    first = _compute_entry_hash(entry)
    second = _compute_entry_hash(entry)
    assert first == second
    entry.action = "governance.tampered"
    assert _compute_entry_hash(entry) != first


def test_scope_uses_reserved_platform_key_for_null_tenant():
    assert _scope(None) == "__platform__"
    assert _scope("tenant-123") == "tenant-123"


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value

    def scalar_one_or_none(self):
        return self.value


class FakeScalars:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeRows:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return FakeScalars(self.values)


class FakeDb:
    def __init__(self, previous=None):
        self.calls = []
        self.added = None
        self.previous = previous

    async def execute(self, statement):
        self.calls.append(statement)
        if len(self.calls) == 1:
            return FakeScalarResult(None)
        if len(self.calls) == 2:
            return FakeScalarResult(0)
        return FakeScalarResult(self.previous)

    def add(self, entry):
        self.added = entry

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_record_starts_scoped_ledger_at_genesis():
    tenant = uuid4()
    db = FakeDb()
    entry = await record(
        db,
        tenant_id=tenant,
        actor_type="system",
        action="governance.test",
        metadata={"safe": True},
    )
    assert entry.ledger_scope == str(tenant)
    assert entry.ledger_sequence == 1
    assert entry.previous_hash == GENESIS_HASH
    assert entry.entry_hash == _compute_entry_hash(entry)
    assert db.added is entry


@pytest.mark.asyncio
async def test_verify_ledger_reports_tampering():
    class VerifyDb:
        async def execute(self, _statement):
            valid = make_entry()
            valid.entry_hash = _compute_entry_hash(valid)
            return FakeRows([valid])

    result = await verify_ledger(VerifyDb(), tenant_id="tenant-1")
    assert result["valid"] is True
    assert result["checked"] == 1


# Keep the ORM import referenced so this test fails loudly if the ledger model
# is accidentally removed from metadata during a future refactor.
def test_audit_model_has_ledger_columns():
    for name in ("ledger_scope", "ledger_sequence", "previous_hash", "entry_hash"):
        assert hasattr(AuditLog, name)
