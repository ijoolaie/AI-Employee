from pathlib import Path

from app.models.employee import EmployeeVersion


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "alembic" / "versions" / "p1h_employee_single_current_version.py"


def test_employee_version_model_declares_single_current_index() -> None:
    index = next(
        index
        for index in EmployeeVersion.__table__.indexes
        if index.name == "uq_employee_single_current_version"
    )

    assert index.unique is True
    assert [column.name for column in index.columns] == ["employee_id"]
    assert str(index.dialect_options["postgresql"]["where"]) == "is_current = true"


def test_employee_version_migration_declares_single_current_index() -> None:
    source = MIGRATION.read_text(encoding="utf-8")

    assert 'revision = "p1hemployeesinglecurrent"' in source
    assert 'down_revision = "p1gteaminstallnull"' in source
    assert '"uq_employee_single_current_version"' in source
    assert '"is_current = true"' in source
