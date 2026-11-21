# Customer Support Agent

An agentic RAG customer support assistant for a fictional DTH company.
Customers log in with their registered mobile number, chat in plain language,
and the assistant answers from help documents, reads their account, troubleshoots,
and changes things only after confirmation.

> The company, customers, packs and prices are all fictional. This is a learning project.

## How it works
```mermaid
flowchart TD
    A[Customer message] --> B{Guardrail}
    B -->|clear escalation| C[Save callback request]
    C --> D[Reply with request number]
    B -->|normal message| E[AI agent]
    E -->|needs a tool| F[Tool runner]
    F -->|result| E
    E --> G[Reply to customer]
```

## What works
- A database built from a JSON file (customers, connections, packs, channels, work orders, and more)
- Tools that read and change the data, each with its business rules in code:
  account lookup, work orders, temporary suspension and resume, add and drop packs,
  callback requests, IT tickets, account refresh
- Help documents in `docs/`, split into chunks and searched by meaning (Chroma, stored locally)
- A guardrail that sends clear escalations (manager, legal threats, abuse, refused charges)
  to a callback request, without using the AI
- An agent loop where an AI model (through OpenRouter) uses the tools, with the logged-in
  customer's ID set by the code, never chosen by the AI
- The same flow as a LangGraph graph (guardrail node, then agent node)
- Login with a one-time code (demo: shown on screen) and a Streamlit chat screen
- 90 automated tests (`python -m pytest`), using a fake AI so no requests are spent
- Evaluation: the guardrail (`python -m evaluation.guardrail_eval`) and 14 full conversations
  with the real AI (`python -m evaluation.conversation_eval`, score saved in `evaluation/last_run.md`)

## Run it
```
uv sync                  # installs the packages
python start.py          # builds the database and the document search if needed, then opens the chat screen
```
Create a `.env` file first (never upload it):
```
OPENROUTER_API_KEY=your-key
OPENROUTER_MODEL=a-free-model-that-supports-tools
```
`python list_free_models.py` lists free models that support tool calling.
Other commands: `python -m pytest`, `python chat_cli.py` (chat in the terminal), `python seed.py` (reset the data).

## Design decisions
- **Rules live in code, not in the AI prompt.** The AI can ask a tool to do something, but the tool refuses if a rule is broken.
- **The subscriber ID comes from the login session**, never from the text a customer types or from the AI.
- **No live human handoff.** Angry customers, manager requests, refused charges and legal threats become a callback request, and a supervisor calls back within 15 to 30 minutes.
- **Minimum recharge is 200 rupees**, and a recharge is never less than the missing amount.
- **Tests use a fake AI**, so they are fast, free and repeatable. The real AI is checked separately by the conversation evaluation.
- **Local vector search.** Chroma runs on the computer and needs no account. `chroma_db/` is generated automatically and is not uploaded.
- **The one-time code is shown on screen only in this demo.** A real app would send it by SMS.
- Every tool returns a clear result (`ok` plus a reason), so the assistant can explain refusals politely.

## Limits
The free AI models allow only a limited number of requests per day and vary in quality, so results can differ between runs.

## Next
A second guardrail layer where the AI judges the customer's tone, a public demo, and a short demo video.