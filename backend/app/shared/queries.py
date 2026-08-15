from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ModuleQuery:
    module: str
    name: str
    payload: dict[str, Any]
