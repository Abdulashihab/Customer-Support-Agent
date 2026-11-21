from fake_ai import FakeClient, text_answer, tool_answer
from src.agent.graph import build_graph, run_graph_turn


def test_escalation_ends_the_graph_without_the_ai(db_copy):
    client = FakeClient([])
    graph = build_graph(client=client, model="x", db_path=db_copy)
    history = []
    reply = run_graph_turn(graph, "100003", history, "I want to talk to your manager")
    assert "CB-1001" in reply
    assert client.requests == []        # the AI was not called
    assert len(history) == 2


def test_normal_message_goes_to_the_agent(db_copy):
    client = FakeClient([text_answer("Hello! How can I help?")])
    graph = build_graph(client=client, model="x", db_path=db_copy)
    history = []
    reply = run_graph_turn(graph, "100003", history, "hi")
    assert reply == "Hello! How can I help?"
    assert [m["role"] for m in history] == ["user", "assistant"]


def test_agent_can_use_a_tool_inside_the_graph(db_copy):
    client = FakeClient([
        tool_answer("get_account", {}),
        text_answer("Your account is shown."),
    ])
    graph = build_graph(client=client, model="x", db_path=db_copy)
    reply = run_graph_turn(graph, "100003", [], "what is my balance")
    assert reply == "Your account is shown."
    assert "Karthik" in client.requests[1][-1]["content"]