from src.tools.create_work_order import ALLOWED_ISSUE_TYPES
from src.tools.create_it_ticket import ISSUE_TYPES as IT_ISSUE_TYPES
from src.tools.request_callback import CALLBACK_REASONS


def _tool(name, description, properties=None, required=None):
    """Describe one tool to the AI model."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties or {},
                "required": required or [],
            },
        },
    }


# NOTE: no tool asks for a subscriber ID. The customer is already logged in,
# and the runner adds the ID from the login session.
TOOL_SCHEMAS = [
    _tool(
        "search_docs",
        "Search the help documents. Use it for how-to questions, rules and what to tell the customer.",
        {"question": {"type": "string", "description": "The question to search for"}},
        ["question"],
    ),
    _tool("get_account", "Get the customer's balance, monthly charge, due date, status and packs."),
    _tool("get_work_orders", "Get the customer's technician visits (work orders) and their status."),
    _tool("get_suspension_requests", "Get the customer's temporary suspension requests."),
    _tool(
        "create_work_order",
        "Request a technician visit. Only after the customer confirms.",
        {"issue_type": {"type": "string", "enum": sorted(ALLOWED_ISSUE_TYPES)}},
        ["issue_type"],
    ),
    _tool(
        "request_suspension",
        "Request a temporary suspension. Needs a reason and dates. Only after the customer confirms.",
        {
            "reason": {"type": "string", "description": "Why the customer wants the suspension"},
            "start_date": {"type": "string", "description": "YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "YYYY-MM-DD"},
        },
        ["reason", "start_date", "end_date"],
    ),
    _tool(
        "resume_connection",
        "Resume a suspended connection. Ask the customer if the set-top box is on first.",
        {"box_is_on": {"type": "boolean", "description": "True if the customer says the set-top box is on"}},
        ["box_is_on"],
    ),
    _tool(
        "add_pack",
        "Add a pack to the customer's connection. Only after the customer confirms.",
        {"pack_id": {"type": "string", "description": "For example DSK-TLK1"}},
        ["pack_id"],
    ),
    _tool(
        "drop_pack",
        "Drop a pack from the customer's connection. Only after the customer confirms.",
        {"pack_id": {"type": "string", "description": "For example DSK-TMK2"}},
        ["pack_id"],
    ),
    _tool(
        "refresh_account",
        "Send a refresh to the set-top box. Use hard=true for a hard refresh.",
        {"hard": {"type": "boolean", "description": "False for a normal refresh, true for a hard refresh"}},
    ),
    _tool(
        "create_it_ticket",
        "Raise an IT ticket after a normal refresh and a hard refresh did not fix the problem.",
        {
            "issue_type": {"type": "string", "enum": sorted(IT_ISSUE_TYPES)},
            "details": {"type": "string", "description": "What was tried, for the IT team"},
        },
        ["issue_type", "details"],
    ),
    _tool(
        "request_callback",
        "Save a callback request for a supervisor when the customer is upset or the problem is not covered.",
        {
            "reason": {"type": "string", "enum": sorted(CALLBACK_REASONS)},
            "summary": {"type": "string", "description": "Short summary of the case"},
        },
        ["reason", "summary"],
    ),
]