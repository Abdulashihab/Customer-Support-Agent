from evaluation.conversation_eval import pack_ids, run_scenario, said
from fake_ai import FakeClient, text_answer, tool_answer


def test_scenario_passes_when_the_reply_has_the_right_words(db_copy):
    scenario = {
        "name": "balance",
        "subscriber": "100003",
        "messages": ["What is my balance?"],
        "check": lambda replies, db: said(replies, "850"),
    }
    client = FakeClient([text_answer("Your balance is 850 rupees.")])
    ok, replies = run_scenario(scenario, client, "x", db_copy)
    assert ok is True


def test_scenario_fails_when_the_reply_is_wrong(db_copy):
    scenario = {
        "name": "balance",
        "subscriber": "100003",
        "messages": ["What is my balance?"],
        "check": lambda replies, db: said(replies, "850"),
    }
    client = FakeClient([text_answer("I do not know.")])
    ok, replies = run_scenario(scenario, client, "x", db_copy)
    assert ok is False


def test_scenario_runs_on_a_copy_of_the_database(db_copy):
    scenario = {
        "name": "add pack",
        "subscriber": "100003",
        "messages": ["Please add DSK-TLK1", "Yes"],
        "check": lambda replies, db: "DSK-TLK1" in pack_ids(db, "100003"),
    }
    client = FakeClient([
        text_answer("Shall I add it?"),
        tool_answer("add_pack", {"pack_id": "DSK-TLK1"}),
        text_answer("Added."),
    ])
    ok, _ = run_scenario(scenario, client, "x", db_copy)
    assert ok is True                                      # the copy has the new pack
    assert "DSK-TLK1" not in pack_ids(db_copy, "100003")   # the original does not