from uuid import UUID
from fastapi import APIRouter, Query
from app.core.deps import CurrentContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.product import ProductCreate, ProductInventoryUpdate, ProductResponse
from app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])

@router.get("", response_model=APIResponse[list[ProductResponse]])
async def list_products(ctx: CurrentContext, db: DbSession, q: str | None = Query(default=None), active_only: bool = False):
    rows = await product_service.list_products(db, ctx.tenant_id, q, active_only)
    return APIResponse(success=True, data=[ProductResponse.model_validate(x) for x in rows])

@router.post("", response_model=APIResponse[ProductResponse], status_code=201)
async def create_product(payload: ProductCreate, ctx: CurrentContext, db: DbSession):
    row = await product_service.create_product(db, ctx.tenant_id, payload.model_dump())
    return APIResponse(success=True, data=ProductResponse.model_validate(row))

@router.post("/{product_id}/inventory", response_model=APIResponse[ProductResponse])
async def update_inventory(product_id: UUID, payload: ProductInventoryUpdate, ctx: CurrentContext, db: DbSession):
    row = await product_service.update_inventory(db, ctx.tenant_id, product_id, payload.inventory)
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, "Product not found")
    return APIResponse(success=True, data=ProductResponse.model_validate(row))
