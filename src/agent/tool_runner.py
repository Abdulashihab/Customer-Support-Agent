import inspect

from src.tools.account import get_account
from src.tools.create_work_order import create_work_order
from src.tools.create_it_ticket import create_it_ticket
from src.tools.packs import add_pack, drop_pack
from src.tools.refresh_account import refresh_account
from src.tools.request_callback import request_callback
from src.tools.suspension import (
    get_suspension_requests,
    request_suspension,
    resume_connection,
)
from src.tools.work_orders import get_work_orders

# Tools that only READ data. Their result is wrapped as {"ok": True, "data": ...}.
READ_TOOLS = {
    "get_account": get_account,
    "get_work_orders": get_work_orders,
    "get_suspension_requests": get_suspension_requests,
}

# Tools that CHANGE data. They already return {"ok": ...} themselves.
ACTION_TOOLS = {
    "create_work_order": create_work_order,
    "request_suspension": request_suspension,
    "resume_connection": resume_connection,
    "add_pack": add_pack,
    "drop_pack": drop_pack,
    "refresh_account": refresh_account,
    "create_it_ticket": create_it_ticket,
    "request_callback": request_callback,
}


def run_tool(session_subscriber_id, tool_name, args=None, db_path=None):
    """
    Run one tool for the logged-in customer.

    The subscriber ID always comes from the login session (session_subscriber_id).
    If the AI or the customer sends another subscriber_id, it is thrown away.
    """
    args = dict(args or {})
    args.pop("subscriber_id", None)   # never trust this from outside
    args.pop("db_path", None)         # the AI must not choose the database either

    if tool_name in READ_TOOLS:
        function, is_read = READ_TOOLS[tool_name], True
    elif tool_name in ACTION_TOOLS:
        function, is_read = ACTION_TOOLS[tool_name], False
    else:
        return {"ok": False, "reason": "unknown_tool"}

    # Check the arguments fit the tool BEFORE running it.
    try:
        inspect.signature(function).bind(
            subscriber_id=session_subscriber_id, db_path=db_path, **args
        )
    except TypeError:
        return {"ok": False, "reason": "bad_arguments"}

    result = function(subscriber_id=session_subscriber_id, db_path=db_path, **args)

    if is_read:
        if result is None:
            return {"ok": False, "reason": "unknown_subscriber"}
        return {"ok": True, "data": result}
    return result