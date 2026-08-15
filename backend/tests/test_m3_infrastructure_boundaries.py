from pathlib import Path

APP = Path(__file__).parents[1] / "app"
INFRA = APP / "infrastructure"
MODULES = APP / "modules"

def test_infrastructure_ports_exist():
    for name in ("repository.py", "queue.py", "storage.py", "external.py", "composition.py"):
        assert (INFRA / name).exists()

def test_bounded_contexts_expose_ports():
    for name in ("workflow", "knowledge", "crm", "commerce", "billing"):
        assert (MODULES / name / "ports.py").exists()

def test_employee_modules_expose_ports():
    for name in ("report", "document", "invoice", "order", "sales"):
        assert (MODULES / "employees" / name / "ports.py").exists()

def test_adapter_boundaries_exist():
    for name in ("sqlalchemy", "redis", "celery", "storage", "stripe", "shopify", "ai"):
        assert (INFRA / "adapters" / name).is_dir()
