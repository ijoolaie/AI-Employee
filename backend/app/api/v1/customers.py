from uuid import UUID
from fastapi import APIRouter
from app.core.deps import CustomerCreateContext, CustomerReadContext, CustomerUpdateContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])

@router.post("", response_model=APIResponse[CustomerResponse], status_code=201)
async def create_customer(payload: CustomerCreate, ctx: CustomerCreateContext, db: DbSession):
    row = await customer_service.create_customer(
        db,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user.id,
        external_key=payload.external_key,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        tags=payload.tags,
        notes=payload.notes,
    )
    return APIResponse(success=True, data=CustomerResponse.model_validate(row, from_attributes=True))

@router.get("", response_model=APIResponse[list[CustomerResponse]])
async def list_customers(ctx: CustomerReadContext, db: DbSession, q: str | None = None):
    rows = await customer_service.list_customers(db, tenant_id=ctx.tenant_id, q=q)
    return APIResponse(success=True, data=[CustomerResponse.model_validate(x, from_attributes=True) for x in rows])

@router.get("/{customer_id}", response_model=APIResponse[CustomerResponse])
async def get_customer(customer_id: UUID, ctx: CustomerReadContext, db: DbSession):
    row = await customer_service.get_customer(db, tenant_id=ctx.tenant_id, customer_id=customer_id)
    return APIResponse(success=True, data=CustomerResponse.model_validate(row, from_attributes=True))

@router.patch("/{customer_id}", response_model=APIResponse[CustomerResponse])
async def update_customer(customer_id: UUID, payload: CustomerUpdate, ctx: CustomerUpdateContext, db: DbSession):
    row = await customer_service.update_customer(db, tenant_id=ctx.tenant_id, customer_id=customer_id, actor_id=ctx.user.id, **payload.model_dump(exclude_unset=True))
    return APIResponse(success=True, data=CustomerResponse.model_validate(row, from_attributes=True))
