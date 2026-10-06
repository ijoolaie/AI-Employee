"""Governed company-to-company request lifecycle; no remote execution."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.business_network_request import BusinessNetworkRequest, BusinessNetworkRequestStatus
from app.models.tenant import Tenant
from app.services.agent_governance import assert_users_belong_to_tenant
from app.services.audit_service import record
async def create_request(db:AsyncSession,*,sender_tenant_id:uuid.UUID,requester_user_id:uuid.UUID,sponsor_user_id:uuid.UUID,recipient_tenant_id:uuid.UUID,operation:str,capability_contract:dict,payload:dict,idempotency_key:str,correlation_id:str|None=None):
    if sender_tenant_id==recipient_tenant_id: raise ValidationAppError("Business Network requests require distinct sender and recipient tenants")
    if requester_user_id==sponsor_user_id: raise ValidationAppError("Requester and sponsor must be independently attributable")
    await assert_users_belong_to_tenant(db,tenant_id=sender_tenant_id,user_ids={requester_user_id,sponsor_user_id},field_names={requester_user_id:"requester_user_id",sponsor_user_id:"sponsor_user_id"})
    if await db.scalar(select(Tenant.id).where(Tenant.id==recipient_tenant_id)) is None: raise NotFoundError("Recipient tenant not found")
    existing=await db.scalar(select(BusinessNetworkRequest).where(BusinessNetworkRequest.sender_tenant_id==sender_tenant_id,BusinessNetworkRequest.idempotency_key==idempotency_key))
    if existing is not None: return existing
    item=BusinessNetworkRequest(sender_tenant_id=sender_tenant_id,recipient_tenant_id=recipient_tenant_id,requester_user_id=requester_user_id,sponsor_user_id=sponsor_user_id,operation=operation,capability_contract=dict(capability_contract),payload=dict(payload),idempotency_key=idempotency_key,correlation_id=correlation_id or str(uuid.uuid4()))
    try:
        async with db.begin_nested():
            db.add(item)
            await db.flush()
    except IntegrityError as exc:
        constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if constraint_name != "uq_business_network_sender_idempotency":
            raise
        existing = await db.scalar(
            select(BusinessNetworkRequest).where(
                BusinessNetworkRequest.sender_tenant_id == sender_tenant_id,
                BusinessNetworkRequest.idempotency_key == idempotency_key,
            )
        )
        if existing is None:
            raise
        return existing
    await record(db,action="business_network.request.submitted",actor_id=requester_user_id,tenant_id=sender_tenant_id,resource_type="business_network_request",resource_id=item.id,metadata={"recipient_tenant_id":str(recipient_tenant_id),"operation":operation,"correlation_id":item.correlation_id})
    return item
async def decide_request(db:AsyncSession,*,sender_tenant_id:uuid.UUID,request_id:uuid.UUID,decider_user_id:uuid.UUID,approve:bool,reason:str|None=None):
    item=await db.scalar(select(BusinessNetworkRequest).where(BusinessNetworkRequest.id==request_id,BusinessNetworkRequest.sender_tenant_id==sender_tenant_id).with_for_update())
    if item is None: raise NotFoundError("Business Network request not found")
    if item.status!=BusinessNetworkRequestStatus.PENDING_APPROVAL: raise ConflictError("Business Network request is no longer pending approval")
    if decider_user_id in {item.requester_user_id,item.sponsor_user_id}: raise ValidationAppError("Decision maker must be independent from requester and sponsor")
    await assert_users_belong_to_tenant(db,tenant_id=sender_tenant_id,user_ids={decider_user_id},field_names={decider_user_id:"decider_user_id"})
    item.decision_by=decider_user_id; item.decision_reason=reason; item.decided_at=datetime.now(timezone.utc)
    item.status=BusinessNetworkRequestStatus.APPROVED if approve else BusinessNetworkRequestStatus.REJECTED
    await db.flush()
    await record(db,action="business_network.request.decided",actor_id=decider_user_id,tenant_id=sender_tenant_id,resource_type="business_network_request",resource_id=item.id,metadata={"approved":approve,"recipient_tenant_id":str(item.recipient_tenant_id),"correlation_id":item.correlation_id})
    return item
