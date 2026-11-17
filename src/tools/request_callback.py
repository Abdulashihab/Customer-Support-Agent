from src.db.connection import get_connection

# Why a customer might need a supervisor callback.
CALLBACK_REASONS = {
    "manager_request",   # customer asks for a manager or supervisor
    "angry_customer",    # customer is angry or abusive
    "charge_refusal",    # customer will not pay the visit charge
    "legal_threat",      # customer mentions consumer court, police, a case
    "unknown_error",     # an error message the documents do not cover
}

CALL_WITHIN = "15 to 30 minutes"


def request_callback(subscriber_id, reason, summary, db_path=None):
    """
    Save a callback request for a supervisor.

    Returns {"ok": True, "request_id": ...} or {"ok": False, "reason": "..."}.
    """
    subscriber_id = str(subscriber_id)

    # Rule 1: the reason must be one we know.
    if reason not in CALLBACK_REASONS:
        return {"ok": False, "reason": "invalid_reason"}

    # Rule 2: a short summary is needed, so the customer does not have to repeat the problem.
    if not summary or not str(summary).strip():
        return {"ok": False, "reason": "summary_required"}

    conn = get_connection(db_path)
    try:
        # Rule 3: the subscriber must exist. We also need the number to call.
        customer = conn.execute(
            """
            SELECT c.rmn
            FROM connections k
            JOIN customers c ON c.id = k.customer_id
            WHERE k.subscriber_id = ?
            """,
            (subscriber_id,),
        ).fetchone()
        if customer is None:
            return {"ok": False, "reason": "unknown_subscriber"}

        # Rule 4: only one open callback request per customer.
        existing = conn.execute(
            "SELECT request_id FROM callback_requests WHERE subscriber_id = ? AND status = 'open'",
            (subscriber_id,),
        ).fetchone()
        if existing is not None:
            return {
                "ok": False,
                "reason": "callback_already_requested",
                "request_id": existing["request_id"],
                "call_within": CALL_WITHIN,
            }

        # All rules passed: make the next number (CB-1001, CB-1002, ...) and save.
        last = conn.execute(
            "SELECT MAX(CAST(SUBSTR(request_id, 4) AS INTEGER)) AS n FROM callback_requests"
        ).fetchone()["n"]
        new_id = f"CB-{(last or 1000) + 1}"

        conn.execute(
            """
            INSERT INTO callback_requests (request_id, subscriber_id, reason, summary, status)
            VALUES (?, ?, ?, ?, 'open')
            """,
            (new_id, subscriber_id, reason, str(summary).strip()),
        )
        conn.commit()

        return {
            "ok": True,
            "request_id": new_id,
            "phone": customer["rmn"],
            "call_within": CALL_WITHIN,
        }
    finally:
        conn.close()
