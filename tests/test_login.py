from datetime import datetime, timedelta

from src.auth.login import MAX_ATTEMPTS, request_otp, verify_otp

NOW = datetime(2026, 11, 14, 10, 0, 0)
RMN = "9000000010"   # this customer has a primary and a secondary connection


def test_unknown_number_gets_no_code(db_copy):
    result = request_otp("1111111111", now=NOW, db_path=db_copy)
    assert result == {"ok": False, "reason": "unknown_number"}


def test_correct_code_logs_in_and_lists_connections(db_copy):
    otp = request_otp(RMN, now=NOW, db_path=db_copy)["otp"]
    result = verify_otp(RMN, otp, now=NOW, db_path=db_copy)
    assert result["ok"] is True
    assert result["connections"] == [
        {"subscriber_id": "100010", "kind": "primary"},
        {"subscriber_id": "100011", "kind": "secondary"},
    ]


def test_wrong_codes_run_out_of_attempts(db_copy):
    otp = request_otp(RMN, now=NOW, db_path=db_copy)["otp"]
    wrong = "000000" if otp != "000000" else "111111"

    first = verify_otp(RMN, wrong, now=NOW, db_path=db_copy)
    assert first == {"ok": False, "reason": "wrong_code", "attempts_left": MAX_ATTEMPTS - 1}

    for _ in range(MAX_ATTEMPTS - 2):
        verify_otp(RMN, wrong, now=NOW, db_path=db_copy)
    last = verify_otp(RMN, wrong, now=NOW, db_path=db_copy)
    assert last == {"ok": False, "reason": "too_many_attempts"}

    # the code is thrown away, so even the right one no longer works
    again = verify_otp(RMN, otp, now=NOW, db_path=db_copy)
    assert again == {"ok": False, "reason": "no_otp_requested"}


def test_expired_code(db_copy):
    otp = request_otp(RMN, now=NOW, db_path=db_copy)["otp"]
    later = NOW + timedelta(minutes=6)
    result = verify_otp(RMN, otp, now=later, db_path=db_copy)
    assert result == {"ok": False, "reason": "otp_expired"}


def test_code_can_be_used_only_once(db_copy):
    otp = request_otp(RMN, now=NOW, db_path=db_copy)["otp"]
    assert verify_otp(RMN, otp, now=NOW, db_path=db_copy)["ok"] is True
    second = verify_otp(RMN, otp, now=NOW, db_path=db_copy)
    assert second == {"ok": False, "reason": "no_otp_requested"}