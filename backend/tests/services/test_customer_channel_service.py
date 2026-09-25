from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import customer_channel_service


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _DB:
    def __init__(self, value):
        self.value = value
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return _Result(self.value)


@pytest.mark.asyncio
async def test_get_conversation_locks_row_for_serialized_public_chat_sends():
    conversation = SimpleNamespace(id=uuid4())
    db = _DB(conversation)

    result = await customer_channel_service._get_conversation(
        db,
        conversation_id=conversation.id,
        token="customer-token",
    )

    assert result is conversation
    assert db.statement._for_update_arg is not None
