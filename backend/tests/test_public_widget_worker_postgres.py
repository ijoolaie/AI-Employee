"""PostgreSQL-backed public widget -> worker -> assistant transcript test."""

from __future__ import annotations
import os, uuid
import pytest
from sqlalchemy import delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from app.ai.schemas import ChatResult
from app.core import database
from app.models.conversation import CustomerConversation, CustomerMessage
from app.models.customer_channel import CustomerChannel
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.tenant import Tenant


def _support_test_database_url():
    url = os.environ.get("SUPPORT_TEST_DATABASE_URL")
    if not url:
        pytest.skip("SUPPORT_TEST_DATABASE_URL is not configured")
    parsed = make_url(url)
    if (
        parsed.drivername != "postgresql+asyncpg"
        or parsed.host not in {"127.0.0.1", "localhost"}
        or parsed.port not in {5432, 15433}
        or parsed.database != "support_test"
        or parsed.username not in {"support_test_user", "aiep"}
        or not parsed.password
    ):
        raise RuntimeError("Refusing to run outside dedicated local support_test database")
    return url


class _DeterministicGateway:
    calls = 0

    async def chat(self, _db, _request, **_kwargs):
        type(self).calls += 1
        return ChatResult(
            content="DETERMINISTIC_ASSISTANT_REPLY",
            prompt_tokens=11,
            completion_tokens=7,
            tool_calls=[],
        )


@pytest.mark.asyncio
async def test_public_widget_run_is_executed_by_worker_and_persisted_to_transcript(monkeypatch):
    from app.services import customer_channel_service, run_service
    from app.workers import run_worker

    url = _support_test_database_url()
    monkeypatch.setattr(database.settings, "database_url", url)
    monkeypatch.setattr(run_service, "AIGateway", _DeterministicGateway)
    monkeypatch.setattr(run_service, "extract_and_consolidate_run_memory", _noop)
    monkeypatch.setattr(run_service.audit_service, "record", _noop)
    monkeypatch.setattr(run_worker.execute_run_task, "delay", lambda *_a, **_k: None)
    _DeterministicGateway.calls = 0
    engine = create_async_engine(url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    suffix = uuid.uuid4().hex
    tenant_id, employee_id, version_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    channel_id = uuid.uuid4()
    conversation_id = run_id = token = None

    try:
        async with sessions() as session:
            async with session.begin():
                tenant = Tenant(
                    id=tenant_id,
                    name=f"Widget worker {suffix}",
                    slug=f"widget-worker-{suffix}",
                    tenant_kind="vendor",
                    status="active",
                )
                employee = Employee(
                    id=employee_id,
                    tenant_id=tenant_id,
                    slug=f"widget-worker-{suffix}",
                    name="Widget worker test employee",
                    kind="custom",
                    is_active=True,
                )
                version = EmployeeVersion(
                    id=version_id,
                    employee_id=employee_id,
                    version_number=1,
                    is_current=True,
                    input_schema={},
                    output_schema={},
                    prompt_template="Answer the customer clearly.",
                    allowed_tools=[],
                    rules={},
                )
                channel = CustomerChannel(
                    id=channel_id,
                    tenant_id=tenant_id,
                    employee_id=employee_id,
                    name="Worker integration test",
                    channel_type="web_widget",
                    public_key=f"pk_worker_{suffix}",
                    config={},
                    is_active=True,
                )
                session.add(tenant)
                await session.flush()
                session.add(employee)
                await session.flush()
                session.add(version)
                await session.flush()
                session.add(channel)
                await session.flush()
                conversation, token, _ = await customer_channel_service.create_conversation(
                    session,
                    public_key=f"pk_worker_{suffix}",
                    customer_name="Synthetic widget customer",
                    customer_email=None,
                    customer_phone=None,
                )
                conversation, run = await customer_channel_service.send_message(
                    session,
                    conversation_id=conversation.id,
                    token=token,
                    content="Hello, how can you help?",
                )
                conversation_id, run_id = conversation.id, run.id
                await session.commit()

        # Actual worker session, execution fence, RunService, and DB writes.
        await run_worker._run_async(str(run_id), str(tenant_id))

        async with sessions() as session:
            persisted_run = await session.get(Run, run_id)
            _, _, transcript_messages = await customer_channel_service.get_public_conversation(
                session, conversation_id=conversation_id, token=token
            )
            assistant_turns = [
                message
                for message in transcript_messages
                if message.run_id == run_id and message.role == "assistant"
            ]
            assert _DeterministicGateway.calls == 1
            assert persisted_run.status == "success"
            assert persisted_run.output_data == {"content": "DETERMINISTIC_ASSISTANT_REPLY"}
            assert persisted_run.total_tokens == 18
            assert len(assistant_turns) == 1
            assert assistant_turns[0].content == "DETERMINISTIC_ASSISTANT_REPLY"
    finally:
        async with sessions() as session:
            async with session.begin():
                await session.execute(
                    delete(CustomerMessage).where(CustomerMessage.tenant_id == tenant_id)
                )
                await session.execute(delete(Run).where(Run.tenant_id == tenant_id))
                await session.execute(
                    delete(CustomerConversation).where(CustomerConversation.tenant_id == tenant_id)
                )
                await session.execute(
                    delete(CustomerChannel).where(CustomerChannel.tenant_id == tenant_id)
                )
                await session.execute(
                    delete(EmployeeVersion).where(EmployeeVersion.id == version_id)
                )
                await session.execute(delete(Employee).where(Employee.id == employee_id))
                await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await engine.dispose()


async def _noop(*_args, **_kwargs):
    return None
