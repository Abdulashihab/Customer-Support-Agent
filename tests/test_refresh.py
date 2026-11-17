from src.tools.refresh_account import refresh_account


def test_normal_and_hard_refresh(db_copy):
    assert refresh_account("100003", db_path=db_copy) == {"ok": True, "kind": "normal"}
    assert refresh_account("100003", hard=True, db_path=db_copy) == {"ok": True, "kind": "hard"}


def test_refresh_is_refused_for_suspended_connection(db_copy):
    result = refresh_account("100005", db_path=db_copy)
    assert result == {"ok": False, "reason": "connection_suspended"}


def test_refresh_unknown_subscriber(db_copy):
    result = refresh_account("999999", db_path=db_copy)
    assert result == {"ok": False, "reason": "unknown_subscriber"}
