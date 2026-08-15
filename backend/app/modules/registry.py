from .billing.manifest import MANIFEST as BILLING
from .commerce.manifest import MANIFEST as COMMERCE
from .crm.manifest import MANIFEST as CRM
from .employees.document.manifest import MANIFEST as DOCUMENT
from .employees.invoice.manifest import MANIFEST as INVOICE
from .employees.order.manifest import MANIFEST as ORDER
from .employees.report.manifest import MANIFEST as REPORT
from .employees.sales.manifest import MANIFEST as SALES
from .knowledge.manifest import MANIFEST as KNOWLEDGE
from .workflow.manifest import MANIFEST as WORKFLOW

BUILTIN_MODULES = {
    m.slug: m for m in (
        BILLING, COMMERCE, CRM, DOCUMENT, INVOICE, ORDER,
        REPORT, SALES, KNOWLEDGE, WORKFLOW
    )
}
