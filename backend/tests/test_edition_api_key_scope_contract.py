from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.edition_deps import (
    EDITION_RESELLER,
    EDITION_VENDOR,
    _enforce_api_key_scope,
)


def request(method: str, path: str):
    return SimpleNamespace(
        method=method,
        scope={"route": SimpleNamespace(path=path)},
    )


@pytest.mark.parametrize(
    ("kind", "path"),
    [
        (EDITION_VENDOR, "/api/v1/edition/licenses/vendor"),
        (EDITION_RESELLER, "/api/v1/edition/licenses/reseller"),
    ],
)
def test_license_list_requires_explicit_read_scope(kind: str, path: str):
    ctx = SimpleNamespace(
        api_key_id="api-key-id",
        api_key_scopes=["edition.licenses.read"],
    )
    assert _enforce_api_key_scope(ctx, request("GET", path), kind) is None


@pytest.mark.parametrize(
    ("kind", "path"),
    [
        (EDITION_VENDOR, "/api/v1/edition/licenses/vendor"),
        (EDITION_RESELLER, "/api/v1/edition/licenses/reseller"),
    ],
)
def test_license_list_rejects_api_key_without_read_scope(kind: str, path: str):
    ctx = SimpleNamespace(api_key_id="api-key-id", api_key_scopes=["edition.licenses.issue"])
    with pytest.raises(HTTPException) as exc:
        _enforce_api_key_scope(ctx, request("GET", path), kind)
    assert exc.value.status_code == 403


def test_license_list_rejects_legacy_api_key_without_scopes():
    ctx = SimpleNamespace(api_key_id="api-key-id", api_key_scopes=None)
    with pytest.raises(HTTPException) as exc:
        _enforce_api_key_scope(
            ctx,
            request("GET", "/api/v1/edition/licenses/vendor"),
            EDITION_VENDOR,
        )
    assert exc.value.status_code == 403
