# Task 3 Plan

## Changes to agent.py
- Add `query_api` tool schema alongside existing tools
- Implement function: make HTTP request with `LMS_API_KEY` auth header, return `{"status_code": X, "body": ...}`
- Load `AGENT_API_BASE_URL` from env (default localhost:42002)
- Update system prompt: clarify when to use each tool (wiki vs code vs live API)

## Environment
- Already reading LLM vars from `.env.agent.secret`
- Add `LMS_API_KEY` from `.env.docker.secret`
- Add `AGENT_API_BASE_URL` (optional)

## First benchmark run
Run `uv run run_eval.py`, note failures:
- Q4 (item count) → needs query_api
- Q5 (status code) → needs query_api
- Q6-7 (bug diagnosis) → needs tool chaining
- Q8-9 (reasoning) → likely file size issues

## Iteration plan
1. Get query_api working → passes Q4, Q5
2. Fix file truncation → helps Q8, Q9
3. Test tool chaining for Q6-7
4. Tweak tool descriptions if LLM chooses wrong tool

## Tests
Add two regression tests:
- "What framework?" → expect read_file
- "How many items?" → expect query_api