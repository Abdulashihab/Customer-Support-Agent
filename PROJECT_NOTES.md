# Project notes (Customer Support Agent)

## Done
- Database from JSON (seed.py), tools with business rules, help documents, document search (Chroma)
- Guardrail, callback requests, IT tickets, safe tool runner
- AI connection through OpenRouter, agent loop, LangGraph flow
- Login with one-time code, Streamlit chat screen
- One-command start (python start.py)
- About 90 tests with a fake AI
- Evaluation: guardrail set (21 of 24) and 14 conversation scenarios
- README with diagram, interview notes and demo script in notes/

## Rules (already in the code)
- Suspension: start tomorrow or later, minimum 5 days, balance >= 1 day burn rate, reason required
- Resume: set-top box on, balance >= 1 day burn rate
- Minimum recharge 200 everywhere: max(missing amount, 200)
- Base pack DSK-BASIC can never be dropped
- Work order: none if suspended, no second open one for the same issue
- Callback request: one open per customer, supervisor calls within 15 to 30 minutes
- IT ticket (error 3 / error 5 after refresh and hard refresh): 2 hour turnaround
- No live human handoff: escalations become callback requests

## Next
1. Run the real conversation evaluation once and study the failures
2. Record the demo video (notes/DEMO_SCRIPT.md)
3. Practise the interview notes (notes/INTERVIEW_NOTES.md)
4. Optional: second guardrail layer, public demo

## How to work with Claude
- Windows, VS Code, uv. Run tests with: python -m pytest
- Explain code in very simple words, one small step at a time
- Send whole files to replace, not separate edits