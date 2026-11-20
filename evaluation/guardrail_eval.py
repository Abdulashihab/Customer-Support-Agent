from src.agent.guardrail import check_escalation

# (customer message, what the guardrail SHOULD answer)
# The answer is a reason, or None when the bot should carry on normally.
CASES = [
    # --- should escalate ---
    ("I want to talk to your manager", "manager_request"),
    ("Give me your supervisor right now", "manager_request"),
    ("I want to escalate this", "manager_request"),
    ("get me someone senior", "manager_request"),
    ("I will go to consumer court", "legal_threat"),
    ("I will go to consumer cort", "legal_threat"),
    ("I am calling the police", "legal_threat"),
    ("I will file a case against your company", "legal_threat"),
    ("my lawyer will contact you", "legal_threat"),
    ("I can't give 200 rupees for the technician visit", "charge_refusal"),
    ("I will not pay any visit charge", "charge_refusal"),
    ("why should I pay for a technician, I won't pay", "charge_refusal"),
    ("you people are idiots", "angry_customer"),
    ("this is a complete scam", "angry_customer"),
    ("shut up and fix my TV", "angry_customer"),
    ("you are cheating customers", "angry_customer"),
    # --- should NOT escalate ---
    ("my TV shows nothing", None),
    ("the signal is terrible", None),
    ("bad signal since morning", None),
    ("I can't pay now, I will recharge tomorrow", None),
    ("please add the sports pack", None),
    ("what is the minimum recharge", None),
    ("I want to pause my connection for a week", None),
    ("my technician has not come yet", None),
]


def run():
    wrong = []
    for message, expected in CASES:
        found = check_escalation(message)
        actual = found["reason"] if found else None
        if actual != expected:
            wrong.append((message, expected, actual))

    total = len(CASES)
    right = total - len(wrong)
    print(f"Correct: {right} of {total} ({right / total:.0%})\n")
    for message, expected, actual in wrong:
        print(f"WRONG: {message!r}")
        print(f"       expected {expected}, got {actual}\n")


if __name__ == "__main__":
    run()