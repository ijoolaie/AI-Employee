import io

import pytest
from starlette.requests import Request

import app.main as main
from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError
from app.services.file_policy import validate_content_type
from app.services.file_service import _LimitedReader
from app.services.sales_readiness_service import TEMPLATES
from app.services.tool_approval_policy import MANDATORY_APPROVAL_TOOLS


def _request(authorization: str | None = None) -> Request:
    headers = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode()))
    return Request({"type": "http", "method": "GET", "path": "/metrics", "headers": headers})


def test_security_regression_side_effects_require_approval():
    assert MANDATORY_APPROVAL_TOOLS
    for name in MANDATORY_APPROVAL_TOOLS:
        tool = registry.get(name)
        assert tool.side_effects is True
        assert tool.requires_approval is True


def test_security_regression_templates_reference_only_registered_tools():
    registered = {tool.name for tool in registry.list()}
    for template in TEMPLATES:
        assert set(template["allowed_tools"]).issubset(registered)
    assert "add_to_cart" not in registered


def test_security_regression_file_policy_rejects_unsafe_types():
    validate_content_type("application/pdf", "document.pdf")
    with pytest.raises(ValueError):
        validate_content_type("application/x-msdownload", "document.exe")


def test_security_regression_bounded_reader():
    reader = _LimitedReader(io.BytesIO(b"abcdef"), 3)
    assert reader.read(1024) == b"abc"
    assert reader.read(1024) == b""


@pytest.mark.asyncio
async def test_security_regression_metrics_requires_token_when_configured(monkeypatch):
    monkeypatch.setenv("METRICS_AUTH_TOKEN", "phase-12-7-secret")
    with pytest.raises(Exception) as exc_info:
        await main.metrics(_request("Bearer wrong"))
    assert getattr(exc_info.value, "status_code", None) == 401


@pytest.mark.asyncio
async def test_security_regression_mandatory_tool_cannot_execute_without_approval():
    with pytest.raises(ValidationAppError, match="Human approval required"):
        await registry.execute(
            "create_order",
            {"customer_name": "Regression", "line_items": [{"description": "item", "unit_price": 1}]},
            permissions={"run.execute"},
            approval_granted=False,
            allowed_tools={"create_order"},
        )
