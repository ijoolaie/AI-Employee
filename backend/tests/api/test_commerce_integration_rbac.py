import inspect
from typing import get_args

from app.api.v1 import commerce_integrations


EXPECTED_PERMISSION = "commerce.integration.manage"


def _ctx_permission(endpoint) -> str:
    annotation = inspect.get_annotations(endpoint, eval_str=True)["ctx"]
    metadata = get_args(annotation)[1]
    checker = metadata.dependency
    assert checker.__closure__ is not None
    return next(cell.cell_contents for cell in checker.__closure__ if cell.cell_contents == EXPECTED_PERMISSION)


def test_commerce_lifecycle_routes_require_manage_permission():
    endpoints = (
        commerce_integrations.list_integrations,
        commerce_integrations.create_integration,
        commerce_integrations.shopify_install,
        commerce_integrations.test_integration,
        commerce_integrations.sync_products,
        commerce_integrations.sync_orders,
        commerce_integrations.reconcile,
    )

    assert all(_ctx_permission(endpoint) == EXPECTED_PERMISSION for endpoint in endpoints)


def test_shopify_callback_has_no_direct_request_auth_but_requires_issued_state():
    # OAuth callback is provider-redirected and therefore cannot use the caller's
    # bearer/API-key context. Authorization is intentionally inherited from the
    # short-lived, single-use state issued by shopify_install.
    assert "ctx" not in inspect.signature(commerce_integrations.shopify_callback).parameters


import pytest
from types import SimpleNamespace
from uuid import uuid4


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("endpoint_name", "service_name", "action", "result"),
    [
        ("test_integration", "test_connection", "commerce.integration.tested", {"ok": True}),
        ("sync_products", "sync_products", "commerce.integration.products_synced", {"created": 2}),
        ("sync_orders", "sync_orders", "commerce.integration.orders_synced", {"created": 3}),
        ("reconcile", "reconcile", "commerce.integration.reconciled", {"products": {}, "orders": {}}),
    ],
)
async def test_commerce_side_effect_audit_preserves_actor_and_resource(
    monkeypatch, endpoint_name, service_name, action, result
):
    tenant_id = uuid4()
    actor_id = uuid4()
    integration_id = uuid4()
    audit = []

    async def side_effect(*args, **kwargs):
        assert args[1] == tenant_id
        assert args[2] == integration_id
        return result

    async def record(*args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(commerce_integrations.shopify_service, service_name, side_effect)
    monkeypatch.setattr(commerce_integrations.audit_service, "record", record)

    class Db:
        async def commit(self):
            pass

    ctx = SimpleNamespace(tenant_id=tenant_id, user_id=actor_id)
    response = await getattr(commerce_integrations, endpoint_name)(integration_id, ctx, Db())

    assert response.success is True
    assert response.data == result
    assert len(audit) == 1
    assert audit[0]["tenant_id"] == tenant_id
    assert audit[0]["actor_id"] == actor_id
    assert audit[0]["action"] == action
    assert audit[0]["resource_type"] == "commerce_integration"
    assert audit[0]["resource_id"] == integration_id
    assert audit[0]["metadata"]["provider"] == "shopify"
