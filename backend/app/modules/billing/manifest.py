from dataclasses import dataclass

@dataclass(frozen=True)
class ModuleManifest:
    slug: str = "billing"
    name: str = "Billing & Entitlements"
    version: str = "1.0"
    capabilities: tuple[str, ...] = ('billing', 'usage')

MANIFEST = ModuleManifest()
