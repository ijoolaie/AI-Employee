from dataclasses import dataclass

@dataclass(frozen=True)
class ModuleManifest:
    slug: str = "workflow"
    name: str = "Workflow & Automation"
    version: str = "1.0"
    capabilities: tuple[str, ...] = ('workflow', 'workflow-events', 'workflow-schedules', 'approvals')

MANIFEST = ModuleManifest()
