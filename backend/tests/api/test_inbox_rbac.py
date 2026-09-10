import inspect
from typing import get_args

from app.api.v1 import inbox


def _ctx_permission(endpoint) -> str:
    annotation = inspect.get_annotations(endpoint, eval_str=True)["ctx"]
    metadata = get_args(annotation)[1]
    checker = metadata.dependency
    assert checker.__closure__ is not None
    return next(cell.cell_contents for cell in checker.__closure__ if isinstance(cell.cell_contents, str) and "." in cell.cell_contents)


def test_inbox_routes_have_explicit_rbac_boundaries():
    expected = {
        inbox.inbox: "employee.read",
        inbox.inbox_messages: "employee.read",
        inbox.handoff: "employee.write",
        inbox.inbox_send_message: "employee.write",
    }
    assert {endpoint: _ctx_permission(endpoint) for endpoint in expected} == expected
