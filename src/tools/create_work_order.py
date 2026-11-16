from src.db.connection import get_connection

# The kinds of technician visits this company offers.
ALLOWED_ISSUE_TYPES = {"no_signal", "stb_upgrade", "dish_alignment", "remote_replacement"}


def create_work_order(subscriber_id, issue_type, db_path=None):
    """
    Try to create a new work order (technician visit request).

    Always returns a dictionary:
      success -> {"ok": True, "work_order": {...}}
      refused -> {"ok": False, "reason": "..."}
    """
    subscriber_id = str(subscriber_id)

    # Rule 1: the issue type must be one we know.
    if issue_type not in ALLOWED_ISSUE_TYPES:
        return {"ok": False, "reason": "invalid_issue_type"}

    conn = get_connection(db_path)
    try:
        # Rule 2: the subscriber must exist.
        connection = conn.execute(
            "SELECT status FROM connections WHERE subscriber_id = ?",
            (subscriber_id,),
        ).fetchone()
        if connection is None:
            return {"ok": False, "reason": "unknown_subscriber"}

        # Rule 3: a suspended connection cannot get a new work order.
        if connection["status"] == "suspended":
            return {"ok": False, "reason": "connection_suspended"}

        # Rule 4: no second open work order for the same issue.
        open_order = conn.execute(
            """
            SELECT wo_id FROM work_orders
            WHERE subscriber_id = ?
              AND issue_type = ?
              AND status IN ('unscheduled', 'scheduled')
            """,
            (subscriber_id, issue_type),
        ).fetchone()
        if open_order is not None:
            return {
                "ok": False,
                "reason": "duplicate_open_work_order",
                "wo_id": open_order["wo_id"],
            }

        # All rules passed: make the next number (WO-1005, WO-1006, ...).
        last = conn.execute(
            "SELECT MAX(CAST(SUBSTR(wo_id, 4) AS INTEGER)) AS n FROM work_orders"
        ).fetchone()["n"]
        new_id = f"WO-{(last or 1000) + 1}"

        conn.execute(
            """
            INSERT INTO work_orders (wo_id, subscriber_id, issue_type, status, slot)
            VALUES (?, ?, ?, 'unscheduled', NULL)
            """,
            (new_id, subscriber_id, issue_type),
        )
        conn.commit()

        return {
            "ok": True,
            "work_order": {
                "wo_id": new_id,
                "issue_type": issue_type,
                "status": "unscheduled",
                "slot": None,
            },
        }
    finally:
        conn.close()