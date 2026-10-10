"""World Mode catalogue and one-time commerce endpoints.

Manual approval is deliberately separate from activation. Provider callbacks
are not wired here, so a submitted reference is a claim awaiting vendor review.
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentContext, DbSession, has_permission
from app.models.employee import Employee
from app.models.world_commerce import (
    WorldCatalogueItem,
    WorldCommerceEvent,
    WorldFeatureEntitlement,
    WorldOrder,
    WorldRoomInventory,
)
from app.schemas.common import APIResponse
from app.schemas.world_commerce import (
    WorldCatalogueItemResponse,
    WorldCommerceEventResponse,
    WorldFeatureAccessResponse,
    WorldFeatureEntitlementResponse,
    WorldRoomInventoryAccessResponse,
    WorldRoomInventoryResponse,
    WorldRoomSceneConfig,
    WorldRoomSceneConfigResponse,
    WorldRoomSceneConfigUpdateRequest,
    WorldOrderCreateRequest,
    WorldOrderResponse,
    WorldPaymentDecision,
    WorldPaymentSubmission,
    WorldSupportDiagnosticsResponse,
    WorldSupportEntitlementSummary,
    WorldSupportOrderSummary,
)
from app.services import world_commerce_service as commerce

router = APIRouter(prefix="/world-commerce", tags=["world-commerce"])
VENDOR_INCLUDED_ITEM_TYPES = {"layout", "appearance", "personality", "support"}


async def _vendor_tenant_scope(ctx: CurrentContext, db: AsyncSession) -> set[UUID]:
    if ctx.user.is_platform_admin:
        rows = await db.scalars(select(WorldOrder.tenant_id).distinct())
        return set(rows.all())
    if ctx.tenant.tenant_kind != "vendor":
        raise HTTPException(status_code=403, detail="Vendor tenant required")
    if not await has_permission(ctx, "world.commerce.approve") and not await has_permission(ctx, "world.commerce.activate"):
        raise HTTPException(status_code=403, detail="Missing World commerce vendor permission")
    result = await db.execute(text("""
        WITH RECURSIVE descendants(id) AS (
            SELECT id FROM tenants WHERE id = :root_id
            UNION
            SELECT child.id FROM tenants AS child
            JOIN descendants AS parent ON child.parent_tenant_id = parent.id
        )
        SELECT id FROM descendants
    """), {"root_id": str(ctx.tenant_id)})
    return {UUID(str(row[0])) for row in result.all()}


@router.get("/catalogue", response_model=APIResponse[list[WorldCatalogueItemResponse]])
async def catalogue(ctx: CurrentContext, db: DbSession):
    rows = await db.scalars(
        select(WorldCatalogueItem).where(WorldCatalogueItem.is_active.is_(True))
        .order_by(WorldCatalogueItem.item_type, WorldCatalogueItem.code)
    )
    return APIResponse(success=True, data=[
        WorldCatalogueItemResponse.model_validate(row, from_attributes=True) for row in rows.all()
    ])


@router.get("/access/{item_code}", response_model=APIResponse[WorldFeatureAccessResponse])
async def feature_access(item_code: str, ctx: CurrentContext, db: DbSession):
    item = await db.scalar(select(WorldCatalogueItem).where(
        WorldCatalogueItem.code == item_code,
        WorldCatalogueItem.is_active.is_(True),
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="World catalogue item not found")
    # Vendor support access is role/tenant based, not a fabricated purchase.
    if item.is_free:
        data = WorldFeatureAccessResponse(
            item_code=item.code, granted=True, access_source="catalog_free",
            item_type=item.item_type,
        )
    elif ctx.tenant.tenant_kind == "vendor" and item.item_type in VENDOR_INCLUDED_ITEM_TYPES:
        data = WorldFeatureAccessResponse(
            item_code=item.code, granted=True, access_source="vendor_included",
            item_type=item.item_type,
        )
    else:
        entitlement = await db.scalar(select(WorldFeatureEntitlement).where(
            WorldFeatureEntitlement.tenant_id == ctx.tenant_id,
            WorldFeatureEntitlement.item_code == item.code,
            WorldFeatureEntitlement.status == "active",
            or_(
                and_(WorldFeatureEntitlement.item_type != "room", WorldFeatureEntitlement.expires_at.is_(None)),
                WorldFeatureEntitlement.expires_at > datetime.now(timezone.utc),
            ),
        ))
        data = WorldFeatureAccessResponse(
            item_code=item.code, granted=entitlement is not None,
            access_source="entitlement" if entitlement else "not_entitled",
            entitlement_id=entitlement.id if entitlement else None,
            item_type=item.item_type,
        )
    return APIResponse(success=True, data=data)


@router.get("/entitlements", response_model=APIResponse[list[WorldFeatureEntitlementResponse]])
async def my_entitlements(ctx: CurrentContext, db: DbSession):
    rows = await db.scalars(
        select(WorldFeatureEntitlement).where(
            WorldFeatureEntitlement.tenant_id == ctx.tenant_id,
            WorldFeatureEntitlement.status == "active",
            or_(
                and_(WorldFeatureEntitlement.item_type != "room", WorldFeatureEntitlement.expires_at.is_(None)),
                WorldFeatureEntitlement.expires_at > datetime.now(timezone.utc),
            ),
        ).order_by(WorldFeatureEntitlement.activated_at.desc())
    )
    return APIResponse(success=True, data=[
        WorldFeatureEntitlementResponse.model_validate(row, from_attributes=True) for row in rows.all()
    ])


@router.get("/room-inventory", response_model=APIResponse[list[WorldRoomInventoryResponse]])
async def my_room_inventory(ctx: CurrentContext, db: DbSession):
    """List only this tenant's provisioned rooms with currently valid leases."""
    now = datetime.now(timezone.utc)
    rows = await db.execute(
        select(WorldRoomInventory, WorldFeatureEntitlement).join(
            WorldFeatureEntitlement,
            WorldFeatureEntitlement.id == WorldRoomInventory.entitlement_id,
        ).join(
            WorldCatalogueItem,
            WorldCatalogueItem.code == WorldRoomInventory.item_code,
        ).where(
            WorldRoomInventory.tenant_id == ctx.tenant_id,
            WorldRoomInventory.status == "provisioned",
            WorldFeatureEntitlement.tenant_id == ctx.tenant_id,
            WorldFeatureEntitlement.status == "active",
            WorldFeatureEntitlement.item_type == "room",
            WorldFeatureEntitlement.expires_at.is_not(None),
            WorldFeatureEntitlement.expires_at > now,
            WorldCatalogueItem.item_type == "room",
            WorldCatalogueItem.is_active.is_(True),
        ).order_by(WorldRoomInventory.created_at.asc())
    )
    return APIResponse(success=True, data=[
        WorldRoomInventoryResponse(
            room_instance_id=inventory.id,
            item_code=inventory.item_code,
            status=inventory.status,
            expires_at=entitlement.expires_at,
            updated_at=inventory.updated_at,
            scene_config=inventory.scene_config,
        )
        for inventory, entitlement in rows.all()
    ])


@router.get(
    "/room-inventory/{item_code}/access",
    response_model=APIResponse[WorldRoomInventoryAccessResponse],
)
async def room_inventory_access(item_code: str, ctx: CurrentContext, db: DbSession):
    """Server-authoritative room access decision; never trusts client state."""
    item = await db.scalar(select(WorldCatalogueItem).where(
        WorldCatalogueItem.code == item_code,
        WorldCatalogueItem.item_type == "room",
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="World room not found")

    pair = await db.execute(
        select(WorldRoomInventory, WorldFeatureEntitlement).join(
            WorldFeatureEntitlement,
            WorldFeatureEntitlement.id == WorldRoomInventory.entitlement_id,
        ).where(
            WorldRoomInventory.tenant_id == ctx.tenant_id,
            WorldRoomInventory.item_code == item_code,
            WorldFeatureEntitlement.tenant_id == ctx.tenant_id,
        )
    )
    row = pair.first()
    if row is None:
        return APIResponse(success=True, data=WorldRoomInventoryAccessResponse(
            item_code=item_code, granted=False, reason="not_provisioned",
        ))

    inventory, entitlement = row
    now = datetime.now(timezone.utc)
    reason = "active"
    granted = True
    if not item.is_active:
        granted, reason = False, "catalogue_inactive"
    elif inventory.status != "provisioned":
        granted, reason = False, "inventory_suspended"
    elif entitlement.status != "active":
        granted, reason = False, "entitlement_inactive"
    elif entitlement.expires_at is None:
        granted, reason = False, "lease_unreconciled"
    elif entitlement.expires_at <= now:
        granted, reason = False, "lease_expired"

    return APIResponse(success=True, data=WorldRoomInventoryAccessResponse(
        item_code=item_code,
        granted=granted,
        reason=reason,
        room_instance_id=inventory.id,
        expires_at=entitlement.expires_at,
    ))




@router.put(
    "/room-inventory/{item_code}/scene-config",
    response_model=APIResponse[WorldRoomSceneConfigResponse],
)
async def update_room_scene_config(
    item_code: str,
    payload: WorldRoomSceneConfigUpdateRequest,
    ctx: CurrentContext,
    db: DbSession,
):
    """Persist a bounded room layout only while this tenant has a valid room lease."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(WorldRoomInventory, WorldFeatureEntitlement, WorldCatalogueItem)
        .join(
            WorldFeatureEntitlement,
            WorldFeatureEntitlement.id == WorldRoomInventory.entitlement_id,
        )
        .join(
            WorldCatalogueItem,
            WorldCatalogueItem.code == WorldRoomInventory.item_code,
        )
        .where(
            WorldRoomInventory.tenant_id == ctx.tenant_id,
            WorldRoomInventory.item_code == item_code,
            WorldFeatureEntitlement.tenant_id == ctx.tenant_id,
        )
        .with_for_update()
    )
    row = result.first()
    if row is None:
        # Do not disclose whether another tenant owns an inventory row.
        raise HTTPException(status_code=404, detail="World room not found")

    inventory, entitlement, catalogue_item = row
    if (
        catalogue_item.item_type != "room"
        or not catalogue_item.is_active
        or inventory.status != "provisioned"
        or entitlement.status != "active"
        or entitlement.expires_at is None
        or entitlement.expires_at <= now
    ):
        raise HTTPException(status_code=403, detail="Active room access is required to update the scene")

    if payload.expected_updated_at != inventory.updated_at:
        raise HTTPException(status_code=409, detail="Room layout changed since it was loaded; refresh before saving")

    scene_config = payload.scene_config
    employee_ids = {placement.employee_id for placement in scene_config.employee_placements}
    if employee_ids:
        active_employee_result = await db.scalars(
            select(Employee.id).where(
                Employee.tenant_id == ctx.tenant_id,
                Employee.is_active.is_(True),
                Employee.id.in_(employee_ids),
            )
        )
        active_employee_ids = set(active_employee_result.all())
        if active_employee_ids != employee_ids:
            # Never reveal whether an invalid ID belongs to another tenant.
            raise HTTPException(status_code=422, detail="Employee placements must reference active employees in this tenant")

    inventory.scene_config = scene_config.model_dump(mode="json")
    await db.flush()
    await db.commit()
    await db.refresh(inventory)
    return APIResponse(success=True, data=WorldRoomSceneConfigResponse(
        room_instance_id=inventory.id,
        item_code=inventory.item_code,
        scene_config=WorldRoomSceneConfig.model_validate(inventory.scene_config),
        updated_at=inventory.updated_at,
    ))

@router.post("/orders", response_model=APIResponse[WorldOrderResponse])
async def create_order(payload: WorldOrderCreateRequest, ctx: CurrentContext, db: DbSession):
    row = await commerce.create_order(
        db, tenant_id=ctx.tenant_id, buyer=ctx.user,
        item_code=payload.item_code, currency=payload.currency,
        payment_method=payload.payment_method, payment_provider=payload.payment_provider,
        idempotency_key=payload.idempotency_key,
    )
    await db.commit()
    await db.refresh(row)
    return APIResponse(success=True, data=WorldOrderResponse.model_validate(row, from_attributes=True))


@router.get("/orders", response_model=APIResponse[list[WorldOrderResponse]])
async def my_orders(ctx: CurrentContext, db: DbSession):
    rows = await db.scalars(
        select(WorldOrder).where(WorldOrder.tenant_id == ctx.tenant_id)
        .order_by(WorldOrder.created_at.desc()).limit(100)
    )
    return APIResponse(success=True, data=[
        WorldOrderResponse.model_validate(row, from_attributes=True) for row in rows.all()
    ])


@router.get("/orders/{order_id}/events", response_model=APIResponse[list[WorldCommerceEventResponse]])
async def order_events(order_id: UUID, ctx: CurrentContext, db: DbSession):
    order = await db.scalar(select(WorldOrder).where(WorldOrder.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="World order not found")
    if order.tenant_id != ctx.tenant_id:
        scopes = await _vendor_tenant_scope(ctx, db)
        if order.tenant_id not in scopes:
            raise HTTPException(status_code=404, detail="World order not found")
    events = await db.scalars(
        select(WorldCommerceEvent).where(
            WorldCommerceEvent.order_id == order_id,
            WorldCommerceEvent.tenant_id == order.tenant_id,
        ).order_by(WorldCommerceEvent.created_at.asc()).limit(500)
    )
    return APIResponse(success=True, data=[
        WorldCommerceEventResponse.model_validate(row, from_attributes=True) for row in events.all()
    ])


@router.post("/orders/{order_id}/payment-submission", response_model=APIResponse[WorldOrderResponse])
async def submit_payment(order_id: UUID, payload: WorldPaymentSubmission, ctx: CurrentContext, db: DbSession):
    row = await commerce.submit_payment(
        db, order_id=order_id, tenant_id=ctx.tenant_id, actor=ctx.user,
        provider_transaction_ref=payload.provider_transaction_ref,
    )
    await db.commit()
    await db.refresh(row)
    return APIResponse(success=True, data=WorldOrderResponse.model_validate(row, from_attributes=True))


@router.get(
    "/vendor/tenants/{tenant_id}/diagnostics",
    response_model=APIResponse[WorldSupportDiagnosticsResponse],
)
async def vendor_tenant_diagnostics(
    tenant_id: UUID,
    ctx: CurrentContext,
    db: DbSession,
):
    """Read-only, tenant-scoped diagnostics for vendor support staff."""
    if not ctx.user.is_platform_admin:
        if ctx.tenant.tenant_kind != "vendor":
            raise HTTPException(status_code=403, detail="Vendor tenant required")
        if not await has_permission(ctx, "world.support.view"):
            raise HTTPException(status_code=403, detail="Missing World support permission")
        scope_result = await db.execute(text("""
            WITH RECURSIVE descendants(id) AS (
                SELECT id FROM tenants WHERE id = :root_id
                UNION
                SELECT child.id FROM tenants AS child
                JOIN descendants AS parent ON child.parent_tenant_id = parent.id
            )
            SELECT id FROM descendants
        """), {"root_id": str(ctx.tenant_id)})
        allowed_tenants = {UUID(str(row[0])) for row in scope_result.all()}
        if tenant_id not in allowed_tenants:
            raise HTTPException(status_code=404, detail="Tenant not found")
    else:
        tenant_exists = await db.scalar(
            text("SELECT id FROM tenants WHERE id = :tenant_id"),
            {"tenant_id": str(tenant_id)},
        )
        if tenant_exists is None:
            raise HTTPException(status_code=404, detail="Tenant not found")

    count_rows = await db.execute(
        select(WorldOrder.status, func.count())
        .where(WorldOrder.tenant_id == tenant_id)
        .group_by(WorldOrder.status)
    )
    order_counts = {str(status): int(count) for status, count in count_rows.all()}
    active_entitlement_count = int(await db.scalar(
        select(func.count()).select_from(WorldFeatureEntitlement).where(
            WorldFeatureEntitlement.tenant_id == tenant_id,
            WorldFeatureEntitlement.status == "active",
            or_(
                and_(WorldFeatureEntitlement.item_type != "room", WorldFeatureEntitlement.expires_at.is_(None)),
                WorldFeatureEntitlement.expires_at > datetime.now(timezone.utc),
            ),
        )
    ) or 0)
    orders = await db.scalars(
        select(WorldOrder).where(WorldOrder.tenant_id == tenant_id)
        .order_by(WorldOrder.created_at.desc()).limit(20)
    )
    entitlements = await db.scalars(
        select(WorldFeatureEntitlement).where(
            WorldFeatureEntitlement.tenant_id == tenant_id
        ).order_by(WorldFeatureEntitlement.activated_at.desc()).limit(100)
    )
    diagnostics = WorldSupportDiagnosticsResponse(
        tenant_id=tenant_id,
        order_counts_by_status=order_counts,
        active_entitlement_count=active_entitlement_count,
        recent_orders=[
            WorldSupportOrderSummary.model_validate(row, from_attributes=True)
            for row in orders.all()
        ],
        entitlements=[
            WorldSupportEntitlementSummary.model_validate(row, from_attributes=True)
            for row in entitlements.all()
        ],
    )
    await commerce.record_support_diagnostics_view(
        db, tenant_id=tenant_id, actor=ctx.user,
        is_platform_admin=ctx.user.is_platform_admin,
    )
    await db.commit()
    return APIResponse(success=True, data=diagnostics)


@router.get("/vendor/orders", response_model=APIResponse[list[WorldOrderResponse]])
async def vendor_orders(
    ctx: CurrentContext,
    db: DbSession,
    status: str = Query(default="payment_submitted", pattern="^(payment_submitted|approved|rejected|fulfilled)$"),
):
    scopes = await _vendor_tenant_scope(ctx, db)
    if not ctx.user.is_platform_admin:
        required_permission = (
            "world.commerce.activate" if status == "approved"
            else "world.commerce.approve" if status in {"payment_submitted", "rejected"}
            else None
        )
        if required_permission and not await has_permission(ctx, required_permission):
            raise HTTPException(status_code=403, detail=f"Missing permission: {required_permission}")
    if not scopes:
        return APIResponse(success=True, data=[])
    rows = await db.scalars(
        select(WorldOrder).where(WorldOrder.tenant_id.in_(scopes), WorldOrder.status == status)
        .order_by(WorldOrder.created_at.asc()).limit(250)
    )
    return APIResponse(success=True, data=[
        WorldOrderResponse.model_validate(row, from_attributes=True) for row in rows.all()
    ])


async def _load_vendor_order(order_id: UUID, ctx: CurrentContext, db: AsyncSession) -> WorldOrder:
    scopes = await _vendor_tenant_scope(ctx, db)
    row = await db.scalar(select(WorldOrder).where(WorldOrder.id == order_id).with_for_update())
    if row is None or row.tenant_id not in scopes:
        raise HTTPException(status_code=404, detail="World order not found")
    return row


@router.post("/vendor/orders/{order_id}/approve", response_model=APIResponse[WorldOrderResponse])
async def approve_order(order_id: UUID, ctx: CurrentContext, db: DbSession):
    if not ctx.user.is_platform_admin and not await has_permission(ctx, "world.commerce.approve"):
        raise HTTPException(status_code=403, detail="Missing World commerce approval permission")
    order = await _load_vendor_order(order_id, ctx, db)
    row = await commerce.approve_payment(
        db, order_id=order.id, tenant_id=order.tenant_id, approver=ctx.user
    )
    await db.commit()
    await db.refresh(row)
    return APIResponse(success=True, data=WorldOrderResponse.model_validate(row, from_attributes=True))


@router.post("/vendor/orders/{order_id}/reject", response_model=APIResponse[WorldOrderResponse])
async def reject_order(order_id: UUID, payload: WorldPaymentDecision, ctx: CurrentContext, db: DbSession):
    if not ctx.user.is_platform_admin and not await has_permission(ctx, "world.commerce.approve"):
        raise HTTPException(status_code=403, detail="Missing World commerce approval permission")
    if not payload.reason:
        raise HTTPException(status_code=422, detail="A rejection reason is required")
    order = await _load_vendor_order(order_id, ctx, db)
    row = await commerce.reject_payment(
        db, order_id=order.id, tenant_id=order.tenant_id, approver=ctx.user, reason=payload.reason
    )
    await db.commit()
    await db.refresh(row)
    return APIResponse(success=True, data=WorldOrderResponse.model_validate(row, from_attributes=True))


@router.post("/vendor/orders/{order_id}/activate", response_model=APIResponse[WorldOrderResponse])
async def activate_order(order_id: UUID, ctx: CurrentContext, db: DbSession):
    if not ctx.user.is_platform_admin and not await has_permission(ctx, "world.commerce.activate"):
        raise HTTPException(status_code=403, detail="Missing World commerce activation permission")
    order = await _load_vendor_order(order_id, ctx, db)
    row = await commerce.mark_fulfilled(
        db, order_id=order.id, tenant_id=order.tenant_id, activator=ctx.user
    )
    await db.commit()
    await db.refresh(row)
    return APIResponse(success=True, data=WorldOrderResponse.model_validate(row, from_attributes=True))
