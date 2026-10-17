from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.api.v1.ai_workforce_roles import materialize_first_party_workforce_template


def _result(value):
    return SimpleNamespace(scalar_one_or_none=lambda: value)


@pytest.mark.asyncio
async def test_materialize_rejects_unknown_first_party_role_before_database_access():
    db = SimpleNamespace(execute=AsyncMock())
    ctx = SimpleNamespace(tenant_id="tenant-a", user_id="user-a")

    with pytest.raises(HTTPException) as exc:
        await materialize_first_party_workforce_template(
            "role_that_does_not_exist", ctx=ctx, db=db
        )

    assert exc.value.status_code == 404
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_materialize_duplicate_template_is_rejected_with_tenant_scoped_lookup():
    existing = SimpleNamespace(id="existing-template")
    db = SimpleNamespace(execute=AsyncMock(return_value=_result(existing)))
    ctx = SimpleNamespace(tenant_id="tenant-a", user_id="user-a")

    with pytest.raises(HTTPException) as exc:
        await materialize_first_party_workforce_template(
            "ai_software_developer", ctx=ctx, db=db
        )

    assert exc.value.status_code == 409
    statement = db.execute.await_args.args[0]
    compiled = statement.compile()
    assert "agent_templates.tenant_id" in str(statement)
    assert "tenant-a" in compiled.params.values()


@pytest.mark.asyncio
async def test_materialize_rejects_conflicting_tenant_agent_definition():
    conflicting_definition = SimpleNamespace(
        name="Unrelated definition",
        capabilities=[],
        allowed_tools=[],
        policy_requirements={"workforce_role_code": "some_other_role"},
    )
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[_result(None), _result(conflicting_definition)])
    )
    ctx = SimpleNamespace(tenant_id="tenant-a", user_id="user-a")

    with pytest.raises(HTTPException) as exc:
        await materialize_first_party_workforce_template(
            "ai_software_developer", ctx=ctx, db=db
        )

    assert exc.value.status_code == 409
    assert "conflicts with the first-party role" in exc.value.detail
    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_materialize_rolls_back_when_definition_flush_fails():
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[_result(None), _result(None)]),
        add=Mock(),
        flush=AsyncMock(side_effect=RuntimeError("simulated flush failure")),
        rollback=AsyncMock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )
    ctx = SimpleNamespace(tenant_id="tenant-a", user_id="user-a")

    with pytest.raises(HTTPException) as exc:
        await materialize_first_party_workforce_template(
            "ai_software_developer", ctx=ctx, db=db
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "Could not materialize the first-party workforce template"
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()
