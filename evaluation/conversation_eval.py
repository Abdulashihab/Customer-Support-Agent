import shutil
import sys
import tempfile
import time
from pathlib import Path

from src.agent.agent import chat_turn
from src.db.connection import DB_PATH, get_connection

RESULTS_FILE = Path(__file__).resolve().parent / "last_run.md"


def said(replies, text):
    """True if any reply contains the text (capital letters do not matter)."""
    return any(text.lower() in reply.lower() for reply in replies)


def scalar(db_path, sql, params=()):
    """Ask the database one question and return the first value of the answer."""
    conn = get_connection(db_path)
    try:
        return conn.execute(sql, params).fetchone()[0]
    finally:
        conn.close()


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
    {
        "name": "Tells when the technician comes",
        "subscriber": "100006",
        "messages": ["When is my technician coming?"],
        "check": lambda replies, db: said(replies, "16") and said(replies, "10"),
    },
    {
        "name": "Knows the minimum suspension period",
        "subscriber": "100003",
        "messages": ["What is the minimum period for a temporary suspension?"],
        "check": lambda replies, db: said(replies, "5"),
    },
    {
        "name": "A 3 day suspension is not saved",
        "subscriber": "100003",
        "messages": [
            "I want to pause my connection from 2026-11-15 to 2026-11-17 because I am travelling",
            "Yes, please do it",
        ],
        "check": lambda replies, db: scalar(
            db, "SELECT COUNT(*) FROM suspension_requests WHERE subscriber_id = '100003'") == 0,
    },
    {
        "name": "Cannot resume with no balance",
        "subscriber": "100005",
        "messages": ["Please resume my connection. My set-top box is on."],
        "check": lambda replies, db: scalar(
            db, "SELECT status FROM connections WHERE subscriber_id = '100005'") == "suspended",
    },
    {
        "name": "Legal threat becomes a callback",
        "subscriber": "100003",
        "messages": ["I will go to consumer court"],
        "check": lambda replies, db: said(replies, "CB-"),
    },
    {
        "name": "No technician for a suspended account",
        "subscriber": "100005",
        "messages": ["Please send a technician, my TV shows no signal", "Yes, create it"],
        "check": lambda replies, db: scalar(
            db, "SELECT COUNT(*) FROM work_orders WHERE subscriber_id = '100005'") == 0,
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


def write_results(model, results):
    """Save the score in a small file, so it can be shown on GitHub."""
    passed = sum(1 for _, ok in results if ok)
    lines = [
        "# Last conversation evaluation run",
        "",
        f"Date: {time.strftime('%Y-%m-%d')}",
        f"Model: {model}",
        f"Score: {passed} of {len(results)}",
        "",
        "| Scenario | Result |",
        "|---|---|",
    ]
    for name, ok in results:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} |")
    RESULTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    from src.agent.llm import get_client, get_model_name

    # "python -m evaluation.conversation_eval 4 5" runs only scenarios 4 and 5.
    numbers = [int(arg) for arg in sys.argv[1:]] or list(range(1, len(SCENARIOS) + 1))
    client, model = get_client(), get_model_name()

    results = []
    for number in numbers:
        scenario = SCENARIOS[number - 1]
        try:
            ok, replies = run_scenario(scenario, client, model, DB_PATH)
        except Exception as error:
            ok, replies = False, [f"ERROR: {error}"]
        results.append((scenario["name"], ok))
        print(f"{'PASS' if ok else 'FAIL'}  {number}. {scenario['name']}")
        if not ok:
            print("      last reply:", replies[-1][:200])
        time.sleep(3)   # a short pause, because free models allow only a few requests per minute

    passed = sum(1 for _, ok in results if ok)
    print(f"\nScore: {passed} of {len(results)}")
    if len(numbers) == len(SCENARIOS):
        write_results(model, results)
        print(f"Saved in {RESULTS_FILE.name}")


if __name__ == "__main__":
    main()