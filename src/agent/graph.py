from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agent.agent import run_agent_loop
from src.agent.escalation import handle_escalation


class ChatState(TypedDict):
    """Everything the graph remembers while it handles one message."""
    subscriber_id: str
    history: list
    message: str
    reply: str
    escalated: bool


def build_graph(client=None, model=None, db_path=None, docs_search=None):
    """Build the LangGraph flow: guardrail first, then the AI agent."""

    def guardrail_node(state):
        escalation = handle_escalation(state["subscriber_id"], state["message"], db_path=db_path)
        if escalation is None:
            return {"escalated": False}
        history = list(state["history"]) + [
            {"role": "user", "content": state["message"]},
            {"role": "assistant", "content": escalation["reply"]},
        ]
        return {"escalated": True, "reply": escalation["reply"], "history": history}

    def agent_node(state):
        history = list(state["history"])
        reply = run_agent_loop(
            state["subscriber_id"], history, state["message"],
            client=client, model=model, db_path=db_path, docs_search=docs_search,
        )
        return {"reply": reply, "history": history}

    def route_after_guardrail(state):
        return "end" if state["escalated"] else "agent"

    graph = StateGraph(ChatState)
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("agent", agent_node)
    graph.add_edge(START, "guardrail")
    graph.add_conditional_edges("guardrail", route_after_guardrail, {"agent": "agent", "end": END})
    graph.add_edge("agent", END)
    return graph.compile()


def run_graph_turn(graph, subscriber_id, history, message):
    """One message through the graph. The caller's history list is updated in place."""
    result = graph.invoke({
        "subscriber_id": subscriber_id,
        "history": list(history),
        "message": message,
        "reply": "",
        "escalated": False,
    })
    history[:] = result["history"]
    return result["reply"]