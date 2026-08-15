"""Tenant administration: users and roles, strictly tenant-scoped."""
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.deps import CurrentContext, DbSession
from app.models.user import User
from app.models.role import Role
from app.schemas.common import APIResponse

router = APIRouter(prefix="/tenant-admin", tags=["tenant-admin"])

class UserSummary(BaseModel):
    id: UUID; email: str; full_name: str | None; is_active: bool; roles: list[str]
class RoleSummary(BaseModel):
    id: UUID; name: str; description: str | None; permissions: list[str]
class UserStatusUpdate(BaseModel):
    is_active: bool
class UserRolesUpdate(BaseModel):
    role_ids: list[UUID] = Field(default_factory=list)

async def require_tenant_admin(ctx: CurrentContext):
    if not ctx.user.is_superuser and not any(r.name.lower() in {"admin", "owner", "tenant_admin"} and r.tenant_id == ctx.tenant_id for r in ctx.user.roles):
        raise HTTPException(status_code=403, detail="Tenant administrator access required")
    return ctx

@router.get("/users", response_model=APIResponse[list[UserSummary]])
async def list_users(ctx: CurrentContext, db: DbSession):
    await require_tenant_admin(ctx)
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.tenant_id == ctx.tenant_id).order_by(User.created_at))
    rows = result.scalars().all()
    return APIResponse(success=True, data=[UserSummary(id=u.id,email=u.email,full_name=u.full_name,is_active=u.is_active,roles=[r.name for r in u.roles if r.tenant_id == ctx.tenant_id]) for u in rows])

@router.get("/roles", response_model=APIResponse[list[RoleSummary]])
async def list_roles(ctx: CurrentContext, db: DbSession):
    await require_tenant_admin(ctx)
    result = await db.execute(select(Role).options(selectinload(Role.permissions)).where((Role.tenant_id == ctx.tenant_id) | (Role.tenant_id.is_(None))).order_by(Role.name))
    rows = result.scalars().all()
    return APIResponse(success=True, data=[RoleSummary(id=r.id,name=r.name,description=r.description,permissions=[p.code for p in r.permissions]) for r in rows])

@router.post("/users/{user_id}/status", response_model=APIResponse[UserSummary])
async def update_user_status(user_id: UUID, payload: UserStatusUpdate, ctx: CurrentContext, db: DbSession):
    await require_tenant_admin(ctx)
    if user_id == ctx.user_id and not payload.is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id, User.tenant_id == ctx.tenant_id))
    user = result.scalar_one_or_none()
    if user is None: raise HTTPException(status_code=404, detail="User not found")
    user.is_active = payload.is_active
    await db.commit(); await db.refresh(user)
    return APIResponse(success=True, data=UserSummary(id=user.id,email=user.email,full_name=user.full_name,is_active=user.is_active,roles=[r.name for r in user.roles if r.tenant_id == ctx.tenant_id]))

@router.post("/users/{user_id}/roles", response_model=APIResponse[UserSummary])
async def update_user_roles(user_id: UUID, payload: UserRolesUpdate, ctx: CurrentContext, db: DbSession):
    await require_tenant_admin(ctx)
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id, User.tenant_id == ctx.tenant_id))
    user = result.scalar_one_or_none()
    if user is None: raise HTTPException(status_code=404, detail="User not found")
    roles_result = await db.execute(select(Role).where(Role.id.in_(payload.role_ids), ((Role.tenant_id == ctx.tenant_id) | (Role.tenant_id.is_(None)))))
    roles = roles_result.scalars().all()
    if len(roles) != len(set(payload.role_ids)): raise HTTPException(status_code=400, detail="One or more roles are invalid for this tenant")
    user.roles = roles
    await db.commit(); await db.refresh(user)
    return APIResponse(success=True, data=UserSummary(id=user.id,email=user.email,full_name=user.full_name,is_active=user.is_active,roles=[r.name for r in user.roles if r.tenant_id == ctx.tenant_id]))
