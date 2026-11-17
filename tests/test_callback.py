from src.tools.request_callback import request_callback


def test_callback_request_is_saved(db_copy):
    result = request_callback("100003", "manager_request", "Customer wants a manager", db_path=db_copy)
    assert result == {
        "ok": True,
        "request_id": "CB-1001",
        "phone": "9000000003",
        "call_within": "15 to 30 minutes",
    }


def test_only_one_open_callback_per_customer(db_copy):
    request_callback("100003", "angry_customer", "Customer is angry", db_path=db_copy)
    second = request_callback("100003", "legal_threat", "Mentioned consumer court", db_path=db_copy)
    assert second["ok"] is False
    assert second["reason"] == "callback_already_requested"
    assert second["request_id"] == "CB-1001"


def test_unknown_reason_is_refused(db_copy):
    result = request_callback("100003", "just_because", "Some summary", db_path=db_copy)
    assert result == {"ok": False, "reason": "invalid_reason"}


def test_suspended_customer_can_still_ask_for_a_callback(db_copy):
    # 100005 is suspended, but an angry customer must still be able to reach a supervisor
    result = request_callback("100005", "angry_customer", "Customer is upset", db_path=db_copy)
    assert result["ok"] is True
