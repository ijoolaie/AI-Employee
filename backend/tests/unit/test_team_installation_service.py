from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.team_installation import TeamInstallationError, TeamInstallationService


class Result:
    def __init__(self, row=None, scalar=None):
        self._row = row
        self._scalar = scalar

    def one_or_none(self):
        return self._row

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return SimpleNamespace(all=lambda: [])


class FakeSession:
    def __init__(self, rows):
        self.rows = iter(rows)
        self.added = []

    async def execute(self, _stmt):
        return next(self.rows)

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_install_rejects_cross_tenant_version():
    tenant_id = uuid4()
    source_tenant_id = uuid4()
    version = SimpleNamespace(id=uuid4(), version=1, member_agent_definition_ids=[uuid4()])
    team = SimpleNamespace(id=uuid4(), tenant_id=source_tenant_id, enabled=True)
    db = FakeSession([Result(row=(version, team))])

    with pytest.raises(TeamInstallationError, match="cross-tenant"):
        await TeamInstallationService(db).install(
            tenant_id=tenant_id,
            team_version_id=version.id,
            actor_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_install_rejects_disabled_team():
    tenant_id = uuid4()
    version = SimpleNamespace(id=uuid4(), version=1, member_agent_definition_ids=[uuid4()])
    team = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, enabled=False)
    db = FakeSession([Result(row=(version, team))])

    with pytest.raises(TeamInstallationError, match="disabled"):
        await TeamInstallationService(db).install(
            tenant_id=tenant_id,
            team_version_id=version.id,
            actor_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_install_rejects_empty_team():
    tenant_id = uuid4()
    version = SimpleNamespace(id=uuid4(), version=1, member_agent_definition_ids=[])
    team = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, enabled=True)
    db = FakeSession([Result(row=(version, team))])

    with pytest.raises(TeamInstallationError, match="no members"):
        await TeamInstallationService(db).install(
            tenant_id=tenant_id,
            team_version_id=version.id,
            actor_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_install_is_tenant_local_and_records_actor():
    tenant_id = uuid4()
    version = SimpleNamespace(id=uuid4(), version=1, member_agent_definition_ids=[uuid4()])
    team = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, enabled=True)
    db = FakeSession([Result(row=(version, team)), Result(scalar=None)])

    installation = await TeamInstallationService(db).install(
        tenant_id=tenant_id,
        team_version_id=version.id,
        actor_id=uuid4(),
        workspace_key="ops",
    )

    assert installation.tenant_id == tenant_id
    assert installation.team_version_id == version.id
    assert installation.workspace_key == "ops"
    assert installation.installed_by is not None
    assert installation.enabled is True
