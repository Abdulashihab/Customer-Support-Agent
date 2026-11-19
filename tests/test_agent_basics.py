from src.agent.escalation import handle_escalation
from src.agent.tool_runner import run_tool


# ---------- run_tool ----------

def test_subscriber_id_from_outside_is_ignored(db_copy):
    # the AI tries to look at another customer (100005), but the session says 100003
    result = run_tool("100003", "get_account", {"subscriber_id": "100005"}, db_path=db_copy)
    assert result["ok"] is True
    assert result["data"]["subscriber_id"] == "100003"


def test_unknown_tool(db_copy):
    result = run_tool("100003", "delete_everything", db_path=db_copy)
    assert result == {"ok": False, "reason": "unknown_tool"}


def test_bad_arguments(db_copy):
    result = run_tool("100003", "add_pack", {"wrong_name": 1}, db_path=db_copy)
    assert result == {"ok": False, "reason": "bad_arguments"}


def test_action_tool_runs_through_the_runner(db_copy):
    result = run_tool("100003", "add_pack", {"pack_id": "DSK-TLK1"}, db_path=db_copy)
    assert result["ok"] is True
    assert result["new_monthly_charge"] == 731


# ---------- handle_escalation ----------

def test_manager_request_takes_a_callback(db_copy):
    result = handle_escalation("100003", "I want to talk to your manager", db_path=db_copy)
    assert result["reason"] == "manager_request"
    assert "CB-1001" in result["reply"]
    assert "15 to 30 minutes" in result["reply"]


def test_second_escalation_gives_the_same_request_number(db_copy):
    handle_escalation("100003", "I want your manager", db_path=db_copy)
    second = handle_escalation("100003", "I will go to consumer court", db_path=db_copy)
    assert "CB-1001" in second["reply"]


def test_normal_message_is_not_escalated(db_copy):
    assert handle_escalation("100003", "my TV shows nothing", db_path=db_copy) is None