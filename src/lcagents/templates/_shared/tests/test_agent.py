from agent.agent import agent


def test_agent_is_invokable() -> None:
    assert hasattr(agent, "invoke")
