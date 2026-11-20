import copy
import json
from types import SimpleNamespace

from src.agent.agent import MAX_STEPS, chat_turn
from src.agent.tool_runner import ACTION_TOOLS, READ_TOOLS
from src.agent.tool_schemas import TOOL_SCHEMAS
from src.tools.account import get_account


# ---------- a fake AI, so the tests never use your daily quota ----------

class FakeClient:
    """Pretends to be the AI. It returns the answers we prepared, one by one."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.requests = []   # what we sent to the "AI", for checking
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(copy.deepcopy(kwargs["messages"]))
        return self.answers.pop(0)


def text_answer(text):
    message = SimpleNamespace(content=text, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def tool_answer(name, args):
    call = SimpleNamespace(
        id="call_1", function=SimpleNamespace(name=name, arguments=json.dumps(args))
    )
    message = SimpleNamespace(content=None, tool_calls=[call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


# ---------- tests ----------

def test_clear_escalation_never_reaches_the_ai(db_copy):
    client = FakeClient([])
    reply = chat_turn("100003", [], "I want to talk to your manager",
                      client=client, model="x", db_path=db_copy)
    assert "CB-1001" in reply
    assert client.requests == []          # the AI was not called at all


def test_plain_answer_is_returned_and_saved_in_history(db_copy):
    history = []
    client = FakeClient([text_answer("Hello! How can I help?")])
    reply = chat_turn("100003", history, "hi", client=client, model="x", db_path=db_copy)
    assert reply == "Hello! How can I help?"
    assert [m["role"] for m in history] == ["user", "assistant"]


def test_tool_runs_for_the_logged_in_customer_only(db_copy):
    # the AI asks for customer 100005, but the session customer is 100003
    client = FakeClient([
        tool_answer("get_account", {"subscriber_id": "100005"}),
        text_answer("Your balance is shown."),
    ])
    chat_turn("100003", [], "what is my balance", client=client, model="x", db_path=db_copy)
    tool_message = client.requests[1][-1]          # what the AI received back
    assert tool_message["role"] == "tool"
    assert "Karthik" in tool_message["content"]    # customer 100003, not 100005


def test_action_tool_changes_the_database(db_copy):
    client = FakeClient([
        tool_answer("add_pack", {"pack_id": "DSK-TLK1"}),
        text_answer("The pack is added."),
    ])
    chat_turn("100003", [], "yes, add it", client=client, model="x", db_path=db_copy)
    packs = [p["pack_id"] for p in get_account("100003", db_path=db_copy)["packs"]]
    assert "DSK-TLK1" in packs


def test_search_docs_tool_uses_the_search_function(db_copy):
    asked = []

    def fake_search(question):
        asked.append(question)
        return {"ok": True, "data": [{"source": "recharge.md", "section": "Rules", "text": "Minimum 200"}]}

    client = FakeClient([
        tool_answer("search_docs", {"question": "minimum recharge"}),
        text_answer("The minimum recharge is 200 rupees."),
    ])
    reply = chat_turn("100003", [], "what is the minimum recharge", client=client,
                      model="x", db_path=db_copy, docs_search=fake_search)
    assert asked == ["minimum recharge"]
    assert "200" in reply


def test_loop_stops_if_the_ai_never_finishes(db_copy):
    client = FakeClient([tool_answer("get_account", {}) for _ in range(MAX_STEPS)])
    reply = chat_turn("100003", [], "hello", client=client, model="x", db_path=db_copy)
    assert reply.startswith("Sorry, I could not finish")


def test_tool_descriptions_match_the_real_tools():
    names = {schema["function"]["name"] for schema in TOOL_SCHEMAS}
    real = set(READ_TOOLS) | set(ACTION_TOOLS) | {"search_docs"}
    assert names <= real
    for schema in TOOL_SCHEMAS:
        # no tool may ask the AI for a subscriber ID
        assert "subscriber_id" not in schema["function"]["parameters"]["properties"]