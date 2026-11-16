from src.db.connection import get_connection
from src.rules import minimum_recharge
BASE_PACK = "DSK-BASIC"   # every connection must keep this pack


def _recalculate_monthly_charge(conn, subscriber_id):
    """Monthly charge = base pack + all add-on packs the customer has."""
    conn.execute(
        """
        UPDATE connections
        SET monthly_charge = (
            SELECT SUM(p.price)
            FROM connection_packs cp
            JOIN packs p ON p.pack_id = cp.pack_id
            WHERE cp.subscriber_id = ?
        )
        WHERE subscriber_id = ?
        """,
        (subscriber_id, subscriber_id),
    )
    row = conn.execute(
        "SELECT monthly_charge FROM connections WHERE subscriber_id = ?",
        (subscriber_id,),
    ).fetchone()
    return row["monthly_charge"]


def add_pack(subscriber_id, pack_id, db_path=None):
    """Add a pack to a connection. Returns {"ok": True, ...} or {"ok": False, "reason": ...}."""
    subscriber_id = str(subscriber_id)
    conn = get_connection(db_path)
    try:
        connection = conn.execute(
            "SELECT status, balance, monthly_charge FROM connections WHERE subscriber_id = ?",
            (subscriber_id,),
        ).fetchone()
        if connection is None:
            return {"ok": False, "reason": "unknown_subscriber"}

        pack = conn.execute(
            "SELECT price FROM packs WHERE pack_id = ?", (pack_id,)
        ).fetchone()
        if pack is None:
            return {"ok": False, "reason": "unknown_pack"}

        if connection["status"] == "suspended":
            return {"ok": False, "reason": "connection_suspended"}

        already = conn.execute(
            "SELECT 1 FROM connection_packs WHERE subscriber_id = ? AND pack_id = ?",
            (subscriber_id, pack_id),
        ).fetchone()
        if already is not None:
            return {"ok": False, "reason": "already_subscribed"}

        # The balance must cover the NEW monthly charge.
        required = connection["monthly_charge"] + pack["price"]
        if connection["balance"] < required:
            shortfall = required - connection["balance"]
            return {
                "ok": False,
                "reason": "insufficient_balance",
                "required": required,
                "balance": connection["balance"],
                "shortfall": shortfall,
                "minimum_recharge": minimum_recharge(shortfall)
            }

        # Which channels of the new pack does the customer already get? (check BEFORE adding)
        overlap = conn.execute(
            """
            SELECT DISTINCT pc.channel_no
            FROM pack_channels pc
            WHERE pc.pack_id = ?
              AND pc.channel_no IN (
                  SELECT pc2.channel_no
                  FROM pack_channels pc2
                  JOIN connection_packs cp ON cp.pack_id = pc2.pack_id
                  WHERE cp.subscriber_id = ?
              )
            ORDER BY pc.channel_no
            """,
            (pack_id, subscriber_id),
        ).fetchall()

        conn.execute(
            "INSERT INTO connection_packs (subscriber_id, pack_id) VALUES (?, ?)",
            (subscriber_id, pack_id),
        )
        new_monthly = _recalculate_monthly_charge(conn, subscriber_id)
        conn.commit()

        return {
            "ok": True,
            "pack_added": pack_id,
            "new_monthly_charge": new_monthly,
            "overlapping_channels": [r["channel_no"] for r in overlap],
        }
    finally:
        conn.close()


def drop_pack(subscriber_id, pack_id, db_path=None):
    """Drop a pack from a connection. Returns {"ok": True, ...} or {"ok": False, "reason": ...}."""
    subscriber_id = str(subscriber_id)
    conn = get_connection(db_path)
    try:
        connection = conn.execute(
            "SELECT status FROM connections WHERE subscriber_id = ?",
            (subscriber_id,),
        ).fetchone()
        if connection is None:
            return {"ok": False, "reason": "unknown_subscriber"}

        # The base pack is mandatory.
        if pack_id == BASE_PACK:
            return {"ok": False, "reason": "base_pack_cannot_be_dropped"}

        if connection["status"] == "suspended":
            return {"ok": False, "reason": "connection_suspended"}

        owned = conn.execute(
            "SELECT 1 FROM connection_packs WHERE subscriber_id = ? AND pack_id = ?",
            (subscriber_id, pack_id),
        ).fetchone()
        if owned is None:
            return {"ok": False, "reason": "pack_not_subscribed"}

        # Channels of this pack that the customer's OTHER packs do not give.
        lost = conn.execute(
            """
            SELECT pc.channel_no
            FROM pack_channels pc
            WHERE pc.pack_id = ?
              AND pc.channel_no NOT IN (
                  SELECT pc2.channel_no
                  FROM pack_channels pc2
                  JOIN connection_packs cp ON cp.pack_id = pc2.pack_id
                  WHERE cp.subscriber_id = ? AND cp.pack_id != ?
              )
            ORDER BY pc.channel_no
            """,
            (pack_id, subscriber_id, pack_id),
        ).fetchall()
        all_channels = conn.execute(
            "SELECT channel_no FROM pack_channels WHERE pack_id = ? ORDER BY channel_no",
            (pack_id,),
        ).fetchall()
        lost_numbers = [r["channel_no"] for r in lost]
        kept_numbers = [r["channel_no"] for r in all_channels if r["channel_no"] not in lost_numbers]

        conn.execute(
            "DELETE FROM connection_packs WHERE subscriber_id = ? AND pack_id = ?",
            (subscriber_id, pack_id),
        )
        new_monthly = _recalculate_monthly_charge(conn, subscriber_id)
        conn.commit()

        return {
            "ok": True,
            "pack_dropped": pack_id,
            "new_monthly_charge": new_monthly,
            "channels_lost": lost_numbers,
            "channels_kept": kept_numbers,
        }
    finally:
        conn.close()