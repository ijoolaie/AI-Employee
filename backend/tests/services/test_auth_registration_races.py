from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.services import auth_service


class _Nested:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _Result:
    def __init__(self, row=None):
        self.row = row

    def scalar_one_or_none(self):
        return self.row

    def scalar_one(self):
        if self.row is None:
            raise AssertionError("expected a winner")
        return self.row


class _TenantRaceDb:
    def __init__(self):
        self.added = []
        self.flushes = 0

    def begin_nested(self):
        return _Nested()

    def add(self, row):
        self.added.append(row)

    async def flush(self):
        self.flushes += 1
        raise IntegrityError("INSERT", {}, Exception("duplicate key"))


class _PermissionRaceDb:
    def __init__(self, winner):
        self.winner = winner
        self.executes = 0

    async def execute(self, statement):
        self.executes += 1
        if self.executes == 1:
            return _Result(None)
        if self.executes == 2:
            return _Result(None)
        return _Result(self.winner)


@pytest.mark.asyncio
async def test_create_tenant_maps_unique_slug_race_to_conflict():
    db = _TenantRaceDb()
    payload = SimpleNamespace(
        tenant_name="Acme",
        tenant_slug="acme",
    )

    with pytest.raises(ConflictError, match="Tenant slug already exists"):
        await auth_service._create_tenant(db, payload)

    assert len(db.added) == 1
    assert db.flushes == 1


@pytest.mark.asyncio
async def test_get_or_create_permission_recovers_from_global_unique_race():
    winner = SimpleNamespace(id=uuid4(), code="employee.read")
    db = _PermissionRaceDb(winner)

    permission = await auth_service._get_or_create_permission(db, "employee.read")

    assert permission is winner
    assert db.executes == 3
