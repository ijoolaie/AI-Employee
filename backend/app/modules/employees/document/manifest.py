from dataclasses import dataclass

@dataclass(frozen=True)
class EmployeeModuleManifest:
    slug: str = "document"
    name: str = "Document Employee"
    version: str = "1.0"
    entrypoint: str = "analyze_document"
    isolation: str = "tenant-scoped"

MANIFEST = EmployeeModuleManifest()
