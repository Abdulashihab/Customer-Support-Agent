from src.db.connection import get_connection

# Problems the IT team can fix on the server.
ISSUE_TYPES = {"channel_not_visible"}

TURNAROUND = "2 hours"


def create_it_ticket(subscriber_id, issue_type, details, db_path=None):
    """
    Raise a ticket to the IT team.

    Returns {"ok": True, "ticket_id": ...} or {"ok": False, "reason": "..."}.
    """
    subscriber_id = str(subscriber_id)

    # Rule 1: the issue type must be one we know.
    if issue_type not in ISSUE_TYPES:
        return {"ok": False, "reason": "invalid_issue_type"}

    # Rule 2: the details (what was already tried) are required.
    if not details or not str(details).strip():
        return {"ok": False, "reason": "details_required"}

    conn = get_connection(db_path)
    try:
        # Rule 3: the subscriber must exist.
        connection = conn.execute(
            "SELECT status FROM connections WHERE subscriber_id = ?",
            (subscriber_id,),
        ).fetchone()
        if connection is None:
            return {"ok": False, "reason": "unknown_subscriber"}

        # Rule 4: a suspended connection needs no ticket. Explain the suspension instead.
        if connection["status"] == "suspended":
            return {"ok": False, "reason": "connection_suspended"}

        # Rule 5: no second open ticket for the same issue.
        existing = conn.execute(
            """
            SELECT ticket_id FROM it_tickets
            WHERE subscriber_id = ? AND issue_type = ? AND status = 'open'
            """,
            (subscriber_id, issue_type),
        ).fetchone()
        if existing is not None:
            return {
                "ok": False,
                "reason": "duplicate_open_ticket",
                "ticket_id": existing["ticket_id"],
                "resolved_within": TURNAROUND,
            }

        # All rules passed: make the next number (TKT-1001, TKT-1002, ...) and save.
        last = conn.execute(
            "SELECT MAX(CAST(SUBSTR(ticket_id, 5) AS INTEGER)) AS n FROM it_tickets"
        ).fetchone()["n"]
        new_id = f"TKT-{(last or 1000) + 1}"

        conn.execute(
            """
            INSERT INTO it_tickets (ticket_id, subscriber_id, issue_type, details, status)
            VALUES (?, ?, ?, ?, 'open')
            """,
            (new_id, subscriber_id, issue_type, str(details).strip()),
        )
        conn.commit()

        return {"ok": True, "ticket_id": new_id, "resolved_within": TURNAROUND}
    finally:
        conn.close()
