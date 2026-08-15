from uuid import UUID
from fastapi import APIRouter
from app.core.deps import CurrentContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.customer import CustomerResponse, CustomerUpdate
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("", response_model=APIResponse[list[CustomerResponse]])
async def list_customers(ctx: CurrentContext, db: DbSession, q: str | None = None):
    rows = await customer_service.list_customers(db, tenant_id=ctx.tenant_id, q=q)
    return APIResponse(success=True, data=[CustomerResponse.model_validate(x, from_attributes=True) for x in rows])

@router.get("/{customer_id}", response_model=APIResponse[CustomerResponse])
async def get_customer(customer_id: UUID, ctx: CurrentContext, db: DbSession):
    row = await customer_service.get_customer(db, tenant_id=ctx.tenant_id, customer_id=customer_id)
    return APIResponse(success=True, data=CustomerResponse.model_validate(row, from_attributes=True))

@router.patch("/{customer_id}", response_model=APIResponse[CustomerResponse])
async def update_customer(customer_id: UUID, payload: CustomerUpdate, ctx: CurrentContext, db: DbSession):
    row = await customer_service.update_customer(db, tenant_id=ctx.tenant_id, customer_id=customer_id, **payload.model_dump())
    return APIResponse(success=True, data=CustomerResponse.model_validate(row, from_attributes=True))
