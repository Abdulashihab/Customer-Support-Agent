import json

from src.agent.escalation import handle_escalation
from src.agent.prompts import build_system_prompt
from src.agent.tool_runner import run_tool
from src.agent.tool_schemas import TOOL_SCHEMAS
from src.db.connection import get_connection

MAX_STEPS = 5   # the AI may use tools at most this many rounds for one message


def _get_today_text(db_path=None):
    """The company's 'today'. For this demo it is fixed in the database."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = 'reference_date'").fetchone()
    finally:
        conn.close()
    return row["value"] if row else "unknown"


def _search_docs(question):
    """Search the help documents. Imported here so tests do not need Chroma."""
    from src.rag.search import search

    cards = search(question)
    return {
        "ok": True,
        "data": [
            {"source": c["source"], "section": c["section"], "text": c["text"]}
            for c in cards
        ],
    }


def _run_one_tool(subscriber_id, call, db_path, docs_search):
    """Run one tool the AI asked for and return its result."""
    try:
        args = json.loads(call.function.arguments or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "reason": "bad_arguments"}
    if not isinstance(args, dict):
        return {"ok": False, "reason": "bad_arguments"}

    if call.function.name == "search_docs":
        return docs_search(str(args.get("question", "")))
    return run_tool(subscriber_id, call.function.name, args, db_path=db_path)


def chat_turn(subscriber_id, history, user_message, client=None, model=None,
              db_path=None, docs_search=None):
    """
    One customer message in, one reply out.

    history is the list of earlier messages. This function adds the new ones to it.
    """
    # Step 1: the guardrail goes first. Clear escalations never reach the AI.
    escalation = handle_escalation(subscriber_id, user_message, db_path=db_path)
    if escalation is not None:
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": escalation["reply"]})
        return escalation["reply"]

    if client is None:
        from src.agent.llm import get_client, get_model_name

        client, model = get_client(), get_model_name()
    docs_search = docs_search or _search_docs

    # Step 2: build the conversation for the AI.
    messages = [{"role": "system", "content": build_system_prompt(_get_today_text(db_path))}]
    messages += history
    messages.append({"role": "user", "content": user_message})

    # Step 3: let the AI think and use tools, round by round.
    for _ in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=model, messages=messages, tools=TOOL_SCHEMAS
        )
        message = response.choices[0].message

        if not message.tool_calls:          # no tool needed: this is the final answer
            reply = message.content or ""
            break

        # keep the AI's request in the conversation
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for call in message.tool_calls
            ],
        })

        # run each tool and give the result back to the AI
        for call in message.tool_calls:
            result = _run_one_tool(subscriber_id, call, db_path, docs_search)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, default=str),
            })
    else:
        reply = "Sorry, I could not finish that. Please try again."

    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    return reply