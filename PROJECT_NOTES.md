# Project notes (Customer Support Agent)

## Done
- GitHub repo, folders, .gitignore
- seed.py builds customer_support.db from data/customer_support_data.json
- Tools: get_account, get_work_orders, create_work_order, request_suspension,
  get_suspension_requests, resume_connection, add_pack, drop_pack,
  request_callback, create_it_ticket, refresh_account
- Shared rules in src/rules.py (minimum recharge)
- Help documents in docs/: temporary-suspension, add-drop-packs, work-orders,
  recharge, no-signal, channel-not-visible, escalation
- 57 tests passing (python -m pytest)

## Rules (already in the code)
- Suspension: start tomorrow or later, minimum 5 days (both dates count),
  balance >= 1 day burn rate (monthly charge / 30), reason required, one request at a time
- Resume: set-top box must be on, balance >= 1 day burn rate (not the full monthly charge)
- Minimum recharge is 200 everywhere: recharge needed = max(missing amount, 200)
- Base pack DSK-BASIC can never be dropped
- Work order: none if suspended, no second open one for the same issue
- Callback request: one open per customer, supervisor calls within 15 to 30 minutes
- IT ticket (error 3 / error 5 after refresh and hard refresh): 2 hour turnaround
- No live human handoff: escalations become callback requests

## Next
1. Install packages for the agent (chromadb, sentence-transformers, langgraph, fastapi, streamlit)
2. Ingest docs into Chroma (search by meaning)
3. LangGraph agent with guardrails
4. Login and chat screen
5. Evaluation tests, README with diagrams, demo video

## How to work with Claude
- Windows, VS Code, uv. Run tests with: python -m pytest
- Explain code in very simple words, one small step at a time
- Send whole files to replace, not separate edits
