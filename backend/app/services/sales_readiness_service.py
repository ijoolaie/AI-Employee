from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.models.employee import Employee, EmployeeVersion
from app.models.conversation import CustomerConversation, CustomerMessage
from app.models.run import Run
from app.models.business_order import BusinessOrder
from app.models.customer import Customer
from app.services import employee_service, audit_service

TEMPLATES = [
    {"code":"sales_assistant","name":"Sales Assistant","description":"Recommends products, checks inventory and guides customers to purchase.","allowed_tools":["search_products","get_product","check_inventory","create_order"],"rules":{"max_discount_percent":10,"require_approval_for":["create_order"],"forbidden_actions":["change_price","delete_customer"]},"prompt_template":"You are a helpful sales assistant. Recommend the best products based on customer needs and current inventory."},
    {"code":"support_agent","name":"Customer Support Agent","description":"Answers support questions and escalates complex cases to a human.","allowed_tools":["get_order","track_order"],"rules":{"require_human_for":["refund","complaint"],"forbidden_actions":["change_price"]},"prompt_template":"You are a calm customer support agent. Resolve routine issues and hand off sensitive cases to a human."},
    {"code":"order_assistant","name":"Order Assistant","description":"Handles order lookup and delivery status conversations.","allowed_tools":["get_order","track_order"],"rules":{"forbidden_actions":["cancel_order","refund"]},"prompt_template":"You help customers find order status and delivery information. Never invent order data."},
]

def list_templates():
    return TEMPLATES

async def create_from_template(db: AsyncSession, *, tenant_id: uuid.UUID, actor_id: uuid.UUID, code: str) -> Employee:
    template = next((x for x in TEMPLATES if x["code"] == code), None)
    if not template:
        raise NotFoundError("Employee template not found")
    slug = template["code"]
    existing = await db.execute(select(Employee).where(Employee.tenant_id==tenant_id, Employee.slug==slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{str(uuid.uuid4())[:8]}"
    return await employee_service.create_employee(db, tenant_id=tenant_id, slug=slug, name=template["name"], kind="custom", input_schema={}, output_schema={}, prompt_template=template["prompt_template"], allowed_tools=template["allowed_tools"], rules=template["rules"], actor_id=actor_id)

async def get_guardrails(db: AsyncSession, *, tenant_id: uuid.UUID, employee_id: uuid.UUID):
    employee = await employee_service.get_employee(db, employee_id=employee_id, tenant_id=tenant_id)
    version = await employee_service.get_current_version(db, employee_id=employee.id)
    return employee, version

async def update_guardrails(db: AsyncSession, *, tenant_id: uuid.UUID, employee_id: uuid.UUID, actor_id: uuid.UUID, rules: dict, allowed_tools: list[str] | None):
    employee, current = await get_guardrails(db, tenant_id=tenant_id, employee_id=employee_id)
    merged_rules = {**(current.rules or {}), **rules}
    return await employee_service.publish_new_version(db, employee_id=employee.id, tenant_id=tenant_id, input_schema=current.input_schema, output_schema=current.output_schema, prompt_template=current.prompt_template, allowed_tools=allowed_tools if allowed_tools is not None else current.allowed_tools, rules=merged_rules, actor_id=actor_id)

async def analytics(db: AsyncSession, *, tenant_id: uuid.UUID) -> dict:
    conversations = int((await db.execute(select(func.count(CustomerConversation.id)).where(CustomerConversation.tenant_id==tenant_id))).scalar_one() or 0)
    handoffs = int((await db.execute(select(func.count(CustomerConversation.id)).where(CustomerConversation.tenant_id==tenant_id, CustomerConversation.handoff_requested.is_(True)))).scalar_one() or 0)
    runs = int((await db.execute(select(func.count(Run.id)).where(Run.tenant_id==tenant_id))).scalar_one() or 0)
    successful = int((await db.execute(select(func.count(Run.id)).where(Run.tenant_id==tenant_id, Run.status=="success"))).scalar_one() or 0)
    orders = int((await db.execute(select(func.count(BusinessOrder.id)).where(BusinessOrder.tenant_id==tenant_id))).scalar_one() or 0)
    revenue = float((await db.execute(select(func.coalesce(func.sum(BusinessOrder.total),0)).where(BusinessOrder.tenant_id==tenant_id, BusinessOrder.status != "cancelled"))).scalar_one() or 0)
    influenced = int((await db.execute(select(func.count(BusinessOrder.id)).where(BusinessOrder.tenant_id==tenant_id, BusinessOrder.metadata_.contains({"source":"ai"})))).scalar_one() or 0)
    influenced_revenue = float((await db.execute(select(func.coalesce(func.sum(BusinessOrder.total),0)).where(BusinessOrder.tenant_id==tenant_id, BusinessOrder.status != "cancelled", BusinessOrder.metadata_.contains({"source":"ai"})))).scalar_one() or 0)
    ai_resolved = max(conversations - handoffs, 0)
    return {"conversations":conversations,"ai_resolved":ai_resolved,"human_handoffs":handoffs,"runs":runs,"successful_runs":successful,"orders":orders,"revenue":revenue,"influenced_orders":influenced,"influenced_revenue":influenced_revenue,"ai_resolution_rate":round(ai_resolved/conversations*100,2) if conversations else 0,"handoff_rate":round(handoffs/conversations*100,2) if conversations else 0}

async def export_customer(db: AsyncSession, *, tenant_id: uuid.UUID, customer_id: uuid.UUID):
    customer = (await db.execute(select(Customer).where(Customer.tenant_id==tenant_id, Customer.id==customer_id))).scalar_one_or_none()
    if not customer: raise NotFoundError("Customer not found")
    convs = list((await db.execute(select(CustomerConversation).where(CustomerConversation.tenant_id==tenant_id, CustomerConversation.customer_id==customer_id))).scalars().all())
    conv_ids=[c.id for c in convs]
    msgs = list((await db.execute(select(CustomerMessage).where(CustomerMessage.tenant_id==tenant_id, CustomerMessage.conversation_id.in_(conv_ids)))).scalars().all()) if conv_ids else []
    orders = list((await db.execute(select(BusinessOrder).where(BusinessOrder.tenant_id==tenant_id, BusinessOrder.metadata_.contains({"customer_id":str(customer_id)})))).scalars().all())
    return {"customer":{"id":str(customer.id),"external_key":customer.external_key,"name":customer.name,"email":customer.email,"phone":customer.phone,"tags":customer.tags,"notes":customer.notes},"conversations":[{"id":str(c.id),"status":c.status,"created_at":c.created_at.isoformat()} for c in convs],"messages":[{"id":str(m.id),"conversation_id":str(m.conversation_id),"role":m.role,"content":m.content,"created_at":m.created_at.isoformat()} for m in msgs],"orders":[{"id":str(o.id),"number":o.number,"status":o.status,"total":float(o.total),"currency":o.currency} for o in orders]}

async def delete_customer(db: AsyncSession, *, tenant_id: uuid.UUID, customer_id: uuid.UUID, actor_id: uuid.UUID):
    customer=(await db.execute(select(Customer).where(Customer.tenant_id==tenant_id, Customer.id==customer_id))).scalar_one_or_none()
    if not customer: raise NotFoundError("Customer not found")
    convs=list((await db.execute(select(CustomerConversation).where(CustomerConversation.tenant_id==tenant_id, CustomerConversation.customer_id==customer_id))).scalars().all())
    for c in convs:
        c.customer_id=None; c.customer_name="Deleted customer"; c.customer_email=None; c.customer_phone=None; c.customer_token_hash=f"deleted:{uuid.uuid4().hex}"
    customer.name="Deleted customer"; customer.email=None; customer.phone=None; customer.notes=None; customer.tags=[]; customer.external_key=f"deleted:{uuid.uuid4().hex}"; customer.is_active=False
    await audit_service.record(db, action="privacy.customer_deleted", actor_id=actor_id, tenant_id=tenant_id, resource_type="customer", resource_id=customer.id, metadata={"conversation_count":len(convs)})
    await db.flush()
    return {"deleted":True,"customer_id":str(customer_id)}
