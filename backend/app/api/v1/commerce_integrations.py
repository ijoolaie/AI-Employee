from uuid import UUID
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.core.config import get_settings
from app.core.deps import CurrentContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.commerce_integration import CommerceIntegrationCreate, CommerceIntegrationResponse
from app.services import commerce_integration_service, shopify_service
from app.models.commerce_integration import CommerceIntegration
from sqlalchemy import select

router = APIRouter(prefix="/commerce-integrations", tags=["commerce-integrations"])

@router.get("", response_model=APIResponse[list[CommerceIntegrationResponse]])
async def list_integrations(ctx: CurrentContext, db: DbSession):
    rows = await commerce_integration_service.list_integrations(db, ctx.tenant_id)
    return APIResponse(success=True, data=[CommerceIntegrationResponse.model_validate(commerce_integration_service.public_config(x)) for x in rows])

@router.post("", response_model=APIResponse[CommerceIntegrationResponse], status_code=201)
async def create_integration(payload: CommerceIntegrationCreate, ctx: CurrentContext, db: DbSession):
    row = await commerce_integration_service.create_integration(db, ctx.tenant_id, payload.provider, payload.name, payload.config)
    return APIResponse(success=True, data=CommerceIntegrationResponse.model_validate(commerce_integration_service.public_config(row)))

@router.get("/shopify/install")
async def shopify_install(shop: str, ctx: CurrentContext):
    settings = get_settings()
    if not settings.shopify_client_id or not settings.shopify_client_secret:
        raise HTTPException(status_code=503, detail="Shopify OAuth is not configured")
    state = shopify_service.make_state(ctx.tenant_id)
    return RedirectResponse(shopify_service.build_install_url(shop, state), status_code=302)

@router.get("/shopify/callback")
async def shopify_callback(shop: str, code: str, state: str, db: DbSession):
    tenant_id = shopify_service.parse_state(state)
    token = await shopify_service.exchange_code(shop, code)
    cfg = {"shop_domain": shop, "access_token": token.get("access_token"), "scope": token.get("scope"), "api_version": get_settings().shopify_api_version, "currency": "EUR", "oauth_installed": True}
    existing = (await db.execute(select(CommerceIntegration).where(CommerceIntegration.tenant_id==tenant_id, CommerceIntegration.provider=="shopify", CommerceIntegration.config["shop_domain"].as_string()==shop))).scalar_one_or_none()
    if existing:
        existing.config={**(existing.config or {}), **cfg}; existing.status="connected"; existing.is_active=True
        row=existing
    else:
        row=CommerceIntegration(tenant_id=tenant_id, provider="shopify", name=f"Shopify — {shop}", status="connected", config=cfg, is_active=True)
        db.add(row)
    await db.flush()
    try:
        await shopify_service.register_webhooks(row)
    except Exception as exc:
        row.config={**(row.config or {}), "webhook_registration_error": str(exc)[:500]}
    await db.commit()
    return RedirectResponse(f"{get_settings().frontend_app_url}/integrations?shopify=connected", status_code=302)

@router.post("/{integration_id}/test", response_model=APIResponse[dict])
async def test_integration(integration_id: UUID, ctx: CurrentContext, db: DbSession):
    result = await shopify_service.test_connection(db, ctx.tenant_id, integration_id); await db.commit()
    return APIResponse(success=True, data=result)

@router.post("/{integration_id}/sync/products", response_model=APIResponse[dict])
async def sync_products(integration_id: UUID, ctx: CurrentContext, db: DbSession):
    result = await shopify_service.sync_products(db, ctx.tenant_id, integration_id); await db.commit()
    return APIResponse(success=True, data=result)

@router.post("/{integration_id}/sync/orders", response_model=APIResponse[dict])
async def sync_orders(integration_id: UUID, ctx: CurrentContext, db: DbSession):
    result = await shopify_service.sync_orders(db, ctx.tenant_id, integration_id); await db.commit()
    return APIResponse(success=True, data=result)

@router.post("/{integration_id}/reconcile", response_model=APIResponse[dict])
async def reconcile(integration_id: UUID, ctx: CurrentContext, db: DbSession):
    result = await shopify_service.reconcile(db, ctx.tenant_id, integration_id); await db.commit()
    return APIResponse(success=True, data=result)

@router.post("/shopify/webhooks/{integration_id}")
async def shopify_webhook(integration_id: UUID, request: Request, db: DbSession, x_shopify_hmac_sha256: str | None = Header(default=None, alias="X-Shopify-Hmac-Sha256"), x_shopify_webhook_id: str | None = Header(default=None, alias="X-Shopify-Webhook-Id"), x_shopify_topic: str | None = Header(default=None, alias="X-Shopify-Topic")):
    body=await request.body()
    if not shopify_service.verify_webhook(body,x_shopify_hmac_sha256): raise HTTPException(status_code=401,detail="Invalid Shopify webhook signature")
    integration=(await db.execute(select(CommerceIntegration).where(CommerceIntegration.id==integration_id))).scalar_one_or_none()
    if not integration or integration.provider!="shopify": raise HTTPException(status_code=404,detail="Integration not found")
    payload=request.json if False else {}
    import json
    try: payload=json.loads(body.decode() or "{}")
    except Exception: payload={}
    webhook_id = x_shopify_webhook_id or "unknown"
    recorded = await shopify_service.record_webhook(db,integration,webhook_id,x_shopify_topic or "unknown",payload)
    if recorded:
        integration.config={**(integration.config or {}),"last_webhook_topic":x_shopify_topic,"last_webhook_id":webhook_id}
        await db.commit()
    return {"success":True,"duplicate":not recorded,"webhook_id":webhook_id}
