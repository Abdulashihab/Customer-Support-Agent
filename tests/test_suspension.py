import sqlite3

from src.tools.account import get_account
from src.tools.suspension import (
    get_suspension_requests,
    request_suspension,
    resume_connection,
)

# The demo "today" is 2026-11-14, so the earliest start date is 2026-11-15.


def run_sql(db, sql, params=()):
    """Helper: change the throwaway test copy of the database directly."""
    conn = sqlite3.connect(db)
    conn.execute(sql, params)
    conn.commit()
    conn.close()


# ---------- request_suspension ----------

def test_valid_request_is_saved(db_copy):
    result = request_suspension("100003", "Going abroad", "2026-11-15", "2026-11-19", db_path=db_copy)
    assert result["ok"] is True
    assert result["suspension"]["days"] == 5
    assert result["suspension"]["status"] == "scheduled"
    # it is saved, and the connection stays active until the start date
    assert len(get_suspension_requests("100003", db_path=db_copy)) == 1
    assert get_account("100003", db_path=db_copy)["status"] == "active"


def test_reason_is_required(db_copy):
    for empty in ("", "   ", None):
        result = request_suspension("100003", empty, "2026-11-15", "2026-11-19", db_path=db_copy)
        assert result == {"ok": False, "reason": "reason_required"}


def test_cannot_start_today(db_copy):
    result = request_suspension("100003", "Trip", "2026-11-14", "2026-11-20", db_path=db_copy)
    assert result["ok"] is False
    assert result["reason"] == "start_must_be_after_today"
    assert result["earliest_start"] == "2026-11-15"


def test_cannot_start_in_the_past(db_copy):
    result = request_suspension("100003", "Trip", "2026-11-10", "2026-11-20", db_path=db_copy)
    assert result["reason"] == "start_must_be_after_today"


def test_minimum_five_days(db_copy):
    # 15th to 18th is only 4 days
    result = request_suspension("100003", "Trip", "2026-11-15", "2026-11-18", db_path=db_copy)
    assert result == {
        "ok": False,
        "reason": "minimum_period_not_met",
        "minimum_days": 5,
        "requested_days": 4,
    }


def test_end_before_start(db_copy):
    result = request_suspension("100003", "Trip", "2026-11-20", "2026-11-16", db_path=db_copy)
    assert result == {"ok": False, "reason": "invalid_date_range"}


def test_invalid_date_text(db_copy):
    result = request_suspension("100003", "Trip", "tomorrow", "2026-11-20", db_path=db_copy)
    assert result == {"ok": False, "reason": "invalid_date"}


def test_balance_must_cover_one_day_burn_rate(db_copy):
    # 100003 pays 512 a month, so one day costs 17.07. Give the customer only 10.
    run_sql(db_copy, "UPDATE connections SET balance = 10 WHERE subscriber_id = '100003'")
    result = request_suspension("100003", "Trip", "2026-11-15", "2026-11-19", db_path=db_copy)
    assert result["ok"] is False
    assert result["reason"] == "insufficient_balance"
    assert result["daily_burn_rate"] == 17.07
    assert result["minimum_recharge"] == 200


def test_already_suspended_connection(db_copy):
    result = request_suspension("100005", "Trip", "2026-11-15", "2026-11-19", db_path=db_copy)
    assert result == {"ok": False, "reason": "already_suspended"}


def test_unknown_subscriber(db_copy):
    result = request_suspension("999999", "Trip", "2026-11-15", "2026-11-19", db_path=db_copy)
    assert result == {"ok": False, "reason": "unknown_subscriber"}


def test_only_one_request_at_a_time(db_copy):
    request_suspension("100003", "Trip", "2026-11-15", "2026-11-19", db_path=db_copy)
    second = request_suspension("100003", "Another trip", "2026-12-01", "2026-12-10", db_path=db_copy)
    assert second == {"ok": False, "reason": "suspension_already_requested"}


# ---------- resume_connection ----------

def test_resume_unknown_subscriber(db_copy):
    result = resume_connection("999999", True, db_path=db_copy)
    assert result == {"ok": False, "reason": "unknown_subscriber"}


def test_resume_active_connection(db_copy):
    result = resume_connection("100003", True, db_path=db_copy)
    assert result == {"ok": False, "reason": "not_suspended"}


def test_resume_needs_the_set_top_box_on(db_copy):
    run_sql(db_copy, "UPDATE connections SET balance = 25 WHERE subscriber_id = '100005'")
    result = resume_connection("100005", False, db_path=db_copy)
    assert result == {"ok": False, "reason": "set_top_box_must_be_on"}


def test_resume_with_balance_below_one_day(db_copy):
    # 100005 pays 602 a month, so one day costs 20.07. Its balance is 0.
    result = resume_connection("100005", True, db_path=db_copy)
    assert result == {
        "ok": False,
        "reason": "insufficient_balance",
        "daily_burn_rate": 20.07,
        "balance": 0,
        "minimum_recharge": 200,
    }


def test_resume_works_with_one_day_of_balance(db_copy):
    # Balance 25 is far below the monthly charge of 602, but it covers one day (20.07).
    run_sql(db_copy, "UPDATE connections SET balance = 25 WHERE subscriber_id = '100005'")
    result = resume_connection("100005", True, db_path=db_copy)
    assert result == {"ok": True, "status": "active"}
    assert get_account("100005", db_path=db_copy)["status"] == "active"


def test_resume_works_when_balance_is_plenty(db_copy):
    # make 100003 suspended; its balance 850 covers everything
    run_sql(db_copy, "UPDATE connections SET status = 'suspended' WHERE subscriber_id = '100003'")
    result = resume_connection("100003", True, db_path=db_copy)
    assert result == {"ok": True, "status": "active"}
    assert get_account("100003", db_path=db_copy)["status"] == "active"