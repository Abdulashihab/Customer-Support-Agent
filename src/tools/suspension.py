from datetime import date, timedelta

from src.db.connection import get_connection

MIN_SUSPENSION_DAYS = 5   # a suspension must last at least this many days
DAYS_IN_MONTH = 30        # used to work out the daily burn rate (DBR)


def _get_today(conn):
    """The company's 'today'. For this demo it is fixed in the database."""
    row = conn.execute("SELECT value FROM meta WHERE key = 'reference_date'").fetchone()
    return date.fromisoformat(row["value"]) if row else date.today()


def request_suspension(subscriber_id, reason, start_date, end_date, db_path=None):
    """
    Request a temporary suspension (dates are YYYY-MM-DD).

    Returns {"ok": True, "suspension": {...}} or {"ok": False, "reason": "..."}.
    """
    subscriber_id = str(subscriber_id)

    # Rule 1: a reason is required.
    if not reason or not str(reason).strip():
        return {"ok": False, "reason": "reason_required"}

    # Rule 2: both dates must be real dates, and the end cannot be before the start.
    try:
        start = date.fromisoformat(str(start_date))
        end = date.fromisoformat(str(end_date))
    except ValueError:
        return {"ok": False, "reason": "invalid_date"}
    if end < start:
        return {"ok": False, "reason": "invalid_date_range"}

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT status, balance, monthly_charge FROM connections WHERE subscriber_id = ?",
            (subscriber_id,),
        ).fetchone()
        if row is None:
            return {"ok": False, "reason": "unknown_subscriber"}
        if row["status"] == "suspended":
            return {"ok": False, "reason": "already_suspended"}

        # Rule 3: today is already running, so the earliest start is tomorrow.
        today = _get_today(conn)
        if start <= today:
            return {
                "ok": False,
                "reason": "start_must_be_after_today",
                "earliest_start": (today + timedelta(days=1)).isoformat(),
            }

        # Rule 4: the suspension must be at least 5 days long (both dates count).
        days = (end - start).days + 1
        if days < MIN_SUSPENSION_DAYS:
            return {
                "ok": False,
                "reason": "minimum_period_not_met",
                "minimum_days": MIN_SUSPENSION_DAYS,
                "requested_days": days,
            }

        # Rule 5: the balance must cover at least one day's burn rate.
        daily_burn_rate = row["monthly_charge"] / DAYS_IN_MONTH
        if row["balance"] < daily_burn_rate:
            return {
                "ok": False,
                "reason": "insufficient_balance",
                "daily_burn_rate": round(daily_burn_rate, 2),
                "balance": row["balance"],
            }

        # Rule 6: only one suspension request at a time.
        existing = conn.execute(
            """
            SELECT id FROM suspension_requests
            WHERE subscriber_id = ? AND status IN ('scheduled', 'active')
            """,
            (subscriber_id,),
        ).fetchone()
        if existing is not None:
            return {"ok": False, "reason": "suspension_already_requested"}

        # All rules passed: save the request.
        cursor = conn.execute(
            """
            INSERT INTO suspension_requests (subscriber_id, start_date, end_date, reason, status)
            VALUES (?, ?, ?, ?, 'scheduled')
            """,
            (subscriber_id, start.isoformat(), end.isoformat(), str(reason).strip()),
        )
        conn.commit()

        return {
            "ok": True,
            "suspension": {
                "id": cursor.lastrowid,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "days": days,
                "reason": str(reason).strip(),
                "status": "scheduled",
            },
        }
    finally:
        conn.close()


def get_suspension_requests(subscriber_id, db_path=None):
    """Return all suspension requests of one subscriber (empty list if none)."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, start_date, end_date, reason, status
            FROM suspension_requests
            WHERE subscriber_id = ?
            ORDER BY id
            """,
            (str(subscriber_id),),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def resume_connection(subscriber_id, db_path=None):
    """Resume a suspended connection, but only if the balance covers the monthly charge."""
    subscriber_id = str(subscriber_id)
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT status, balance, monthly_charge FROM connections WHERE subscriber_id = ?",
            (subscriber_id,),
        ).fetchone()

        if row is None:
            return {"ok": False, "reason": "unknown_subscriber"}
        if row["status"] != "suspended":
            return {"ok": False, "reason": "not_suspended"}
        if row["balance"] < row["monthly_charge"]:
            return {
                "ok": False,
                "reason": "insufficient_balance",
                "shortfall": row["monthly_charge"] - row["balance"],
            }

        conn.execute(
            "UPDATE connections SET status = 'active' WHERE subscriber_id = ?",
            (subscriber_id,),
        )
        conn.commit()
        return {"ok": True, "status": "active"}
    finally:
        conn.close()