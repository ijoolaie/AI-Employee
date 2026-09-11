import inspect

from app.services import agent_governance, agent_policy_engine


def test_authorization_locks_identity_then_instance_for_side_effect_fence():
    source = inspect.getsource(agent_policy_engine.authorize)
    identity_block = source.index("select(AgentIdentity)")
    instance_block = source.index("select(AgentInstance)")
    assert source.index(".with_for_update()", identity_block) < instance_block
    assert source.index(".with_for_update()", instance_block) > instance_block


def test_access_review_uses_same_identity_then_instance_lock_order():
    source = inspect.getsource(agent_governance.review_access)
    identity_block = source.index("select(AgentIdentity)")
    instance_block = source.index("select(AgentInstance)")
    assert source.index(".with_for_update()", identity_block) < instance_block
    assert source.index(".with_for_update()", instance_block) > instance_block
