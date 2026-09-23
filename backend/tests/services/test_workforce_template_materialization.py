from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import workforce_template_materialization as materialization


@pytest.mark.asyncio
async def test_first_party_workforce_template_materializes_exact_catalog_contract(monkeypatch):
    captured = {}

    async def fake_create_template(db, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id=uuid4(), **kwargs)

    monkeypatch.setattr(materialization, "create_template", fake_create_template)

    result = await materialization.create_first_party_workforce_template(
        object(),
        tenant_id=uuid4(),
        agent_definition_id=uuid4(),
        role_code="ai_trader",
        version=1,
        risk_tier=2,
        permission_policy={"permissions": ["run.execute"], "allowed_tools": []},
        approval_policy={"requires_ceo_approval": True},
        evaluation_policy={"suite_id": "workforce-trader-v1"},
        install_policy={"requires_ceo_approval": True},
    )

    assert result.slug == "ai-trader"
    assert result.name == "AI Trader"
    assert result.capability_contract["workforce_role_code"] == "ai_trader"
    assert result.capability_contract["workforce_capability_contract"]
    assert result.is_system_template is True
