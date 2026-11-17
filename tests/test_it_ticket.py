from src.tools.it_ticket import create_it_ticket


def test_ticket_is_created(db_copy):
    result = create_it_ticket("100003", "channel_not_visible", "Error 3. Refresh and hard refresh done.", db_path=db_copy)
    assert result == {"ok": True, "ticket_id": "TKT-1001", "resolved_within": "2 hours"}


def test_no_second_open_ticket_for_the_same_issue(db_copy):
    create_it_ticket("100003", "channel_not_visible", "Error 3", db_path=db_copy)
    second = create_it_ticket("100003", "channel_not_visible", "Error 3 again", db_path=db_copy)
    assert second["ok"] is False
    assert second["reason"] == "duplicate_open_ticket"
    assert second["ticket_id"] == "TKT-1001"


def test_suspended_connection_gets_no_ticket(db_copy):
    result = create_it_ticket("100005", "channel_not_visible", "Error 5", db_path=db_copy)
    assert result == {"ok": False, "reason": "connection_suspended"}


def test_unknown_issue_type_is_refused(db_copy):
    result = create_it_ticket("100003", "banana", "Some details", db_path=db_copy)
    assert result == {"ok": False, "reason": "invalid_issue_type"}
