"""PostgreSQL + HTTP acceptance for Business Network tenant boundaries."""

import os
import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def _database_url() -> str:
    raw = os.environ.get("SUPPORT_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
    if not raw:
        raise RuntimeError(
            "Dedicated local support_test database URL is required; refusing to run."
        )
    parsed = make_url(raw)
    if (
        parsed.drivername != "postgresql+asyncpg"
        or parsed.username not in {"support_test_user", "aiep"}
        or parsed.host not in {"127.0.0.1", "localhost"}
        or parsed.port not in {5432, 15433}
        or parsed.database != "support_test"
        or not parsed.password
    ):
        raise RuntimeError(
            "URL must target the dedicated local support_test database; refusing to run."
        )
    return raw


@pytest.mark.asyncio
async def test_business_network_sender_decision_and_recipient_isolation():
    database_url = _database_url()
    from app.core.database import get_db
    from app.core.security import create_access_token
    from app.main import app
    from app.models.audit_log import AuditLog
    from app.models.business_network_request import (
        BusinessNetworkRequest,
        BusinessNetworkRequestStatus,
    )
    from app.models.role import Permission, Role
    from app.models.tenant import Tenant
    from app.models.user import User

    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    run_id = uuid.uuid4().hex
    sender = Tenant(
        name=f"Network sender {run_id}",
        slug=f"network-sender-{run_id}",
        status="active",
        tenant_kind="vendor",
        settings={},
    )
    recipient = Tenant(
        name=f"Network recipient {run_id}",
        slug=f"network-recipient-{run_id}",
        status="active",
        tenant_kind="vendor",
        settings={},
    )
    try:
        async with sessions() as session:
            session.add_all([sender, recipient])
            await session.flush()
            requester = User(
                tenant_id=sender.id,
                email=f"network-requester-{run_id}@example.test",
                password_hash="unused",
                full_name="Network Requester",
                is_active=True,
                is_superuser=False,
                is_platform_admin=False,
                roles=[],
            )
            sponsor = User(
                tenant_id=sender.id,
                email=f"network-sponsor-{run_id}@example.test",
                password_hash="unused",
                full_name="Network Sponsor",
                is_active=True,
                is_superuser=False,
                is_platform_admin=False,
                roles=[],
            )
            sender_decider = User(
                tenant_id=sender.id,
                email=f"network-decider-{run_id}@example.test",
                password_hash="unused",
                full_name="Network Decider",
                is_active=True,
                is_superuser=False,
                is_platform_admin=False,
                roles=[],
            )
            recipient_decider = User(
                tenant_id=recipient.id,
                email=f"network-recipient-decider-{run_id}@example.test",
                password_hash="unused",
                full_name="Recipient Decider",
                is_active=True,
                is_superuser=False,
                is_platform_admin=False,
                roles=[],
            )
            session.add_all([requester, sponsor, sender_decider, recipient_decider])
            await session.flush()
            permissions = {}
            for code in ("business_network.submit", "business_network.decide"):
                permission = (
                    await session.execute(select(Permission).where(Permission.code == code))
                ).scalar_one_or_none()
                if permission is None:
                    permission = Permission(
                        code=code, description=f"Business Network {code.rsplit('.', 1)[-1]}"
                    )
                    session.add(permission)
                    await session.flush()
                permissions[code] = permission
            sender_role = Role(
                tenant_id=sender.id,
                name=f"network-sender-admin-{run_id}",
                description="Business Network sender test role",
            )
            sender_role.permissions = list(permissions.values())
            recipient_role = Role(
                tenant_id=recipient.id,
                name=f"network-recipient-admin-{run_id}",
                description="Business Network recipient test role",
            )
            recipient_role.permissions = [permissions["business_network.decide"]]
            requester.roles = [sender_role]
            sponsor.roles = [sender_role]
            sender_decider.roles = [sender_role]
            recipient_decider.roles = [recipient_role]
            session.add_all([sender_role, recipient_role])
            await session.commit()

        async def override_get_db() -> AsyncIterator[AsyncSession]:
            async with sessions() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        missing = object()
        previous = app.dependency_overrides.get(get_db, missing)
        app.dependency_overrides[get_db] = override_get_db
        try:

            def headers(user: User, tenant: Tenant):
                token = create_access_token(
                    subject=user.id,
                    tenant_id=tenant.id,
                    extra_claims={"auth_token_version": user.auth_token_version},
                )
                return {"Authorization": f"Bearer {token}"}

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                created = await client.post(
                    "/api/v1/business-network/requests",
                    headers=headers(requester, sender),
                    json={
                        "recipient_tenant_id": str(recipient.id),
                        "operation": "share_capability",
                        "capability_contract": {"capability": "catalog.read", "version": 1},
                        "payload": {"resource": "public-catalog"},
                        "idempotency_key": f"network-{run_id}",
                        "sponsor_user_id": str(sponsor.id),
                    },
                )
                assert created.status_code == 201, created.text
                request_id = uuid.UUID(created.json()["id"])
                assert created.json()["sender_tenant_id"] == str(sender.id)
                assert created.json()["recipient_tenant_id"] == str(recipient.id)
                assert created.json()["status"] == "pending_approval"

                foreign_decision = await client.post(
                    f"/api/v1/business-network/requests/{request_id}/decision",
                    headers=headers(recipient_decider, recipient),
                    json={
                        "approve": True,
                        "reason": "Recipient cannot decide sender-owned request",
                    },
                )
                assert foreign_decision.status_code == 404, foreign_decision.text

                sender_decision = await client.post(
                    f"/api/v1/business-network/requests/{request_id}/decision",
                    headers=headers(sender_decider, sender),
                    json={"approve": True, "reason": "Independent sender approval"},
                )
                assert sender_decision.status_code == 200, sender_decision.text
                assert sender_decision.json()["status"] == "approved"
                assert sender_decision.json()["decision_by"] == str(sender_decider.id)
        finally:
            if previous is missing:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous

        async with sessions() as session:
            persisted = await session.get(BusinessNetworkRequest, request_id)
            assert persisted is not None
            assert persisted.sender_tenant_id == sender.id
            assert persisted.recipient_tenant_id == recipient.id
            assert persisted.status == BusinessNetworkRequestStatus.APPROVED
            assert persisted.decision_by == sender_decider.id
            events = (
                (
                    await session.execute(
                        select(AuditLog).where(
                            AuditLog.resource_id == str(request_id),
                            AuditLog.action.in_(
                                [
                                    "business_network.request.submitted",
                                    "business_network.request.decided",
                                ]
                            ),
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(events) == 2
            assert {event.tenant_id for event in events} == {sender.id}
    finally:
        await engine.dispose()
