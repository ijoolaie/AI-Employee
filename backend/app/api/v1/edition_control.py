"""Vendor/reseller/customer runtime control-plane boundaries."""

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import DbSession
from app.core.edition_deps import CustomerAdminContext, ResellerAdminContext, VendorAdminContext
from app.models.tenant import Tenant
from app.models.support_escalation import SupportEscalation
from app.models.support_escalation_message import SupportEscalationMessage
from app.models.tenant_entitlement import TenantEntitlement
from app.schemas.common import APIResponse
from app.schemas.edition import (
    ChildTenantProvisionRequest,
    EntitlementDelegationRequest,
    EntitlementResponse,
    SupportEscalationRequest,
    SupportEscalationResponse,
    SupportEscalationStatusRequest,
    SupportEscalationMessageRequest,
    SupportEscalationMessageResponse,
    TenantSummary,
)
from app.services import edition_lifecycle_service, edition_service

router = APIRouter(prefix="/edition", tags=["edition-control"])


@router.get("/vendor/resellers", response_model=APIResponse[list[TenantSummary]])
async def list_resellers(ctx: VendorAdminContext, db: DbSession):
    rows = (await db.execute(select(Tenant).where(Tenant.parent_tenant_id == ctx.tenant_id, Tenant.tenant_kind == edition_service.EDITION_RESELLER).order_by(Tenant.created_at))).scalars().all()
    return APIResponse(success=True, data=rows)


@router.post("/vendor/resellers", response_model=APIResponse[TenantSummary], status_code=201)
async def create_reseller(payload: ChildTenantProvisionRequest, ctx: VendorAdminContext, db: DbSession):
    tenant, _ = await edition_service.provision_child_tenant(
        db,
        parent=ctx.tenant,
        name=payload.name,
        slug=payload.slug,
        admin_email=payload.admin_email,
        admin_password=payload.admin_password,
        full_name=payload.full_name,
        kind=edition_service.EDITION_RESELLER,
        vendor_release_tag=payload.vendor_release_tag,
        delivery_revision=payload.delivery_revision,
    )
    return APIResponse(success=True, data=tenant)


@router.post("/vendor/resellers/{reseller_id}/suspend", response_model=APIResponse[TenantSummary])
async def suspend_reseller(reseller_id: UUID, ctx: VendorAdminContext, db: DbSession):
    tenant = await edition_lifecycle_service.set_child_tenant_status(
        db,
        parent=ctx.tenant,
        child_id=reseller_id,
        expected_kind=edition_service.EDITION_RESELLER,
        target_status=edition_lifecycle_service.STATUS_SUSPENDED,
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=tenant)


@router.post("/vendor/resellers/{reseller_id}/resume", response_model=APIResponse[TenantSummary])
async def resume_reseller(reseller_id: UUID, ctx: VendorAdminContext, db: DbSession):
    tenant = await edition_lifecycle_service.set_child_tenant_status(
        db,
        parent=ctx.tenant,
        child_id=reseller_id,
        expected_kind=edition_service.EDITION_RESELLER,
        target_status=edition_lifecycle_service.STATUS_ACTIVE,
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=tenant)


@router.post("/vendor/resellers/{reseller_id}/deprovision", response_model=APIResponse[TenantSummary])
async def deprovision_reseller(reseller_id: UUID, ctx: VendorAdminContext, db: DbSession):
    tenant = await edition_lifecycle_service.set_child_tenant_status(
        db,
        parent=ctx.tenant,
        child_id=reseller_id,
        expected_kind=edition_service.EDITION_RESELLER,
        target_status=edition_lifecycle_service.STATUS_DEPROVISIONED,
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=tenant)


@router.get("/reseller/customers", response_model=APIResponse[list[TenantSummary]])
async def list_customers(ctx: ResellerAdminContext, db: DbSession):
    rows = (await db.execute(select(Tenant).where(Tenant.parent_tenant_id == ctx.tenant_id, Tenant.tenant_kind == edition_service.EDITION_CUSTOMER).order_by(Tenant.created_at))).scalars().all()
    return APIResponse(success=True, data=rows)


@router.post("/reseller/customers", response_model=APIResponse[TenantSummary], status_code=201)
async def create_customer(payload: ChildTenantProvisionRequest, ctx: ResellerAdminContext, db: DbSession):
    tenant, _ = await edition_service.provision_child_tenant(
        db,
        parent=ctx.tenant,
        name=payload.name,
        slug=payload.slug,
        admin_email=payload.admin_email,
        admin_password=payload.admin_password,
        full_name=payload.full_name,
        kind=edition_service.EDITION_CUSTOMER,
        vendor_release_tag=payload.vendor_release_tag,
        delivery_revision=payload.delivery_revision,
    )
    return APIResponse(success=True, data=tenant)


@router.post("/reseller/customers/{customer_id}/suspend", response_model=APIResponse[TenantSummary])
async def suspend_customer(customer_id: UUID, ctx: ResellerAdminContext, db: DbSession):
    tenant = await edition_lifecycle_service.set_child_tenant_status(
        db,
        parent=ctx.tenant,
        child_id=customer_id,
        expected_kind=edition_service.EDITION_CUSTOMER,
        target_status=edition_lifecycle_service.STATUS_SUSPENDED,
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=tenant)


@router.post("/reseller/customers/{customer_id}/resume", response_model=APIResponse[TenantSummary])
async def resume_customer(customer_id: UUID, ctx: ResellerAdminContext, db: DbSession):
    tenant = await edition_lifecycle_service.set_child_tenant_status(
        db,
        parent=ctx.tenant,
        child_id=customer_id,
        expected_kind=edition_service.EDITION_CUSTOMER,
        target_status=edition_lifecycle_service.STATUS_ACTIVE,
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=tenant)


@router.post("/reseller/customers/{customer_id}/deprovision", response_model=APIResponse[TenantSummary])
async def deprovision_customer(customer_id: UUID, ctx: ResellerAdminContext, db: DbSession):
    tenant = await edition_lifecycle_service.set_child_tenant_status(
        db,
        parent=ctx.tenant,
        child_id=customer_id,
        expected_kind=edition_service.EDITION_CUSTOMER,
        target_status=edition_lifecycle_service.STATUS_DEPROVISIONED,
        actor_id=ctx.user_id,
    )
    return APIResponse(success=True, data=tenant)


@router.post("/reseller/customers/{customer_id}/entitlements", response_model=APIResponse[EntitlementResponse])
async def delegate_customer_entitlement(customer_id: UUID, payload: EntitlementDelegationRequest, ctx: ResellerAdminContext, db: DbSession):
    child = (await db.execute(select(Tenant).where(Tenant.id == customer_id))).scalar_one_or_none()
    if child is None:
        raise HTTPException(status_code=404, detail="Customer tenant not found")
    edition_service.assert_direct_child(ctx.tenant, child, edition_service.EDITION_CUSTOMER)
    row = await edition_service.delegate_entitlement(db, parent=ctx.tenant, child=child, feature_code=payload.feature_code, quota_limit=payload.quota_limit)
    return APIResponse(success=True, data=row)


async def _list_incoming_support_escalations(db: DbSession, tenant_id: UUID):
    rows = await db.execute(
        select(SupportEscalation)
        .where(SupportEscalation.to_tenant_id == tenant_id)
        .order_by(SupportEscalation.created_at.desc())
        .limit(100)
    )
    return APIResponse(success=True, data=[
        SupportEscalationResponse.model_validate(row, from_attributes=True)
        for row in rows.scalars().all()
    ])


@router.get("/vendor/support/escalations", response_model=APIResponse[list[SupportEscalationResponse]])
async def list_vendor_support_escalations(ctx: VendorAdminContext, db: DbSession):
    """List only support escalations addressed to this vendor tenant."""
    return await _list_incoming_support_escalations(db, ctx.tenant_id)


@router.get("/reseller/support/escalations", response_model=APIResponse[list[SupportEscalationResponse]])
async def list_reseller_support_escalations(ctx: ResellerAdminContext, db: DbSession):
    """List only support escalations addressed to this reseller tenant."""
    return await _list_incoming_support_escalations(db, ctx.tenant_id)


async def _update_incoming_support_escalation(
    escalation_id: UUID,
    payload: SupportEscalationStatusRequest,
    ctx,
    db: DbSession,
):
    result = await db.execute(
        select(SupportEscalation).where(
            SupportEscalation.id == escalation_id,
            SupportEscalation.to_tenant_id == ctx.tenant_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Support escalation not found")
    allowed_transitions = {
        "open": {"in_progress", "resolved"},
        "in_progress": {"open", "resolved"},
        "resolved": {"open"},
    }
    if payload.status == row.status:
        return APIResponse(success=True, data=SupportEscalationResponse.model_validate(row, from_attributes=True))
    if payload.status not in allowed_transitions.get(row.status, set()):
        raise HTTPException(status_code=409, detail="Invalid support escalation status transition")
    previous_status = row.status
    row.status = payload.status
    await edition_service.record_audit(
        db,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        action="support.escalation.status_changed",
        resource_type="support_escalation",
        resource_id=str(row.id),
        metadata={"from_status": previous_status, "to_status": payload.status},
    )
    await db.refresh(row)
    return APIResponse(success=True, data=SupportEscalationResponse.model_validate(row, from_attributes=True))


@router.patch("/vendor/support/escalations/{escalation_id}/status", response_model=APIResponse[SupportEscalationResponse])
async def update_vendor_support_escalation_status(
    escalation_id: UUID,
    payload: SupportEscalationStatusRequest,
    ctx: VendorAdminContext,
    db: DbSession,
):
    """Change status only for escalations addressed to this vendor tenant."""
    return await _update_incoming_support_escalation(escalation_id, payload, ctx, db)


@router.patch("/reseller/support/escalations/{escalation_id}/status", response_model=APIResponse[SupportEscalationResponse])
async def update_reseller_support_escalation_status(
    escalation_id: UUID,
    payload: SupportEscalationStatusRequest,
    ctx: ResellerAdminContext,
    db: DbSession,
):
    """Change status only for escalations addressed to this reseller tenant."""
    return await _update_incoming_support_escalation(escalation_id, payload, ctx, db)


@router.post("/support/escalations", response_model=APIResponse[SupportEscalationResponse], status_code=201)
async def create_escalation(payload: SupportEscalationRequest, ctx: CustomerAdminContext, db: DbSession):
    row = await edition_service.create_support_escalation(
        db,
        from_tenant=ctx.tenant,
        opened_by=ctx.user_id,
        subject=payload.subject,
        description=payload.description,
    )
    return APIResponse(success=True, data=row)


@router.post("/reseller/support/escalations", response_model=APIResponse[SupportEscalationResponse], status_code=201)
async def create_reseller_escalation(payload: SupportEscalationRequest, ctx: ResellerAdminContext, db: DbSession):
    row = await edition_service.create_support_escalation(
        db,
        from_tenant=ctx.tenant,
        opened_by=ctx.user_id,
        subject=payload.subject,
        description=payload.description,
    )
    return APIResponse(success=True, data=row)


async def _get_participant_support_escalation(escalation_id: UUID, ctx, db: DbSession):
    result = await db.execute(
        select(SupportEscalation).where(
            SupportEscalation.id == escalation_id,
            (SupportEscalation.from_tenant_id == ctx.tenant_id)
            | (SupportEscalation.to_tenant_id == ctx.tenant_id),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Support escalation not found")
    return row


async def _list_support_escalation_messages(escalation_id: UUID, ctx, db: DbSession):
    await _get_participant_support_escalation(escalation_id, ctx, db)
    result = await db.execute(
        select(SupportEscalationMessage)
        .where(SupportEscalationMessage.escalation_id == escalation_id)
        .order_by(SupportEscalationMessage.created_at.desc())
        .limit(200)
    )
    rows = list(result.scalars().all())
    rows.reverse()
    return APIResponse(
        success=True,
        data=[SupportEscalationMessageResponse.model_validate(row, from_attributes=True) for row in rows],
    )


async def _create_support_escalation_message(
    escalation_id: UUID,
    payload: SupportEscalationMessageRequest,
    ctx,
    db: DbSession,
):
    ticket = await _get_participant_support_escalation(escalation_id, ctx, db)
    if ticket.status == "resolved":
        raise HTTPException(status_code=409, detail="Reopen the support escalation before replying")
    message = SupportEscalationMessage(
        id=uuid4(),
        escalation_id=ticket.id,
        author_tenant_id=ctx.tenant_id,
        author_user_id=ctx.user_id,
        body=payload.body.strip(),
    )
    if not message.body:
        raise HTTPException(status_code=422, detail="Message body must not be blank")
    db.add(message)
    await db.flush()
    await db.refresh(message)
    await edition_service.record_audit(
        db,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        action="support.escalation.message_created",
        resource_type="support_escalation_message",
        resource_id=str(message.id),
        metadata={"escalation_id": str(ticket.id)},
    )
    return APIResponse(
        success=True,
        data=SupportEscalationMessageResponse.model_validate(message, from_attributes=True),
    )


@router.get("/vendor/support/escalations/{escalation_id}/messages", response_model=APIResponse[list[SupportEscalationMessageResponse]])
async def list_vendor_support_escalation_messages(escalation_id: UUID, ctx: VendorAdminContext, db: DbSession):
    return await _list_support_escalation_messages(escalation_id, ctx, db)


@router.post("/vendor/support/escalations/{escalation_id}/messages", response_model=APIResponse[SupportEscalationMessageResponse], status_code=201)
async def create_vendor_support_escalation_message(escalation_id: UUID, payload: SupportEscalationMessageRequest, ctx: VendorAdminContext, db: DbSession):
    return await _create_support_escalation_message(escalation_id, payload, ctx, db)


@router.get("/reseller/support/escalations/{escalation_id}/messages", response_model=APIResponse[list[SupportEscalationMessageResponse]])
async def list_reseller_support_escalation_messages(escalation_id: UUID, ctx: ResellerAdminContext, db: DbSession):
    return await _list_support_escalation_messages(escalation_id, ctx, db)


@router.post("/reseller/support/escalations/{escalation_id}/messages", response_model=APIResponse[SupportEscalationMessageResponse], status_code=201)
async def create_reseller_support_escalation_message(escalation_id: UUID, payload: SupportEscalationMessageRequest, ctx: ResellerAdminContext, db: DbSession):
    return await _create_support_escalation_message(escalation_id, payload, ctx, db)


@router.get("/support/escalations/{escalation_id}/messages", response_model=APIResponse[list[SupportEscalationMessageResponse]])
async def list_customer_support_escalation_messages(escalation_id: UUID, ctx: CustomerAdminContext, db: DbSession):
    return await _list_support_escalation_messages(escalation_id, ctx, db)


@router.post("/support/escalations/{escalation_id}/messages", response_model=APIResponse[SupportEscalationMessageResponse], status_code=201)
async def create_customer_support_escalation_message(escalation_id: UUID, payload: SupportEscalationMessageRequest, ctx: CustomerAdminContext, db: DbSession):
    return await _create_support_escalation_message(escalation_id, payload, ctx, db)


@router.get("/customer/{customer_id}/entitlements", response_model=APIResponse[list[EntitlementResponse]])
async def list_customer_entitlements(customer_id: UUID, ctx: ResellerAdminContext, db: DbSession):
    child = (await db.execute(select(Tenant).where(Tenant.id == customer_id))).scalar_one_or_none()
    if child is None:
        raise HTTPException(status_code=404, detail="Customer tenant not found")
    edition_service.assert_direct_child(ctx.tenant, child, edition_service.EDITION_CUSTOMER)
    rows = (await db.execute(select(TenantEntitlement).where(TenantEntitlement.tenant_id == child.id).order_by(TenantEntitlement.feature_code))).scalars().all()
    return APIResponse(success=True, data=rows)
