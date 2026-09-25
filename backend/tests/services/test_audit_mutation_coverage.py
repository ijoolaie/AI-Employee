import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.onboarding import OnboardingProgress
from app.services import billing_service, feedback_service, onboarding_service


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value


@pytest.mark.asyncio
async def test_onboarding_update_audits_actor(monkeypatch):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    row = OnboardingProgress(id=uuid.uuid4(), tenant_id=tenant_id, setup_data={}, completed_steps=[], current_step=1, completed=False)
    audits = []

    class DB:
        def __init__(self):
            self.refreshed = False

        async def execute(self, statement):
            return Result(row)

        async def flush(self):
            return None

        async def refresh(self, value):
            self.refreshed = value is row

    async def record(*args, **kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(onboarding_service.audit_service, "record", record)
    result = await onboarding_service.update(DB(), tenant_id, 2, "retail", {"x": 1}, True, actor_id=actor_id)

    assert result is row
    assert audits[0]["action"] == "onboarding.progress_updated"
    assert audits[0]["actor_id"] == actor_id
    assert audits[0]["tenant_id"] == tenant_id
    assert audits[0]["resource_id"] == str(row.id)


@pytest.mark.asyncio
async def test_change_plan_audits_actor(monkeypatch):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    subscription = SimpleNamespace(id=uuid.uuid4(), plan_id=uuid.uuid4(), status="trialing", cancel_at_period_end=False, canceled_at=None, current_period_end=__import__("datetime").datetime.now(__import__("datetime").timezone.utc) + __import__("datetime").timedelta(days=30), trial_ends_at=None, provider="stripe")
    plan = SimpleNamespace(id=uuid.uuid4(), code="business", is_active=True)
    audits = []

    class DB:
        def __init__(self):
            self.calls = 0

        async def execute(self, statement):
            self.calls += 1
            return Result(subscription if self.calls == 1 else plan)

        async def flush(self):
            return None

    async def record(*args, **kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(billing_service.audit_service, "record", record)
    result = await billing_service.change_plan(DB(), tenant_id=tenant_id, plan_code="business", actor_id=actor_id)

    assert result is subscription
    assert audits[0]["action"] == "billing.subscription.plan_changed"
    assert audits[0]["actor_id"] == actor_id
    assert audits[0]["tenant_id"] == tenant_id


@pytest.mark.asyncio
async def test_cancel_subscription_audits_actor(monkeypatch):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    subscription = SimpleNamespace(id=uuid.uuid4(), plan_id=uuid.uuid4(), status="active", cancel_at_period_end=False, canceled_at=None, current_period_end=SimpleNamespace(), provider="stripe", trial_ends_at=None)
    audits = []

    class DB:
        async def execute(self, statement):
            return Result(subscription)

        async def flush(self):
            return None

    async def record(*args, **kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(billing_service.audit_service, "record", record)
    result = await billing_service.cancel_subscription(DB(), tenant_id=tenant_id, at_period_end=True, actor_id=actor_id)

    assert result is subscription
    assert audits[0]["action"] == "billing.subscription.cancellation_updated"
    assert audits[0]["actor_id"] == actor_id
    assert audits[0]["tenant_id"] == tenant_id
    assert subscription.cancel_at_period_end is True


@pytest.mark.asyncio
async def test_feedback_creation_audits_actor(monkeypatch):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    audits = []

    class DB:
        def __init__(self):
            self.added = []

        def add(self, value):
            self.added.append(value)

        async def flush(self):
            if self.added:
                self.added[0].id = uuid.uuid4()

        async def commit(self):
            return None

        async def refresh(self, value):
            return None

    async def record(*args, **kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(feedback_service.audit_service, "record", record)
    result = await feedback_service.create_feedback(
        DB(),
        tenant_id=tenant_id,
        user_id=user_id,
        rating=5,
        comment="great",
        run_id=None,
        employee_id=None,
        category="product",
    )

    assert result.rating == 5
    assert audits[0]["action"] == "feedback.created"
    assert audits[0]["actor_id"] == user_id
    assert audits[0]["tenant_id"] == tenant_id
    assert audits[0]["resource_type"] == "feedback"
