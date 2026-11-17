from src.db.connection import get_connection


def refresh_account(subscriber_id, hard=False, db_path=None):
    """
    Send a refresh signal to the customer's set-top box.

    hard=False is a normal refresh, hard=True is a hard refresh.
    In this demo no real signal is sent. We only check the rules and say it was done.
    """
    subscriber_id = str(subscriber_id)
    conn = get_connection(db_path)
    try:
        connection = conn.execute(
            "SELECT status FROM connections WHERE subscriber_id = ?",
            (subscriber_id,),
        ).fetchone()
    finally:
        conn.close()

    if connection is None:
        return {"ok": False, "reason": "unknown_subscriber"}

    # A refresh cannot help a suspended connection.
    if connection["status"] == "suspended":
        return {"ok": False, "reason": "connection_suspended"}

    return {"ok": True, "kind": "hard" if hard else "normal"}
