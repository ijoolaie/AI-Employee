from .document.manifest import MANIFEST as DOCUMENT
from .invoice.manifest import MANIFEST as INVOICE
from .order.manifest import MANIFEST as ORDER
from .report.manifest import MANIFEST as REPORT
from .sales.manifest import MANIFEST as SALES

BUILTIN_EMPLOYEE_MODULES = {
    item.slug: item for item in (REPORT, DOCUMENT, INVOICE, ORDER, SALES)
}
