from dataclasses import dataclass

@dataclass(frozen=True)
class EmployeeModuleManifest:
    slug: str = "sales"
    name: str = "Sales Employee"
    version: str = "1.0"
    entrypoint: str = "analyze_sales"
    isolation: str = "tenant-scoped"

MANIFEST = EmployeeModuleManifest()
