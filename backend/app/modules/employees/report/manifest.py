from dataclasses import dataclass

@dataclass(frozen=True)
class EmployeeModuleManifest:
    slug: str = "report"
    name: str = "Report Employee"
    version: str = "1.0"
    entrypoint: str = "analyze_dataset"
    isolation: str = "tenant-scoped"

MANIFEST = EmployeeModuleManifest()
