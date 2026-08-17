from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "app"
FRONTEND = ROOT / "frontend" / "src"
POLICY = ROOT / "architecture" / "module-boundaries.json"

policy = json.loads(POLICY.read_text(encoding="utf-8"))
contexts = set(policy["backend_contexts"])
errors: list[str] = []


def imports(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        errors.append(f"Syntax error in {path}: {exc}")
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                yield node.module


# Backend bounded contexts may not import each other directly.
modules = BACKEND / "modules"
for owner in contexts:
    owner_dir = modules / owner
    if not owner_dir.exists():
        errors.append(f"Missing backend context: {owner}")
        continue
    for path in owner_dir.rglob("*.py"):
        for imp in imports(path) or ():
            for target in contexts - {owner}:
                if imp.startswith(f"app.modules.{target}."):
                    errors.append(
                        f"Forbidden cross-context import: {path} -> {imp}"
                    )


# Employee modules may not import bounded-context implementations directly.
employees = modules / "employees"
if employees.exists():
    for path in employees.rglob("*.py"):
        for imp in imports(path) or ():
            for target in contexts:
                if imp.startswith(f"app.modules.{target}."):
                    errors.append(
                        f"Forbidden employee->context import: {path} -> {imp}"
                    )


# No application module may import infrastructure adapters directly.
for path in modules.rglob("*.py"):
    for imp in imports(path) or ():
        if imp.startswith("app.infrastructure.adapters."):
            errors.append(
                f"Forbidden infrastructure adapter import: {path} -> {imp}"
            )


# Frontend may not import backend Python modules or infrastructure adapters.
# Check actual module/import syntax rather than arbitrary feature/provider names;
# domain feature labels such as "shopify" are valid business concepts and are
# not evidence of a forbidden frontend dependency.
if FRONTEND.exists():
    forbidden_modules = (
        "app.infrastructure",
        "backend/app",
        "sqlalchemy",
    )
    for path in FRONTEND.rglob("*"):
        if path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            if not (stripped.startswith("import ") or stripped.startswith("export ") or "require(" in stripped):
                continue
            for token in forbidden_modules:
                if token in line:
                    errors.append(f"Forbidden frontend dependency: {path} imports {token}")


if errors:
    print("\n".join(errors))
    sys.exit(1)

print("Architecture check passed.")
