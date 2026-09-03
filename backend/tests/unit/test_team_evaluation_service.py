from __future__ import annotations

import uuid

import pytest

from app.services.team_evaluation import TeamEvaluationError, TeamEvaluationService


class FakeScalar:
    def __init__(self, value):
        self.value = value

    def one_or_none(self):
        return self.value


class FakeResult:
    def __init__(self, value):
        self.value = value

    def one_or_none(self):
        return self.value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.value


class FakeSession:
    def __init__(self, pair=None, item=None):
        self.pair = pair
        self.item = item
        self.added = []
        self.flushed = False

    async def execute(self, query):
        return FakeResult(self.pair if self.pair is not None else self.item)

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        self.flushed = True
        if self.added and getattr(self.added[-1], "id", None) is None:
            self.added[-1].id = uuid.uuid4()


@pytest.mark.asyncio
async def test_cross_tenant_version_is_rejected():
    db = FakeSession(pair=None)
    with pytest.raises(TeamEvaluationError, match="not found"):
        await TeamEvaluationService(db).create(
            tenant_id=uuid.uuid4(), team_version_id=uuid.uuid4(), evaluator_id=None,
            evaluation_type="quality", score=.8, input_data={}, output_data={}, metrics={}, notes=None,
        )


@pytest.mark.asyncio
async def test_sensitive_evidence_is_rejected():
    db = FakeSession(pair=(object(), object()))
    with pytest.raises(TeamEvaluationError, match="forbidden"):
        await TeamEvaluationService(db).create(
            tenant_id=uuid.uuid4(), team_version_id=uuid.uuid4(), evaluator_id=None,
            evaluation_type="quality", score=.8, input_data={},
            output_data={"api_token": "secret"}, metrics={}, notes=None,
        )


@pytest.mark.asyncio
async def test_evaluation_is_created_for_authorized_version():
    db = FakeSession(pair=(object(), object()))
    item = await TeamEvaluationService(db).create(
        tenant_id=uuid.uuid4(), team_version_id=uuid.uuid4(), evaluator_id=uuid.uuid4(),
        evaluation_type="quality", score=.9, input_data={"x": 1}, output_data={"y": 2},
        metrics={"latency_ms": 20}, notes="baseline",
    )
    assert item.evidence_class == "engineering"
    assert item.score == .9
    assert db.flushed is True


@pytest.mark.asyncio
async def test_invalid_score_is_rejected():
    db = FakeSession(pair=(object(), object()))
    with pytest.raises(TeamEvaluationError, match="score"):
        await TeamEvaluationService(db).create(
            tenant_id=uuid.uuid4(), team_version_id=uuid.uuid4(), evaluator_id=None,
            evaluation_type="quality", score=1.1, input_data={}, output_data={}, metrics={}, notes=None,
        )
