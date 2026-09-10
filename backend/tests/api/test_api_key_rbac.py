import inspect
from typing import get_args

from app.api.v1 import api_keys


def _ctx_permission(endpoint) -> str:
    annotation = inspect.get_annotations(endpoint, eval_str=True)["ctx"]
    metadata = get_args(annotation)[1]
    checker = metadata.dependency
    assert checker.__closure__ is not None
    return next(
        cell.cell_contents
        for cell in checker.__closure__
        if isinstance(cell.cell_contents, str) and cell.cell_contents.startswith("api_keys.")
    )


def test_api_key_routes_have_explicit_rbac_boundaries():
    expected = {
        api_keys.list_api_keys: "api_keys.read",
        api_keys.create_api_key: "api_keys.create",
        api_keys.revoke_api_key: "api_keys.revoke",
    }
    assert {endpoint: _ctx_permission(endpoint) for endpoint in expected} == expected
