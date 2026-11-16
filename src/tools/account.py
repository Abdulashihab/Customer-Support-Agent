from src.db.connection import get_connection


def get_account(subscriber_id, db_path=None):
    """Return one subscriber's account details, or None if the ID does not exist."""
    subscriber_id = str(subscriber_id)
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT k.subscriber_id, k.kind, k.status, k.balance,
                   k.monthly_charge, k.due_date,
                   c.name, c.rmn, c.address
            FROM connections k
            JOIN customers c ON c.id = k.customer_id
            WHERE k.subscriber_id = ?
            """,
            (subscriber_id,),
        ).fetchone()

        if row is None:
            return None

        packs = conn.execute(
            """
            SELECT p.pack_id, p.pack_name, p.price
            FROM connection_packs cp
            JOIN packs p ON p.pack_id = cp.pack_id
            WHERE cp.subscriber_id = ?
            ORDER BY p.pack_id
            """,
            (subscriber_id,),
        ).fetchall()

        account = dict(row)
        account["packs"] = [dict(p) for p in packs]
        return account
    finally:
        conn.close()