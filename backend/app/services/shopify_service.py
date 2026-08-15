"""Production-oriented Shopify GraphQL connector.

Uses Shopify Admin GraphQL (required for new public apps), OAuth for merchant
installation, HMAC-verified webhooks, cursor pagination, and reconciliation.
Webhooks are treated as change signals; reconciliation remains the source of
truth because Shopify does not guarantee delivery/order.
"""
from __future__ import annotations
import base64, hashlib, hmac, secrets, uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.models.commerce_integration import CommerceIntegration
from app.models.customer import Customer
from app.models.product import Product
from app.models.business_order import BusinessOrder
from app.models.shopify_webhook_event import ShopifyWebhookEvent


def _cfg(integration: CommerceIntegration):
    cfg = integration.config or {}
    shop = str(cfg.get("shop_domain") or "").strip().replace("https://", "").rstrip("/")
    token = str(cfg.get("access_token") or "").strip()
    version = str(cfg.get("api_version") or get_settings().shopify_api_version).strip()
    if not shop or not token:
        raise ValidationAppError("Shopify requires an installed shop and access token")
    return shop, token, version

async def _graphql(integration: CommerceIntegration, query: str, variables: dict[str, Any] | None = None):
    shop, token, version = _cfg(integration)
    url = f"https://{shop}/admin/api/{version}/graphql.json"
    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.post(url, json={"query": query, "variables": variables or {}}, headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"})
    if r.status_code >= 400:
        raise ValidationAppError("Shopify GraphQL request failed", details={"status": r.status_code, "body": r.text[:500]})
    body = r.json()
    if body.get("errors"):
        raise ValidationAppError("Shopify GraphQL returned errors", details={"errors": body["errors"][:3]})
    return body.get("data") or {}

async def get_integration(db, tenant_id, integration_id):
    row = (await db.execute(select(CommerceIntegration).where(CommerceIntegration.id == integration_id, CommerceIntegration.tenant_id == tenant_id))).scalar_one_or_none()
    if not row or row.provider != "shopify":
        raise ValidationAppError("Shopify integration not found")
    return row

async def test_connection(db, tenant_id, integration_id):
    integration = await get_integration(db, tenant_id, integration_id)
    data = await _graphql(integration, "query { shop { id name myshopifyDomain primaryDomain { url } } }")
    shop = data.get("shop") or {}
    integration.status = "connected"; integration.is_active = True
    integration.config = {**(integration.config or {}), "shop_id": shop.get("id"), "shop_name": shop.get("name"), "shop_domain": shop.get("myshopifyDomain") or integration.config.get("shop_domain")}
    await db.flush()
    return {"connected": True, "shop": {"id": shop.get("id"), "name": shop.get("name"), "domain": shop.get("myshopifyDomain")}}

async def _paginate(integration, query, root, variables=None, page_size=100, max_pages=50):
    variables = dict(variables or {}); variables["first"] = page_size; variables["after"] = None
    items=[]
    for _ in range(max_pages):
        data=await _graphql(integration, query, variables); conn=data[root]; items.extend(conn.get("nodes") or [])
        if not (conn.get("pageInfo") or {}).get("hasNextPage"): break
        variables["after"]=(conn.get("pageInfo") or {}).get("endCursor")
    return items

PRODUCTS_Q='''query Products($first:Int!,$after:String){ products(first:$first,after:$after){ nodes { id title descriptionHtml productType status variants(first:100){ nodes { id sku price inventoryQuantity } } images(first:20){ nodes { url } } } pageInfo { hasNextPage endCursor } } }'''
ORDERS_Q='''query Orders($first:Int!,$after:String){ orders(first:$first,after:$after,query:"status:any"){ nodes { id name createdAt currencyCode subtotalPriceSet { shopMoney { amount } } totalTaxSet { shopMoney { amount } } totalPriceSet { shopMoney { amount } } cancelledAt displayFulfillmentStatus customer { id firstName lastName email phone } lineItems(first:100){ nodes { title quantity sku originalUnitPriceSet { shopMoney { amount } } } } } pageInfo { hasNextPage endCursor } } }'''
CUSTOMERS_Q='''query Customers($first:Int!,$after:String){ customers(first:$first,after:$after){ nodes { id firstName lastName email phone } pageInfo { hasNextPage endCursor } } }'''

async def sync_products(db, tenant_id, integration_id):
    integration=await get_integration(db,tenant_id,integration_id); products=await _paginate(integration,PRODUCTS_Q,"products")
    created=updated=0
    for remote in products:
        variants=(remote.get("variants") or {}).get("nodes") or []; variant=variants[0] if variants else {}
        existing=(await db.execute(select(Product).where(Product.tenant_id==tenant_id, Product.attributes["shopify_product_id"].as_string()==str(remote.get("id"))))).scalar_one_or_none()
        data={"sku":variant.get("sku") or f"shopify:{remote.get('id')}","name":remote.get("title") or "Untitled product","description":remote.get("descriptionHtml"),"category":remote.get("productType"),"price":Decimal(str(variant.get("price") or "0")),"currency":(integration.config or {}).get("currency","EUR"),"inventory":int(variant.get("inventoryQuantity") or 0),"attributes":{"shopify_product_id":remote.get("id"),"shopify_variant_id":variant.get("id"),"source":"shopify"},"images":[x.get("url") for x in ((remote.get("images") or {}).get("nodes") or []) if x.get("url")],"is_active":remote.get("status")=="ACTIVE","source":"shopify"}
        if existing:
            for k,v in data.items(): setattr(existing,k,v)
            updated+=1
        else: db.add(Product(tenant_id=tenant_id,**data)); created+=1
    integration.status="synced"; integration.config={**(integration.config or {}),"last_product_sync_count":len(products)}; await db.flush()
    return {"provider":"shopify","products_seen":len(products),"created":created,"updated":updated}

async def sync_customers(db, tenant_id, integration_id):
    integration=await get_integration(db,tenant_id,integration_id); rows=await _paginate(integration,CUSTOMERS_Q,"customers"); created=0; updated=0
    for c in rows:
        key=str(c.get("id")); row=(await db.execute(select(Customer).where(Customer.tenant_id==tenant_id,Customer.external_key==key))).scalar_one_or_none(); name=" ".join(filter(None,[c.get("firstName"),c.get("lastName")])) or None
        if row: row.name=name; row.email=c.get("email"); row.phone=c.get("phone"); row.last_channel="shopify"; updated+=1
        else: db.add(Customer(tenant_id=tenant_id,external_key=key,name=name,email=c.get("email"),phone=c.get("phone"),last_channel="shopify")); created+=1
    await db.flush(); return {"customers_seen":len(rows),"created":created,"updated":updated}

async def sync_orders(db, tenant_id, integration_id):
    integration=await get_integration(db,tenant_id,integration_id); orders=await _paginate(integration,ORDERS_Q,"orders"); created=updated=0
    for remote in orders:
        rid=str(remote.get("id")); existing=(await db.execute(select(BusinessOrder).where(BusinessOrder.tenant_id==tenant_id,BusinessOrder.metadata_["shopify_order_id"].as_string()==rid))).scalar_one_or_none()
        c=remote.get("customer") or {}; key=str(c.get("id") or f"shopify-order:{rid}"); customer=(await db.execute(select(Customer).where(Customer.tenant_id==tenant_id,Customer.external_key==key))).scalar_one_or_none()
        if not customer:
            customer=Customer(tenant_id=tenant_id,external_key=key,name=" ".join(filter(None,[c.get("firstName"),c.get("lastName")])) or None,email=c.get("email"),phone=c.get("phone"),last_channel="shopify"); db.add(customer); await db.flush()
        lines=[]
        for item in ((remote.get("lineItems") or {}).get("nodes") or []):
            lines.append({"description":item.get("title") or "Item","quantity":item.get("quantity") or 1,"unit_price":float((((item.get("originalUnitPriceSet") or {}).get("shopMoney") or {}).get("amount") or 0)),"sku":item.get("sku")})
        status="cancelled" if remote.get("cancelledAt") else ("delivered" if remote.get("displayFulfillmentStatus")=="FULFILLED" else "processing")
        def money(name): return Decimal(str((((remote.get(name) or {}).get("shopMoney") or {}).get("amount") or "0")))
        data={"number":remote.get("name") or f"SHOPIFY-{rid}","status":status,"currency":remote.get("currencyCode") or "EUR","customer_name":customer.name or "Shopify customer","customer_email":customer.email,"order_date":date.fromisoformat(str(remote.get("createdAt"))[:10]),"line_items":lines,"subtotal":money("subtotalPriceSet"),"tax_amount":money("totalTaxSet"),"total":money("totalPriceSet"),"tax_rate":Decimal("0"),"metadata_":{"shopify_order_id":rid,"shopify":True,"customer_id":str(customer.id)}}
        if existing:
            for k,v in data.items(): setattr(existing,k,v)
            updated+=1
        else: db.add(BusinessOrder(tenant_id=tenant_id,**data)); created+=1
    integration.status="synced"; integration.config={**(integration.config or {}),"last_order_sync_count":len(orders)}; await db.flush()
    return {"provider":"shopify","orders_seen":len(orders),"created":created,"updated":updated}

async def reconcile(db, tenant_id, integration_id):
    p=await sync_products(db,tenant_id,integration_id); c=await sync_customers(db,tenant_id,integration_id); o=await sync_orders(db,tenant_id,integration_id)
    return {"products":p,"customers":c,"orders":o}

def build_install_url(shop: str, state: str) -> str:
    settings=get_settings(); shop=shop.strip().replace("https://","").rstrip("/")
    params={"client_id":settings.shopify_client_id,"scope":settings.shopify_scopes,"redirect_uri":settings.shopify_redirect_uri,"state":state}
    return f"https://{shop}/admin/oauth/authorize?{urlencode(params)}"

def make_state(tenant_id: uuid.UUID) -> str:
    settings=get_settings(); raw=f"{tenant_id}:{int(datetime.now(timezone.utc).timestamp())}:{secrets.token_urlsafe(12)}"; sig=hmac.new(settings.secret_key.encode(),raw.encode(),hashlib.sha256).hexdigest(); return base64.urlsafe_b64encode(f"{raw}:{sig}".encode()).decode()

def parse_state(state: str) -> uuid.UUID:
    settings=get_settings()
    try:
        raw=base64.urlsafe_b64decode(state.encode()).decode()
        tenant,ts,nonce,sig=raw.rsplit(":",3)
        if abs(int(datetime.now(timezone.utc).timestamp())-int(ts)) > 600:
            raise ValidationAppError("Expired Shopify OAuth state")
        signed=f"{tenant}:{ts}:{nonce}"
        expected=hmac.new(settings.secret_key.encode(),signed.encode(),hashlib.sha256).hexdigest()
    except ValidationAppError:
        raise
    except Exception as exc:
        raise ValidationAppError("Invalid Shopify OAuth state") from exc
    if not hmac.compare_digest(sig,expected): raise ValidationAppError("Invalid Shopify OAuth state")
    return uuid.UUID(tenant)

async def exchange_code(shop: str, code: str):
    settings=get_settings()
    if not settings.shopify_client_id or not settings.shopify_client_secret: raise ValidationAppError("Shopify OAuth is not configured")
    async with httpx.AsyncClient(timeout=30) as client:
        r=await client.post(f"https://{shop}/admin/oauth/access_token",json={"client_id":settings.shopify_client_id,"client_secret":settings.shopify_client_secret,"code":code})
    if r.status_code>=400: raise ValidationAppError("Shopify OAuth token exchange failed",details={"status":r.status_code,"body":r.text[:500]})
    return r.json()

async def register_webhooks(integration: CommerceIntegration):
    settings=get_settings()
    callback=f"{settings.shopify_redirect_uri.split('/api/v1/commerce-integrations/shopify/callback')[0]}/api/v1/commerce-integrations/shopify/webhooks/{integration.id}"
    mutation="""mutation CreateWebhook($topic: WebhookSubscriptionTopic!, $callbackUrl: URL!) { webhookSubscriptionCreate(topic: $topic, webhookSubscription: {callbackUrl: $callbackUrl, format: JSON}) { webhookSubscription { id topic } userErrors { field message } } }"""
    topics=["PRODUCTS_CREATE","PRODUCTS_UPDATE","PRODUCTS_DELETE","ORDERS_CREATE","ORDERS_UPDATED","CUSTOMERS_CREATE","CUSTOMERS_UPDATE","INVENTORY_LEVELS_UPDATE"]
    results=[]
    for topic in topics:
        try:
            data=await _graphql(integration,mutation,{"topic":topic,"callbackUrl":callback})
            results.append(data.get("webhookSubscriptionCreate") or {})
        except Exception as exc:
            results.append({"topic":topic,"error":str(exc)})
    integration.config={**(integration.config or {}),"webhook_callback":callback,"webhooks_registered":results}
    return results

def verify_webhook(raw_body: bytes, hmac_header: str | None) -> bool:
    secret=get_settings().shopify_client_secret
    if not secret or not hmac_header: return False
    digest=base64.b64encode(hmac.new(secret.encode(),raw_body,hashlib.sha256).digest()).decode()
    return hmac.compare_digest(digest,hmac_header)

async def record_webhook(db, integration, webhook_id, topic, payload):
    existing=(await db.execute(select(ShopifyWebhookEvent).where(ShopifyWebhookEvent.integration_id==integration.id,ShopifyWebhookEvent.webhook_id==webhook_id))).scalar_one_or_none()
    if existing: return False
    db.add(ShopifyWebhookEvent(tenant_id=integration.tenant_id,integration_id=integration.id,webhook_id=webhook_id,topic=topic,payload=payload,status="received")); await db.flush(); return True
