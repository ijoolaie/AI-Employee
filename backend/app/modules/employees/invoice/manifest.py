from dataclasses import dataclass

@dataclass(frozen=True)
class EmployeeModuleManifest:
    slug: str = "invoice"
    name: str = "Invoice Employee"
    version: str = "1.0"
    entrypoint: str = "analyze_invoice"
    isolation: str = "tenant-scoped"

MANIFEST = EmployeeModuleManifest()
