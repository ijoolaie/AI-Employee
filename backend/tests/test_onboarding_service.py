"""Focused tests for onboarding initialization concurrency."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.onboarding import OnboardingProgress
from app.services import onboarding_service


@pytest.mark.asyncio
async def test_get_or_create_recovers_from_concurrent_unique_violation():
    tenant_id = uuid.uuid4()
    winner = OnboardingProgress(tenant_id=tenant_id)
    lookup_count = 0

    class Result:
        def scalar_one_or_none(self):
            return None if lookup_count == 1 else winner

    class Nested:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DB:
        def add(self, item):
            assert isinstance(item, OnboardingProgress)
            assert item.tenant_id == tenant_id

        async def execute(self, statement):
            nonlocal lookup_count
            lookup_count += 1
            return Result()

        async def flush(self):
            raise IntegrityError("insert", {}, Exception("duplicate"))

        async def refresh(self, row):
            assert row is winner

        def begin_nested(self):
            return Nested()

    result = await onboarding_service.get_or_create(DB(), tenant_id)

    assert result is winner
    assert lookup_count == 2
