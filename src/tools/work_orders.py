from src.db.connection import get_connection


def get_work_orders(subscriber_id, db_path=None):
    """Return all work orders of one subscriber as a list (empty list if none)."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT wo_id, issue_type, status, slot
            FROM work_orders
            WHERE subscriber_id = ?
            ORDER BY wo_id
            """,
            (str(subscriber_id),),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()