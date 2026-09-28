from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.services import agent_governance as service


class Result:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values


@pytest.mark.asyncio
async def test_governance_user_attribution_rejects_cross_tenant_user():
    tenant_id = uuid4()
    user_id = uuid4()
    db = type("DB", (), {"execute": AsyncMock(return_value=Result([]))})()

    with pytest.raises(ValidationAppError, match="sponsor_user_id"):
        await service.assert_users_belong_to_tenant(
            db,
            tenant_id=tenant_id,
            user_ids={user_id},
            field_names={user_id: "sponsor_user_id"},
        )


@pytest.mark.asyncio
async def test_governance_user_attribution_accepts_users_from_same_tenant():
    tenant_id = uuid4()
    user_id = uuid4()
    db = type("DB", (), {"execute": AsyncMock(return_value=Result([user_id]))})()

    await service.assert_users_belong_to_tenant(
        db,
        tenant_id=tenant_id,
        user_ids={user_id},
        field_names={user_id: "sponsor_user_id"},
    )
    db.execute.assert_awaited_once()
