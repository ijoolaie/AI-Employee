from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.tool_registry import registry
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.employee import Employee, EmployeeVersion
from app.models.conversation import CustomerConversation, CustomerMessage
from app.models.run import Run
from app.models.business_order import BusinessOrder
from app.models.customer import Customer
from app.services import employee_service, audit_service

TEMPLATES = [
    {
        "code": "sales_assistant",
        "name": "Sales Assistant",
        "name_fa": "دستیار فروش",
        "description": "Recommends products, checks inventory and guides customers to purchase.",
        "description_fa": "محصول مناسب را پیشنهاد می‌دهد، موجودی را بررسی می‌کند و مشتری را تا خرید راهنمایی می‌کند.",
        "purpose": "Product discovery and assisted checkout for customer-facing sales conversations.",
        "purpose_fa": "کشف محصول و کمک به تکمیل خرید در گفتگوهای فروش با مشتری.",
        "category": "sales",
        "input_contract": "Customer need, product query, or purchase request.",
        "output_contract": "Product recommendations, availability, and an approved order request.",
        "dependencies": ["Product catalog", "Inventory"],
        "example": "A customer asks for a laptop under a target budget and wants to know whether it is in stock.",
        "example_fa": "مشتری لپ‌تاپی تا سقف بودجه مشخص می‌خواهد و می‌پرسد آیا موجود است یا نه.",
        "version": "1.0.0",
        "min_platform_version": "1.4.9",
        "allowed_tools": ["search_products", "get_product", "check_inventory", "create_order"],
        "rules": {"max_discount_percent": 10, "require_approval_for": ["create_order"], "forbidden_actions": ["change_price", "delete_customer"]},
        "prompt_template": "You are a helpful sales assistant. Recommend the best products based on customer needs and current inventory.",
    },
    {
        "code": "support_agent",
        "name": "Customer Support Agent",
        "name_fa": "کارشناس پشتیبانی مشتری",
        "description": "Answers support questions and escalates complex cases to a human.",
        "description_fa": "به پرسش‌های پشتیبانی پاسخ می‌دهد و موارد پیچیده را به نیروی انسانی ارجاع می‌دهد.",
        "purpose": "Resolve routine order and delivery questions while preserving a human handoff boundary.",
        "purpose_fa": "حل پرسش‌های معمول سفارش و ارسال با حفظ مرز ارجاع به نیروی انسانی.",
        "category": "support",
        "input_contract": "Customer question plus an order ID or order number when relevant.",
        "output_contract": "Verified order status, delivery information, or a human handoff.",
        "dependencies": ["Order data"],
        "example": "A customer asks where order #1042 is and when it is expected to arrive.",
        "example_fa": "مشتری می‌پرسد سفارش شماره ۱۰۴۲ کجاست و چه زمانی تحویل می‌شود.",
        "version": "1.0.0",
        "min_platform_version": "1.4.9",
        "allowed_tools": ["get_order", "track_order"],
        "rules": {"require_human_for": ["refund", "complaint"], "forbidden_actions": ["change_price"]},
        "prompt_template": "You are a calm customer support agent. Resolve routine issues and hand off sensitive cases to a human.",
    },
    {
        "code": "order_assistant",
        "name": "Order Assistant",
        "name_fa": "دستیار سفارش",
        "description": "Handles order lookup and delivery status conversations.",
        "description_fa": "گفتگوهای مربوط به پیگیری سفارش و وضعیت تحویل را مدیریت می‌کند.",
        "purpose": "Provide read-only order lookup and delivery tracking.",
        "purpose_fa": "ارائه اطلاعات خواندنی درباره سفارش و رهگیری تحویل.",
        "category": "orders",
        "input_contract": "Order ID or customer-visible order number.",
        "output_contract": "Current order status and requested delivery information.",
        "dependencies": ["Order data"],
        "example": "A customer sends an order number and asks for its current delivery status.",
        "example_fa": "مشتری شماره سفارش را می‌فرستد و وضعیت فعلی تحویل را می‌پرسد.",
        "version": "1.0.0",
        "min_platform_version": "1.4.9",
        "allowed_tools": ["get_order", "track_order"],
        "rules": {"forbidden_actions": ["cancel_order", "refund"]},
        "prompt_template": "You help customers find order status and delivery information. Never invent order data.",
    },
    {
        "code": "catalog_assistant",
        "name": "Catalog Assistant",
        "name_fa": "دستیار کاتالوگ",
        "description": "Answers product, pricing, category, and availability questions from the tenant catalog.",
        "description_fa": "به پرسش‌های محصول، قیمت، دسته‌بندی و موجودی بر اساس کاتالوگ تننت پاسخ می‌دهد.",
        "purpose": "Give sales and support teams a reliable product-information assistant without write access.",
        "purpose_fa": "ارائه اطلاعات قابل اتکای محصول برای فروش و پشتیبانی بدون دسترسی نوشتن.",
        "category": "commerce",
        "input_contract": "Product name, SKU, category, or availability question.",
        "output_contract": "Verified product attributes, price, and inventory status.",
        "dependencies": ["Product catalog", "Inventory"],
        "example": "A shopper asks whether a specific SKU is available and what its current price is.",
        "example_fa": "مشتری می‌پرسد یک SKU مشخص موجود است و قیمت فعلی آن چقدر است.",
        "version": "1.0.0",
        "min_platform_version": "1.4.9",
        "allowed_tools": ["search_products", "get_product", "check_inventory"],
        "rules": {"forbidden_actions": ["change_price", "create_order", "delete_customer"]},
        "prompt_template": "You are a product catalog assistant. Only use verified catalog data and never invent price or inventory.",
    },
    {
        "code": "report_analyst",
        "name": "Report Analyst",
        "name_fa": "تحلیلگر گزارش",
        "description": "Analyzes tenant CSV and Excel datasets and produces structured business reports.",
        "description_fa": "داده‌های CSV و Excel تننت را تحلیل کرده و گزارش کسب‌وکاری ساختاریافته تولید می‌کند.",
        "purpose": "Turn uploaded operational datasets into KPIs, summaries, trends, and downloadable reports.",
        "purpose_fa": "تبدیل داده‌های عملیاتی بارگذاری‌شده به KPI، خلاصه، روند و گزارش قابل دانلود.",
        "category": "analytics",
        "input_contract": "Tenant file ID for a CSV or Excel dataset.",
        "output_contract": "Validated dataset analysis plus generated report artifacts.",
        "dependencies": ["Uploaded CSV/Excel file"],
        "example": "An operations manager uploads monthly sales data and requests KPI and trend analysis.",
        "example_fa": "مدیر عملیات داده فروش ماهانه را بارگذاری کرده و تحلیل KPI و روند می‌خواهد.",
        "version": "1.0.0",
        "min_platform_version": "1.4.9",
        "allowed_tools": ["analyze_dataset"],
        "rules": {"forbidden_actions": ["modify_source_file", "send_external_message"]},
        "prompt_template": "You are a careful business report analyst. Analyze only the supplied tenant dataset and clearly separate observed results from assumptions.",
    },
    {
        "code": "document_analyst",
        "name": "Document Analyst",
        "name_fa": "تحلیلگر اسناد",
        "description": "Extracts structured information from tenant PDF, image, DOCX, and text documents.",
        "description_fa": "اطلاعات ساختاریافته را از اسناد PDF، تصویر، DOCX و متن تننت استخراج می‌کند.",
        "purpose": "Classify business documents and surface dates, amounts, contacts, and other detected fields.",
        "purpose_fa": "دسته‌بندی اسناد کسب‌وکار و استخراج تاریخ، مبالغ، اطلاعات تماس و سایر فیلدهای شناسایی‌شده.",
        "category": "documents",
        "input_contract": "Tenant file ID for a supported document.",
        "output_contract": "Extracted text, document classification, and detected field candidates.",
        "dependencies": ["Uploaded document"],
        "example": "A user uploads a scanned contract and asks for its key dates and monetary amounts.",
        "example_fa": "کاربر یک قرارداد اسکن‌شده را بارگذاری می‌کند و تاریخ‌های مهم و مبالغ آن را می‌خواهد.",
        "version": "1.0.0",
        "min_platform_version": "1.4.9",
        "allowed_tools": ["analyze_document"],
        "rules": {"forbidden_actions": ["alter_source_document", "send_external_message"]},
        "prompt_template": "You are a document analysis assistant. Extract only evidence present in the supplied document and flag uncertain fields.",
    },
    {
        "code": "finance_assistant",
        "name": "Finance Assistant",
        "name_fa": "دستیار مالی",
        "description": "Creates, reviews, summarizes, and exports tenant invoices within the controlled finance tool boundary.",
        "description_fa": "فاکتورهای تننت را در محدوده ابزار مالی کنترل‌شده ایجاد، بررسی، خلاصه و صادر می‌کند.",
        "purpose": "Support routine invoice operations while keeping financial actions tenant-scoped and auditable.",
        "purpose_fa": "پشتیبانی از عملیات معمول فاکتور با حفظ محدوده تننت و قابلیت حسابرسی.",
        "category": "finance",
        "input_contract": "Customer and line-item data, invoice ID, or a finance-summary request.",
        "output_contract": "Invoice result, status update, PDF artifact, or tenant financial summary.",
        "dependencies": ["Customer/order context", "Invoice data"],
        "example": "A finance user creates an invoice from line items and then exports its PDF.",
        "example_fa": "کاربر مالی از روی اقلام سفارش یک فاکتور ایجاد کرده و سپس PDF آن را صادر می‌کند.",
        "version": "1.0.0",
        "min_platform_version": "1.4.9",
        "allowed_tools": ["create_invoice", "update_invoice_status", "export_invoice_pdf", "invoice_financial_summary"],
        "rules": {"require_approval_for": ["update_invoice_status"], "forbidden_actions": ["delete_invoice", "change_account_owner"]},
        "prompt_template": "You are a finance operations assistant. Keep all calculations and invoice actions grounded in tenant data and preserve an auditable workflow.",
    },
]

def list_templates():
    return TEMPLATES

def _validate_template_tools(template: dict) -> None:
    """Fail closed when a template references a tool absent from the registry."""
    unknown = [name for name in template.get("allowed_tools", []) if not _tool_is_registered(name)]
    if unknown:
        raise ValidationAppError(
            "Employee template references unregistered tools",
            details={"template": template.get("code"), "unknown_tools": sorted(unknown)},
        )

def _tool_is_registered(name: str) -> bool:
    try:
        registry.get(name)
    except ValidationAppError:
        return False
    return True

async def create_from_template(db: AsyncSession, *, tenant_id: uuid.UUID, actor_id: uuid.UUID, code: str) -> Employee:
    template = next((x for x in TEMPLATES if x["code"] == code), None)
    if not template:
        raise NotFoundError("Employee template not found")
    _validate_template_tools(template)
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
    effective_tools = allowed_tools if allowed_tools is not None else current.allowed_tools
    for name in effective_tools or []:
        if not _tool_is_registered(name):
            raise ValidationAppError("Employee guardrails reference an unregistered tool", details={"tool": name})
    merged_rules = {**(current.rules or {}), **rules}
    return await employee_service.publish_new_version(db, employee_id=employee.id, tenant_id=tenant_id, input_schema=current.input_schema, output_schema=current.output_schema, prompt_template=current.prompt_template, allowed_tools=effective_tools, rules=merged_rules, actor_id=actor_id)

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
