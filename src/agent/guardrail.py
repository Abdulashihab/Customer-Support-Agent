import re

# Each reason has a list of patterns that clearly show it.
# The reason names match the ones used by the request_callback tool.
# The order matters: the most serious reason is checked first.
TRIGGERS = {
    "legal_threat": [
        r"\bconsumer court\b",
        r"\bpolice\b",
        r"\blegal action\b",
        r"\blawyer\b",
        r"\bfile a (case|complaint)\b",
        r"\bsue\b",
    ],
    "manager_request": [
        r"\bmanager\b",
        r"\bsupervisor\b",
        r"\bescalat\w*\b",
    ],
    "charge_refusal": [
        # "can't / won't pay or give ... visit / technician / charge / 200" close together
        r"\b(can[’']?t|cannot|won[’']?t|will not|not going to|unable to)\b.{0,30}\b(pay|give)\b.{0,40}\b(visit|technician|charge|charges|200)\b",
    ],
    "angry_customer": [
        r"\bidiots?\b",
        r"\bstupid\b",
        r"\bfraud\b",
        r"\bscam\b",
        r"\bcheat\w*\b",
        r"\bshut up\b",
        r"\bnonsense\b",
    ],
}


def check_escalation(message):
    """
    Look at one customer message.

    Returns {"reason": ..., "matched": ...} if it is a clear escalation, otherwise None.
    """
    for reason, patterns in TRIGGERS.items():
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return {"reason": reason, "matched": match.group(0)}
    return None