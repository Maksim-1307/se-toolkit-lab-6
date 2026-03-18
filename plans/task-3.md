# Task 3 Plan

## Implementation Plan

### 1. Tool Schema (`agent/tools.json`)
Add `query_api` tool with the following schema:
- **name**: `query_api`
- **description**: Query the deployed backend API to get live data or test endpoints
- **parameters**:
  - `method` (string, required): HTTP method (GET, POST, PUT, DELETE, etc.)
  - `path` (string, required): API endpoint path (e.g., `/items/`, `/analytics/completion-rate`)
  - `body` (string, optional): JSON request body for POST/PUT requests

### 2. Tool Implementation (`agent/tools.py`)
Implement `query_api(args)` function:
- Read `LMS_API_KEY` from `.env.docker.secret` (backend auth key)
- Read `AGENT_API_BASE_URL` from env (default: `http://localhost:42002`)
- Make HTTP request using `requests` library
- Return JSON string with `status_code` and `body` fields
- Handle errors gracefully (connection errors, timeouts, HTTP errors)

### 3. Environment Variables (`agent.py`)
Update `get_env()` to load:
- `LMS_API_KEY` from `.env.docker.secret` (separate from LLM key)
- `AGENT_API_BASE_URL` with default fallback to `http://localhost:42002`

Note: Two distinct keys:
- `LLM_API_KEY` → authenticates with LLM provider (in `.env.agent.secret`)
- `LMS_API_KEY` → authenticates with backend API (in `.env.docker.secret`)

### 4. System Prompt Update
Update system prompt to guide LLM on tool selection:
- Use `read_file` / `list_files` for wiki documentation questions
- Use `read_file` for source code questions (framework, router modules, etc.)
- Use `query_api` for live data questions (item count, status codes, analytics)
- For bug diagnosis: first `query_api` to see the error, then `read_file` to find the bug

### 5. Output Format
The `query_api` tool returns:
```json
{
  "status_code": 200,
  "body": { ... response data ... }
}
```

## Expected Benchmark Failures and Fixes

| Question | Expected Issue | Fix |
|----------|----------------|-----|
| Q0-Q3 (wiki/code) | Should work with existing tools | Verify file paths are correct |
| Q4 (item count) | Agent doesn't know to use query_api | Improve system prompt |
| Q5 (status code) | Agent doesn't know to use query_api | Improve system prompt |
| Q6 (ZeroDivisionError) | Needs tool chaining + source reading | Ensure agent can chain tools |
| Q7 (TypeError) | Needs tool chaining + source reading | Ensure agent can chain tools |
| Q8 (request lifecycle) | File too large, truncated | Increase content limit or summarize |
| Q9 (ETL idempotency) | File too large, truncated | Increase content limit or summarize |

## Iteration Strategy
1. First run: Get baseline score, identify which questions fail
2. Fix query_api implementation if Q4/Q5 fail
3. Improve system prompt if wrong tools are chosen
4. For Q6-Q7: Ensure agent chains query_api → read_file
5. For Q8-Q9: May need to read files in chunks or increase limits

## Tests to Add
1. **Test query_api for item count**: Question "How many items are in the database?" → expects `query_api` tool call with GET `/items/`
2. **Test query_api for status code**: Question "What status code for /items/ without auth?" → expects `query_api` tool call, answer contains "401" or "403"

## Acceptance Criteria Checklist
- [ ] `query_api` tool schema in `tools.json`
- [ ] `query_api` function in `tools.py` with auth
- [ ] `LMS_API_KEY` loaded from `.env.docker.secret`
- [ ] `AGENT_API_BASE_URL` loaded from env (with default)
- [ ] System prompt updated for tool selection
- [ ] `run_eval.py` passes 10/10
- [ ] 2 new regression tests added
- [ ] `AGENT.md` updated (200+ words)