from dataclasses import dataclass

@dataclass(frozen=True)
class ModuleManifest:
    slug: str = "crm"
    name: str = "CRM & Customer Experience"
    version: str = "1.0"
    capabilities: tuple[str, ...] = ('customers', 'conversations', 'inbox')

MANIFEST = ModuleManifest()
