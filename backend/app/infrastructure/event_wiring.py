from app.shared.events import InProcessEventBus
from app.shared.event_catalog import (
    ORDER_COMPLETED, INVOICE_ISSUED, PAYMENT_SUCCEEDED,
    CUSTOMER_CREATED, DOCUMENT_INGESTED,
)
from app.modules.workflow.events import handle as workflow_handler
from app.modules.knowledge.events import handle as knowledge_handler
from app.modules.crm.events import handle as crm_handler
from app.modules.billing.events import handle as billing_handler

def build_event_bus() -> InProcessEventBus:
    bus = InProcessEventBus()
    bus.subscribe(ORDER_COMPLETED, billing_handler)
    bus.subscribe(PAYMENT_SUCCEEDED, workflow_handler)
    bus.subscribe(CUSTOMER_CREATED, workflow_handler)
    bus.subscribe(DOCUMENT_INGESTED, workflow_handler)
    bus.subscribe(INVOICE_ISSUED, workflow_handler)
    return bus
