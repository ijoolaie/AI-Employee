from pathlib import Path
import ast

APP = Path(__file__).parents[1] / "app"
EMPLOYEES = APP / "modules" / "employees"
EMPLOYEE_NAMES = {"report", "document", "invoice", "order", "sales"}

def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            yield node.module or ""

def test_all_employee_modules_have_manifest_and_service():
    for name in EMPLOYEE_NAMES:
        module = EMPLOYEES / name
        assert (module / "manifest.py").exists()
        assert (module / "service.py").exists()
        assert (module / "__init__.py").exists()

def test_employee_modules_do_not_import_api_or_frontend():
    for name in EMPLOYEE_NAMES:
        for path in (EMPLOYEES / name).rglob("*.py"):
            imports = list(_imports(path))
            assert not any(i.startswith(("app.api", "frontend")) for i in imports), path

def test_employee_registry_is_explicit():
    registry = (EMPLOYEES / "registry.py").read_text(encoding="utf-8")
    for name in EMPLOYEE_NAMES:
        assert f"{name}.manifest" in registry
