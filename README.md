# Customer Support Agent

An agentic RAG customer support assistant for a fictional DTH company.
Customers will log in with their registered mobile number, chat in plain language,
and the assistant answers from help documents, reads their account, troubleshoots,
and changes things only after confirmation.

> The company, customers, packs and prices are all fictional. This is a learning project.

## What works so far
- A database built from a JSON file (customers, connections, packs, channels, work orders, and more)
- Tools that read and change the data, each with its business rules in code:
  account lookup, work orders, temporary suspension and resume, add and drop packs,
  callback requests, IT tickets, account refresh
- Help documents for the knowledge base in `docs/`
- 57 automated tests (`python -m pytest`)

## Coming next
- Document search (RAG) over the help documents
- A LangGraph agent with a router, guardrails and callback escalation
- Login with mobile number and OTP, and a chat screen
- An evaluation set of full customer conversations

## How to run
```
python seed.py        # builds customer_support.db from data/customer_support_data.json
python -m pytest      # runs all tests
```

## Design decisions
- **Rules live in code, not in the AI prompt.** The AI can ask a tool to do something, but the tool refuses if a rule is broken.
- **The subscriber ID will come from the login session**, never from the text a customer types.
- **No live human handoff.** Angry customers, manager requests, refused charges and legal threats become a callback request, and a supervisor calls back within 15 to 30 minutes.
- **Minimum recharge is 200 rupees**, and a recharge is never less than the missing amount.
- Every tool returns a clear result (`ok` plus a reason), so the assistant can explain refusals politely.
