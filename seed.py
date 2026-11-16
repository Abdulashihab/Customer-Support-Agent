"""
Build the demo database from the JSON data file.

Usage:
    python seed.py                      # reads data/customer_support_data.json, writes customer_support.db
    python seed.py my.json my.db

The data is validated first. If any rule fails, nothing is written.
"""
import json
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

BASE_PACK = "DSK-BASIC"
KINDS = {"primary", "secondary"}
CONNECTION_STATUSES = {"active", "suspended"}
WORK_ORDER_STATUSES = {"unscheduled", "scheduled", "completed", "cancelled"}


def validate(data):
    """Return (errors, warnings). Errors block the seed; warnings are only printed."""
    errors, warnings = [], []

    packs = {p["pack_id"]: p for p in data["packs"]}
    channels = {c["channel_no"]: c for c in data["channels"]}

    if len(packs) != len(data["packs"]):
        errors.append("Duplicate pack_id in packs")
    if len(channels) != len(data["channels"]):
        errors.append("Duplicate channel_no in channels")
    if BASE_PACK not in packs:
        errors.append(f"{BASE_PACK} is missing from packs")

    # packs -> channels
    for p in data["packs"]:
        for no in p["channel_nos"]:
            if no not in channels:
                errors.append(f"{p['pack_id']}: channel {no} does not exist")
        if len(set(p["channel_nos"])) != len(p["channel_nos"]):
            errors.append(f"{p['pack_id']}: repeated channel number")
        # informational: is the pack cheaper than buying its channels one by one?
        total = sum(channels[n]["la_carte_price"] for n in p["channel_nos"] if n in channels)
        if p["pack_id"] != BASE_PACK and total > 0 and p["price"] > total:
            warnings.append(
                f"{p['pack_id']}: pack costs {p['price']} but its channels cost "
                f"{total} a la carte (pack is {p['price'] / total:.1f}x the a la carte total)"
            )

    # subscribers
    seen_ids = set()
    by_rmn = {}
    for s in data["subscribers"]:
        sid = s["subscriber_id"]
        tag = f"{sid} ({s['name']})"

        if not re.fullmatch(r"\d{6}", sid):
            errors.append(f"{tag}: subscriber_id must be exactly 6 digits")
        if sid in seen_ids:
            errors.append(f"{tag}: duplicate subscriber_id")
        seen_ids.add(sid)

        if not re.fullmatch(r"\d{10}", s["rmn"]):
            errors.append(f"{tag}: rmn must be 10 digits")
        if s["kind"] not in KINDS:
            errors.append(f"{tag}: bad kind '{s['kind']}'")
        if s["status"] not in CONNECTION_STATUSES:
            errors.append(f"{tag}: bad status '{s['status']}'")
        try:
            date.fromisoformat(s["due_date"])
        except ValueError:
            errors.append(f"{tag}: due_date is not YYYY-MM-DD")

        if BASE_PACK not in s["packs"]:
            errors.append(f"{tag}: must have {BASE_PACK}")
        for pid in s["packs"]:
            if pid not in packs:
                errors.append(f"{tag}: unknown pack {pid}")
        if len(set(s["packs"])) != len(s["packs"]):
            errors.append(f"{tag}: same pack listed twice")

        expected = sum(packs[pid]["price"] for pid in s["packs"] if pid in packs)
        if s["monthly_charge"] != expected:
            errors.append(
                f"{tag}: monthly_charge is {s['monthly_charge']} but packs add up to {expected}"
            )

        if s["balance"] < 0:
            errors.append(f"{tag}: negative balance")

        wo = s.get("work_order")
        if wo:
            if wo["status"] not in WORK_ORDER_STATUSES:
                errors.append(f"{tag}: bad work order status '{wo['status']}'")
            slot = (wo.get("slot") or "").strip()
            if wo["status"] == "unscheduled" and slot:
                errors.append(f"{tag}: unscheduled work order must have an empty slot")
            if wo["status"] != "unscheduled" and not slot:
                errors.append(f"{tag}: {wo['status']} work order needs a slot")

        by_rmn.setdefault(s["rmn"], []).append(s)

    # one RMN = one person
    for rmn, rows in by_rmn.items():
        if len({(r["name"], r["address"]) for r in rows}) > 1:
            errors.append(f"RMN {rmn}: rows disagree on name or address")
        if sum(r["kind"] == "primary" for r in rows) != 1:
            errors.append(f"RMN {rmn}: needs exactly one primary connection")

    return errors, warnings


SCHEMA = """
DROP TABLE IF EXISTS suspension_requests;
DROP TABLE IF EXISTS work_orders;
DROP TABLE IF EXISTS connection_packs;
DROP TABLE IF EXISTS pack_channels;
DROP TABLE IF EXISTS channels;
DROP TABLE IF EXISTS packs;
DROP TABLE IF EXISTS connections;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS meta;

CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE customers (
    id      INTEGER PRIMARY KEY,
    name    TEXT NOT NULL,
    rmn     TEXT NOT NULL UNIQUE,
    address TEXT
);

CREATE TABLE connections (
    subscriber_id  TEXT PRIMARY KEY,           -- text so leading zeros survive
    customer_id    INTEGER NOT NULL REFERENCES customers(id),
    kind           TEXT NOT NULL CHECK (kind IN ('primary','secondary')),
    status         TEXT NOT NULL CHECK (status IN ('active','suspended')),
    balance        REAL NOT NULL,
    monthly_charge REAL NOT NULL,
    due_date       TEXT NOT NULL
);

CREATE TABLE packs (
    pack_id   TEXT PRIMARY KEY,
    language  TEXT,
    pack_name TEXT NOT NULL,
    category  TEXT,
    price     REAL NOT NULL
);

CREATE TABLE channels (
    channel_no    INTEGER PRIMARY KEY,
    channel_name  TEXT NOT NULL,
    language      TEXT,
    resolution    TEXT,
    genre         TEXT,
    la_carte_price REAL NOT NULL
);

CREATE TABLE pack_channels (
    pack_id    TEXT    NOT NULL REFERENCES packs(pack_id),
    channel_no INTEGER NOT NULL REFERENCES channels(channel_no),
    PRIMARY KEY (pack_id, channel_no)
);

CREATE TABLE connection_packs (
    subscriber_id TEXT NOT NULL REFERENCES connections(subscriber_id),
    pack_id       TEXT NOT NULL REFERENCES packs(pack_id),
    PRIMARY KEY (subscriber_id, pack_id)
);

CREATE TABLE suspension_requests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    subscriber_id TEXT NOT NULL REFERENCES connections(subscriber_id),
    start_date    TEXT NOT NULL,               -- YYYY-MM-DD
    end_date      TEXT NOT NULL,               -- YYYY-MM-DD
    reason        TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('scheduled','active','completed','cancelled'))
);

CREATE TABLE work_orders (
    wo_id         TEXT PRIMARY KEY,            -- WO-1001, WO-1002, ...
    subscriber_id TEXT NOT NULL REFERENCES connections(subscriber_id),
    issue_type    TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('unscheduled','scheduled','completed','cancelled')),
    slot          TEXT                         -- NULL when unscheduled
);
"""


def build(data, db_path):
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA)

    db.execute("INSERT INTO meta VALUES (?, ?)", ("reference_date", data["brand"]["reference_date"]))
    db.execute("INSERT INTO meta VALUES (?, ?)", ("brand", data["brand"]["name"]))

    db.executemany(
        "INSERT INTO packs VALUES (?,?,?,?,?)",
        [(p["pack_id"], p["language"], p["pack_name"], p["category"], p["price"]) for p in data["packs"]],
    )
    db.executemany(
        "INSERT INTO channels VALUES (?,?,?,?,?,?)",
        [
            (c["channel_no"], c["channel_name"], c["language"], c["resolution"], c["genre"], c["la_carte_price"])
            for c in data["channels"]
        ],
    )
    db.executemany(
        "INSERT INTO pack_channels VALUES (?,?)",
        [(p["pack_id"], no) for p in data["packs"] for no in p["channel_nos"]],
    )

    customer_ids = {}  # one customer row per RMN
    wo_counter = 1000
    for s in data["subscribers"]:
        if s["rmn"] not in customer_ids:
            cur = db.execute(
                "INSERT INTO customers (name, rmn, address) VALUES (?,?,?)",
                (s["name"], s["rmn"], s["address"]),
            )
            customer_ids[s["rmn"]] = cur.lastrowid

        db.execute(
            "INSERT INTO connections VALUES (?,?,?,?,?,?,?)",
            (s["subscriber_id"], customer_ids[s["rmn"]], s["kind"], s["status"],
             s["balance"], s["monthly_charge"], s["due_date"]),
        )
        db.executemany(
            "INSERT INTO connection_packs VALUES (?,?)",
            [(s["subscriber_id"], pid) for pid in s["packs"]],
        )

        wo = s.get("work_order")
        if wo:
            wo_counter += 1
            db.execute(
                "INSERT INTO work_orders VALUES (?,?,?,?,?)",
                (f"WO-{wo_counter}", s["subscriber_id"], wo["issue_type"], wo["status"],
                 (wo.get("slot") or "").strip() or None),
            )

    db.commit()
    return db


def main():
    json_path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/customer_support_data.json")
    db_path = Path(sys.argv[2] if len(sys.argv) > 2 else "customer_support.db")

    data = json.loads(json_path.read_text(encoding="utf-8"))

    errors, warnings = validate(data)
    for w in warnings:
        print("WARNING:", w)
    if errors:
        print()
        for e in errors:
            print("ERROR:", e)
        print(f"\n{len(errors)} error(s). Database not created.")
        sys.exit(1)

    db = build(data, db_path)
    counts = {
        t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in ("customers", "connections", "packs", "channels", "pack_channels", "work_orders", "suspension_requests")
    }
    db.close()
    print(f"Created {db_path}: " + ", ".join(f"{n} {t}" for t, n in counts.items()))


if __name__ == "__main__":
    main()