from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, ValidationAppError
from app.services import workforce_delegation_service as service
from app.services.workforce_delegation_service import (
    ALLOWED_MANAGER_OPERATIONS,
    create_delegation,
)


class _Result:
    def __init__(self, values=None, value=None):
        self._values = values or []
        self._value = value

    def scalars(self):
        return self

    def all(self):
        return self._values

    def scalar_one_or_none(self):
        return self._value


class _DB:
    def __init__(self, *, values=None, value=None):
        self.values = values or []
        self.value = value
        self.added = []
        self.flushed = False
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _Result(self.values, self.value)

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        self.flushed = True


def test_manager_operation_catalog_is_bounded():
    assert "staffing_proposal" in ALLOWED_MANAGER_OPERATIONS
    assert "replacement_proposal" in ALLOWED_MANAGER_OPERATIONS
    assert "transfer_proposal" in ALLOWED_MANAGER_OPERATIONS
    assert "retirement_proposal" in ALLOWED_MANAGER_OPERATIONS
    assert "financial_commitment" not in ALLOWED_MANAGER_OPERATIONS
    assert "security_sensitive_change" not in ALLOWED_MANAGER_OPERATIONS


def test_delegation_window_is_timezone_aware_and_bounded():
    start = datetime.now(timezone.utc)
    assert start.tzinfo is not None
    assert start + timedelta(days=366) > start + timedelta(days=365)


@pytest.mark.asyncio
async def test_create_delegation_rejects_non_delegable_operation_before_lookup():
    with pytest.raises(ValidationAppError, match="Unsupported manager delegation operations"):
        await create_delegation(
            object(),
            tenant_id=uuid4(),
            manager_agent_instance_id=uuid4(),
            delegated_by_user_id=uuid4(),
            starts_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            allowed_operations=["financial_commitment"],
        )


@pytest.mark.asyncio
async def test_assert_operation_delegated_allows_scoped_employee_and_operation(monkeypatch):
    employee_id = uuid4()
    now = datetime.now(timezone.utc)
    delegation = type(
        "Delegation",
        (),
        {
            "allowed_operations": ["assign_task"],
            "affected_employee_ids": [str(employee_id)],
            "expires_at": now + timedelta(hours=1),
        },
    )()
    db = _DB(values=[delegation])

    result = await service.assert_operation_delegated(
        db,
        tenant_id=uuid4(),
        manager_agent_instance_id=uuid4(),
        operation="assign_task",
        employee_id=employee_id,
    )
    assert result is delegation

    with pytest.raises(ValidationAppError, match="No active CEO delegation"):
        await service.assert_operation_delegated(
            db,
            tenant_id=uuid4(),
            manager_agent_instance_id=uuid4(),
            operation="prepare_ceo_report",
            employee_id=employee_id,
        )


@pytest.mark.asyncio
async def test_assert_operation_delegated_denies_employee_outside_delegation_scope():
    allowed_employee_id = uuid4()
    other_employee_id = uuid4()
    now = datetime.now(timezone.utc)
    delegation = type(
        "Delegation",
        (),
        {
            "allowed_operations": ["assign_task"],
            "affected_employee_ids": [str(allowed_employee_id)],
            "expires_at": now + timedelta(hours=1),
        },
    )()
    db = _DB(values=[delegation])

    with pytest.raises(ValidationAppError, match="No active CEO delegation"):
        await service.assert_operation_delegated(
            db,
            tenant_id=uuid4(),
            manager_agent_instance_id=uuid4(),
            operation="assign_task",
            employee_id=other_employee_id,
        )


@pytest.mark.asyncio
async def test_assert_operation_delegated_rejects_expired_delegation():
    now = datetime.now(timezone.utc)
    delegation = type(
        "Delegation",
        (),
        {
            "allowed_operations": ["assign_task"],
            "affected_employee_ids": [],
            "expires_at": now - timedelta(seconds=1),
        },
    )()
    db = _DB(values=[delegation])

    with pytest.raises(ValidationAppError, match="No active CEO delegation"):
        await service.assert_operation_delegated(
            db,
            tenant_id=uuid4(),
            manager_agent_instance_id=uuid4(),
            operation="assign_task",
        )


@pytest.mark.asyncio
async def test_create_delegation_normalizes_operations_and_records_actor(monkeypatch):
    manager_id = uuid4()
    actor_id = uuid4()
    audit = {}

    async def fake_get_manager(*args, **kwargs):
        return object()

    async def fake_record(*args, **kwargs):
        audit.update(kwargs)

    monkeypatch.setattr(service, "_get_manager", fake_get_manager)
    monkeypatch.setattr(service, "record", fake_record)

    db = _DB()
    start = datetime.now(timezone.utc)
    item = await create_delegation(
        db,
        tenant_id=uuid4(),
        manager_agent_instance_id=manager_id,
        delegated_by_user_id=actor_id,
        starts_at=start,
        expires_at=start + timedelta(hours=1),
        allowed_operations=["assign_task", "assign_task"],
        affected_employee_ids=[str(uuid4())],
        risk_tier=2,
    )

    assert item.allowed_operations == ["assign_task"]
    assert item.risk_tier == 2
    assert item.status == "active"
    assert db.flushed is True
    assert audit["actor_id"] == actor_id
    assert audit["action"] == "workforce.delegation.created"


@pytest.mark.asyncio
async def test_revoke_delegation_is_tenant_scoped_and_row_locked(monkeypatch):
    delegation_id = uuid4()
    revoker_id = uuid4()
    audit = {}
    item = type(
        "Delegation",
        (),
        {
            "id": delegation_id,
            "status": "active",
            "revoked_at": None,
            "revoked_by_user_id": None,
        },
    )()
    db = _DB(value=item)

    async def fake_record(*args, **kwargs):
        audit.update(kwargs)

    monkeypatch.setattr(service, "record", fake_record)

    result = await service.revoke_delegation(
        db,
        tenant_id=uuid4(),
        delegation_id=delegation_id,
        revoked_by_user_id=revoker_id,
        reason="CEO revoked delegation",
    )

    assert result is item
    assert item.status == "revoked"
    assert item.revoked_by_user_id == revoker_id
    assert item.revoked_at is not None
    assert db.flushed is True
    assert db.statements[0]._for_update_arg is not None
    assert audit["actor_id"] == revoker_id
    assert audit["action"] == "workforce.delegation.revoked"


@pytest.mark.asyncio
async def test_revoke_delegation_rejects_double_revoke():
    item = type("Delegation", (), {"status": "revoked"})()
    db = _DB(value=item)

    with pytest.raises(ConflictError, match="already revoked"):
        await service.revoke_delegation(
            db,
            tenant_id=uuid4(),
            delegation_id=uuid4(),
            revoked_by_user_id=uuid4(),
            reason="duplicate",
        )
