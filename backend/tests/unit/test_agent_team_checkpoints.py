from uuid import uuid4

import pytest

from app.services.agent_team_checkpoints import TeamCheckpointStore
from app.services.agent_teams import AgentTeamError, TeamRun, TeamRunStatus


def test_checkpoint_save_and_replay_preserves_state():
    tenant = uuid4()
    run = TeamRun(team_id=uuid4(), tenant_id=tenant, correlation_id="corr-1")
    run.transition(TeamRunStatus.WAITING_APPROVAL, actor_tenant_id=tenant)

    store = TeamCheckpointStore()
    store.save(run, actor_tenant_id=tenant)

    restored = TeamRun(team_id=run.team_id, tenant_id=tenant, correlation_id="corr-1")
    store.replay(restored, actor_tenant_id=tenant)

    assert restored.status == TeamRunStatus.WAITING_APPROVAL
    assert restored.approval_required is True
    assert restored.evidence == run.evidence


def test_checkpoint_rejects_cross_tenant_access():
    tenant = uuid4()
    run = TeamRun(team_id=uuid4(), tenant_id=tenant, correlation_id="corr-2")
    store = TeamCheckpointStore()

    with pytest.raises(AgentTeamError, match="checkpoint tenant mismatch"):
        store.save(run, actor_tenant_id=uuid4())
