from dataclasses import dataclass

@dataclass(frozen=True)
class EmployeeModuleManifest:
    slug: str = "order"
    name: str = "Order Employee"
    version: str = "1.0"
    entrypoint: str = "analyze_order"
    isolation: str = "tenant-scoped"

MANIFEST = EmployeeModuleManifest()
