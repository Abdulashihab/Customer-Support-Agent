from src.agent.guardrail import check_escalation


def reason_of(message):
    result = check_escalation(message)
    return result["reason"] if result else None


def test_manager_request():
    assert reason_of("I want to talk to your manager") == "manager_request"


def test_legal_threat_comes_first():
    # both a manager and the police are mentioned, the legal threat is more serious
    assert reason_of("Call your manager or I will call the police") == "legal_threat"


def test_refusing_the_visit_charge():
    assert reason_of("I can't give 200 rupees for the technician visit") == "charge_refusal"


def test_abusive_words():
    assert reason_of("You are all idiots") == "angry_customer"
    assert reason_of("this is a scam") == "angry_customer"


def test_normal_messages_are_not_escalations():
    for message in [
        "my TV shows nothing",
        "the signal is terrible",
        "I can't pay now, I will recharge tomorrow",
        "Please add the sports pack",
    ]:
        assert check_escalation(message) is None