"""W21 governed company-to-company business-network API."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import TenantContext, require_permission
from app.schemas.business_network import BusinessNetworkRequestCreate,BusinessNetworkRequestDecision,BusinessNetworkRequestRead
from app.services.business_network_service import create_request,decide_request
router=APIRouter(prefix="/business-network",tags=["business-network"])
def _err(exc:Exception)->HTTPException:
    msg=str(exc); code=status.HTTP_404_NOT_FOUND if "not found" in msg.lower() else status.HTTP_422_UNPROCESSABLE_ENTITY if "must" in msg.lower() or "require" in msg.lower() else status.HTTP_409_CONFLICT
    return HTTPException(status_code=code,detail=msg)
@router.post("/requests",response_model=BusinessNetworkRequestRead,status_code=201)
async def submit(payload:BusinessNetworkRequestCreate,ctx:TenantContext=Depends(require_permission("business_network.submit")),db:AsyncSession=Depends(get_db,scope="function")):
    try:
        item=await create_request(db,sender_tenant_id=ctx.tenant_id,requester_user_id=ctx.user_id,sponsor_user_id=payload.sponsor_user_id,recipient_tenant_id=payload.recipient_tenant_id,operation=payload.operation,capability_contract=payload.capability_contract,payload=payload.payload,idempotency_key=payload.idempotency_key,correlation_id=payload.correlation_id)
        await db.commit(); return item
    except Exception as exc: await db.rollback(); raise _err(exc) from exc
@router.post("/requests/{request_id}/decision",response_model=BusinessNetworkRequestRead)
async def decide(request_id:UUID,payload:BusinessNetworkRequestDecision,ctx:TenantContext=Depends(require_permission("business_network.decide")),db:AsyncSession=Depends(get_db,scope="function")):
    try:
        item=await decide_request(db,sender_tenant_id=ctx.tenant_id,request_id=request_id,decider_user_id=ctx.user_id,approve=payload.approve,reason=payload.reason)
        await db.commit(); return item
    except Exception as exc: await db.rollback(); raise _err(exc) from exc
