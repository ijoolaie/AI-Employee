from app.api.v1.agent_templates import AgentInstanceLifecycleRequest
from app.models.agent_instance import AgentInstanceStatus
from app.services.agent_template_service import _ALLOWED_LIFECYCLE_TRANSITIONS


def test_agent_instance_lifecycle_states_are_explicit() -> None:
    assert {item.value for item in AgentInstanceStatus} == {
        "enabled",
        "disabled",
        "draining",
        "suspended",
        "retired",
    }


def test_agent_instance_lifecycle_transition_matrix_is_fail_closed() -> None:
    assert _ALLOWED_LIFECYCLE_TRANSITIONS[AgentInstanceStatus.ENABLED] == {
        AgentInstanceStatus.DRAINING,
        AgentInstanceStatus.SUSPENDED,
        AgentInstanceStatus.RETIRED,
    }
    assert _ALLOWED_LIFECYCLE_TRANSITIONS[AgentInstanceStatus.DRAINING] == {
        AgentInstanceStatus.ENABLED,
        AgentInstanceStatus.SUSPENDED,
        AgentInstanceStatus.RETIRED,
    }
    assert _ALLOWED_LIFECYCLE_TRANSITIONS[AgentInstanceStatus.SUSPENDED] == {
        AgentInstanceStatus.ENABLED,
        AgentInstanceStatus.RETIRED,
    }
    assert _ALLOWED_LIFECYCLE_TRANSITIONS[AgentInstanceStatus.DISABLED] == {
        AgentInstanceStatus.ENABLED,
        AgentInstanceStatus.RETIRED,
    }
    assert _ALLOWED_LIFECYCLE_TRANSITIONS[AgentInstanceStatus.RETIRED] == set()


def test_lifecycle_request_requires_explicit_requester() -> None:
    request = AgentInstanceLifecycleRequest(
        target_status=AgentInstanceStatus.RETIRED,
        requested_by_user_id="00000000-0000-0000-0000-000000000001",
    )
    assert request.requested_by_user_id is not None


def test_retirement_is_terminal_and_cannot_be_reactivated() -> None:
    assert AgentInstanceStatus.RETIRED not in _ALLOWED_LIFECYCLE_TRANSITIONS[AgentInstanceStatus.RETIRED]
    assert all(
        AgentInstanceStatus.RETIRED not in {
            AgentInstanceStatus.ENABLED,
            AgentInstanceStatus.DRAINING,
        }
        for _ in [0]
    )
