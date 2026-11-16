import shutil

import pytest

from src.db.connection import DB_PATH
from src.tools.create_work_order import create_work_order
from src.tools.work_orders import get_work_orders


@pytest.fixture
def db_copy(tmp_path):
    """Give every test its own throwaway copy of the database."""
    copy = tmp_path / "test.db"
    shutil.copy(DB_PATH, copy)
    return copy


def test_creates_work_order(db_copy):
    result = create_work_order("100003", "no_signal", db_path=db_copy)
    assert result["ok"] is True
    assert result["work_order"]["wo_id"] == "WO-1005"
    assert result["work_order"]["status"] == "unscheduled"
    # the new order is really saved in the database
    orders = get_work_orders("100003", db_path=db_copy)
    assert len(orders) == 1
    assert orders[0]["issue_type"] == "no_signal"


def test_rejects_unknown_issue_type(db_copy):
    result = create_work_order("100003", "banana", db_path=db_copy)
    assert result == {"ok": False, "reason": "invalid_issue_type"}


def test_rejects_unknown_subscriber(db_copy):
    result = create_work_order("999999", "no_signal", db_path=db_copy)
    assert result == {"ok": False, "reason": "unknown_subscriber"}


def test_rejects_suspended_connection(db_copy):
    result = create_work_order("100005", "no_signal", db_path=db_copy)
    assert result == {"ok": False, "reason": "connection_suspended"}


def test_rejects_duplicate_scheduled_order(db_copy):
    # 100006 already has a scheduled no_signal visit
    result = create_work_order("100006", "no_signal", db_path=db_copy)
    assert result["ok"] is False
    assert result["reason"] == "duplicate_open_work_order"
    assert result["wo_id"] == "WO-1001"


def test_rejects_duplicate_unscheduled_order(db_copy):
    # 100007 already has an unscheduled stb_upgrade
    result = create_work_order("100007", "stb_upgrade", db_path=db_copy)
    assert result["ok"] is False
    assert result["reason"] == "duplicate_open_work_order"


def test_completed_order_does_not_block_a_new_one(db_copy):
    # 100008 had a dish_alignment visit that is already completed
    result = create_work_order("100008", "dish_alignment", db_path=db_copy)
    assert result["ok"] is True