import pytest
from starlette.requests import Request

import app.main as main


def _request(authorization: str | None = None) -> Request:
    headers = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode()))
    return Request({"type": "http", "method": "GET", "path": "/metrics", "headers": headers})


@pytest.mark.asyncio
async def test_metrics_rejects_invalid_bearer_token(monkeypatch):
    monkeypatch.setenv("METRICS_AUTH_TOKEN", "test-secret")
    with pytest.raises(Exception) as exc_info:
        await main.metrics(_request("Bearer wrong"))
    assert getattr(exc_info.value, "status_code", None) == 401


@pytest.mark.asyncio
async def test_metrics_accepts_correct_bearer_token(monkeypatch):
    monkeypatch.setenv("METRICS_AUTH_TOKEN", "test-secret")
    monkeypatch.setattr(main, "REQUEST_COUNT", None)
    response = await main.metrics(_request("Bearer test-secret"))
    assert response.status_code == 200
