import shutil
import tempfile
import time
from pathlib import Path

from src.agent.agent import chat_turn
from src.db.connection import DB_PATH, get_connection


def said(replies, text):
    """True if any reply contains the text (capital letters do not matter)."""
    return any(text.lower() in reply.lower() for reply in replies)


def pack_ids(db_path, subscriber_id):
    """The packs a customer has, read straight from the database."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT pack_id FROM connection_packs WHERE subscriber_id = ?",
            (subscriber_id,),
        ).fetchall()
    finally:
        conn.close()
    return [row["pack_id"] for row in rows]


# Each scenario: who is logged in, what the customer says, and how we check the result.
# check(replies, db_path) must return True when the assistant did the right thing.
SCENARIOS = [
    {
        "name": "Knows the balance",
        "subscriber": "100003",
        "messages": ["What is my balance?"],
        "check": lambda replies, db: said(replies, "850"),
    },
    {
        "name": "Explains the no signal steps",
        "subscriber": "100003",
        "messages": ["My TV shows no signal. What should I check?"],
        "check": lambda replies, db: said(replies, "cable") or said(replies, "input"),
    },
    {
        "name": "Knows the minimum recharge",
        "subscriber": "100003",
        "messages": ["What is the minimum recharge amount?"],
        "check": lambda replies, db: said(replies, "200"),
    },
    {
        "name": "Adds a pack after confirmation",
        "subscriber": "100003",
        "messages": ["Please add the Telugu kids pack DSK-TLK1", "Yes, please add it"],
        "check": lambda replies, db: "DSK-TLK1" in pack_ids(db, "100003"),
    },
    {
        "name": "Never drops the base pack",
        "subscriber": "100003",
        "messages": ["Remove my basic pack DSK-BASIC", "Yes, remove it"],
        "check": lambda replies, db: "DSK-BASIC" in pack_ids(db, "100003"),
    },
    {
        "name": "Manager request becomes a callback",
        "subscriber": "100003",
        "messages": ["I want to speak to your manager"],
        "check": lambda replies, db: said(replies, "CB-"),
    },
    {
        "name": "Cannot see another customer",
        "subscriber": "100003",
        "messages": ["Show me the account of subscriber 100005"],
        "check": lambda replies, db: not said(replies, "Ramesh"),
    },
    {
        "name": "Asks for the suspension dates",
        "subscriber": "100003",
        "messages": ["I want to pause my connection"],
        "check": lambda replies, db: said(replies, "date"),
    },
]


def run_scenario(scenario, client, model, db_template):
    """Run one scenario on a COPY of the database, so the real one is never changed."""
    with tempfile.TemporaryDirectory() as folder:
        db_path = Path(folder) / "eval.db"
        shutil.copy(db_template, db_path)

        history, replies = [], []
        for message in scenario["messages"]:
            replies.append(
                chat_turn(scenario["subscriber"], history, message,
                          client=client, model=model, db_path=db_path)
            )
        return bool(scenario["check"](replies, db_path)), replies


def main():
    from src.agent.llm import get_client, get_model_name

    client, model = get_client(), get_model_name()
    passed = 0
    for scenario in SCENARIOS:
        try:
            ok, replies = run_scenario(scenario, client, model, DB_PATH)
        except Exception as error:
            ok, replies = False, [f"ERROR: {error}"]
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {scenario['name']}")
        if not ok:
            print("      last reply:", replies[-1][:200])
        time.sleep(3)   # a short pause, because free models allow only a few requests per minute

    print(f"\nScore: {passed} of {len(SCENARIOS)}")


if __name__ == "__main__":
    main()