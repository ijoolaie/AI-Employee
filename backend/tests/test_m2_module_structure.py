from pathlib import Path

APP = Path(__file__).parents[1] / "app"
MODULES = APP / "modules"

def test_m2_modules_exist():
    for name in ("workflow", "knowledge", "crm", "commerce", "billing"):
        assert (MODULES / name / "manifest.py").exists()
        assert (MODULES / name / "__init__.py").exists()

def test_employee_modules_remain_registered():
    registry = (MODULES / "registry.py").read_text(encoding="utf-8")
    for name in ("report", "document", "invoice", "order", "sales"):
        assert f"{name}.manifest" in registry

def test_shared_contracts_exist():
    assert (APP / "shared" / "module_contracts.py").exists()
    assert (APP / "shared" / "events.py").exists()
