# Project notes (Customer Support Agent)

## Done
- GitHub repo, folders, .gitignore
- seed.py builds customer_support.db from data/customer_support_data.json
- Tools: get_account, get_work_orders, create_work_order, request_suspension,
  get_suspension_requests, resume_connection, add_pack, drop_pack
- 42 tests passing (python -m pytest)

## Rules (already in the code)
- Suspension: start tomorrow or later, minimum 5 days (both dates count),
  balance >= 1 day burn rate (monthly charge / 30), reason required,
  one request at a time
- Base pack DSK-BASIC can never be dropped
- Work order: none if suspended, no second open one for the same issue

## Next
1. Write help documents in docs/
2. Ingest them into Chroma (search by meaning)
3. LangGraph agent
4. Login and chat screen
5. Evaluation tests, README, demo video

## How to work with Claude
- Windows, VS Code, uv. Run tests with: python -m pytest
- Explain code in very simple words, one small step at a time