from src.tools.account import get_account
from src.tools.work_orders import get_work_orders


def test_healthy_account():
    account = get_account("100003")
    assert account["name"] == "Karthik Subramanian"
    assert account["status"] == "active"
    assert account["balance"] == 850
    assert account["monthly_charge"] == 512
    assert [p["pack_id"] for p in account["packs"]] == ["DSK-BASIC", "DSK-TMK2"]


def test_suspended_account():
    account = get_account("100005")
    assert account["status"] == "suspended"
    assert account["balance"] == 0


def test_secondary_connection_has_its_own_balance():
    primary = get_account("100010")
    secondary = get_account("100011")
    assert primary["rmn"] == secondary["rmn"]
    assert secondary["kind"] == "secondary"
    assert primary["balance"] != secondary["balance"]


def test_unknown_subscriber_returns_none():
    assert get_account("999999") is None


def test_scheduled_work_order():
    orders = get_work_orders("100006")
    assert len(orders) == 1
    assert orders[0]["issue_type"] == "no_signal"
    assert orders[0]["status"] == "scheduled"
    assert orders[0]["slot"] == "2026-11-16 10:00-13:00"


def test_unscheduled_work_order_has_no_slot():
    orders = get_work_orders("100007")
    assert orders[0]["status"] == "unscheduled"
    assert orders[0]["slot"] is None


def test_no_work_orders():
    assert get_work_orders("100003") == []