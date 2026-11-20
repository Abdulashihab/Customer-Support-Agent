import secrets
from datetime import datetime, timedelta

from src.db.connection import get_connection

OTP_VALID_MINUTES = 5   # a code works for this many minutes
MAX_ATTEMPTS = 3        # wrong tries allowed before the code is thrown away

# Codes waiting to be used, kept in memory: {mobile number: {code, expires, attempts}}
_pending = {}


def request_otp(rmn, now=None, db_path=None):
    """
    Make a 6 digit code for a registered mobile number (RMN).

    DEMO ONLY: the code is returned so we can show it on screen.
    A real app would send it by SMS and never return it.
    """
    now = now or datetime.now()
    rmn = str(rmn)

    conn = get_connection(db_path)
    try:
        customer = conn.execute("SELECT id FROM customers WHERE rmn = ?", (rmn,)).fetchone()
    finally:
        conn.close()
    if customer is None:
        return {"ok": False, "reason": "unknown_number"}

    code = f"{secrets.randbelow(1_000_000):06d}"
    _pending[rmn] = {
        "code": code,
        "expires": now + timedelta(minutes=OTP_VALID_MINUTES),
        "attempts": 0,
    }
    return {"ok": True, "otp": code}


def verify_otp(rmn, code, now=None, db_path=None):
    """
    Check the code. If it is right, return the customer's connections.

    Returns {"ok": True, "connections": [...]} or {"ok": False, "reason": "..."}.
    """
    now = now or datetime.now()
    rmn = str(rmn)

    entry = _pending.get(rmn)
    if entry is None:
        return {"ok": False, "reason": "no_otp_requested"}

    if now > entry["expires"]:
        del _pending[rmn]
        return {"ok": False, "reason": "otp_expired"}

    if str(code).strip() != entry["code"]:
        entry["attempts"] += 1
        if entry["attempts"] >= MAX_ATTEMPTS:
            del _pending[rmn]
            return {"ok": False, "reason": "too_many_attempts"}
        return {
            "ok": False,
            "reason": "wrong_code",
            "attempts_left": MAX_ATTEMPTS - entry["attempts"],
        }

    del _pending[rmn]   # a code can be used only once

    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT k.subscriber_id, k.kind
            FROM connections k
            JOIN customers c ON c.id = k.customer_id
            WHERE c.rmn = ?
            ORDER BY CASE k.kind WHEN 'primary' THEN 0 ELSE 1 END, k.subscriber_id
            """,
            (rmn,),
        ).fetchall()
    finally:
        conn.close()
    return {"ok": True, "connections": [dict(r) for r in rows]}