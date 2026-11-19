from src.agent.guardrail import check_escalation
from src.tools.request_callback import request_callback

ESCALATION_REPLY = (
    "I understand, and I am sorry for the trouble. I have noted your request, "
    "number {request_id}. A supervisor will call you on your registered mobile number "
    "within {call_within}. I have shared the details, so you will not need to explain again."
)

CHARGE_REPLY = (
    "I am not able to change charges in this chat, but I have noted your concern "
    "for the supervisor. Your request number is {request_id}. A supervisor will call you "
    "on your registered mobile number within {call_within}."
)

FAILED_REPLY = "I am sorry, I could not take your request right now. Please try again in a few minutes."


def handle_escalation(subscriber_id, message, db_path=None):
    """
    If the message is a clear escalation, take a callback request.

    Returns {"reason": ..., "reply": ...}, or None if the message is normal.
    """
    found = check_escalation(message)
    if found is None:
        return None

    summary = f"Customer wrote: {message.strip()[:300]}"
    result = request_callback(subscriber_id, found["reason"], summary, db_path=db_path)

    # A callback that is already open is fine: we just give the same number again.
    if result["ok"] or result["reason"] == "callback_already_requested":
        template = CHARGE_REPLY if found["reason"] == "charge_refusal" else ESCALATION_REPLY
        reply = template.format(
            request_id=result["request_id"], call_within=result["call_within"]
        )
    else:
        reply = FAILED_REPLY

    return {"reason": found["reason"], "reply": reply}