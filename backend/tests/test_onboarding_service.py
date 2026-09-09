import uuid

import pytest

from app.models.onboarding import OnboardingProgress
from app.services import onboarding_service


@pytest.mark.asyncio
async def test_get_or_create_recovers_from_concurrent_unique_violation():
    tenant_id = uuid.uuid4()
    winner = OnboardingProgress(tenant_id=tenant_id)
    first_lookup = True

    class Result:
        def scalar_one_or_none(self):
            return None if first_lookup else winner

    class Nested:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DB:
        def add(self, item):
            pass

        async def execute(self, statement):
            nonlocal first_lookup
            first_lookup = False
            return Result()

        async def flush(self):
            from sqlalchemy.exc import IntegrityError
            raise IntegrityError("insert", {}, Exception("duplicate"))

        async def refresh(self, item):
            return None

        def begin_nested(self):
            return Nested()

    result = await onboarding_service.get_or_create(DB(), tenant_id)

    assert result is winner
