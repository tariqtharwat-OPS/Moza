# INVESTIGATION REPORT: Dummy Payload `{"action":"demo","path":"."}`

## Executive Summary
Clicking "Create a file" or "Research a topic" in the Workspace UI triggers ALL three tools (filesystem, terminal, browser) with the identical dummy payload `{"action":"demo","path":"."}`. This is NOT an LLM hallucination or a parsing error — it is a **hardcoded default in the MockAgent**.

---

## 1. Flow Trace (Actual Log Output)

### Test 1: Input = "Create a file"

```
Total events: 12

  [0] orchestrator -> AGENT_STARTED                description: "Create a file"
  [1] mock_agent -> agent_thinking                 Analyzing task: Create a file
  [2] mock_agent -> agent_thinking                 I have the context. Breaking down the problem...
  [3] mock_agent -> tool_selected                  Available tools: filesystem, terminal, browser
  [4] mock_agent -> TOOL_CALL                      tool: filesystem  args: {"action": "demo", "path": "."}
  [5] mock_agent -> TOOL_RESULT                    tool: filesystem  success: False
  [6] mock_agent -> TOOL_CALL                      tool: terminal    args: {"action": "demo", "path": "."}
  [7] mock_agent -> TOOL_RESULT                    tool: terminal    success: False
  [8] mock_agent -> TOOL_CALL                      tool: browser     args: {"action": "demo", "path": "."}
  [9] mock_agent -> TOOL_RESULT                    tool: browser     success: False
 [10] mock_agent -> llm_finished                   Task completed! Analyzed: 'Create a file'...
 [11] orchestrator -> TASK_COMPLETED
```

**Key observation:** The `source` field on EVERY tool_call and tool_result event is `mock_agent`.

### Test 2: Input = Arabic greeting (proving intent classifier works)

```
Total events: 5
  [0] orchestrator -> agent_started
  [1] orchestrator -> agent_thinking               Conversational intent detected. Responding directly.
  [2] orchestrator -> llm_token                     [Arabic response]
  [3] orchestrator -> llm_finished                  [Arabic response]
  [4] orchestrator -> TASK_COMPLETED
```

**Key observation:** Source is `orchestrator`, NOT `mock_agent`. Zero tool calls. This proves the intent classifier in `_run_agent()` correctly intercepts conversational input.

---

## 2. Root Cause Identified

### Primary Root Cause: `backend/moza/agents/mock_agent.py`, line 186-208

The MockAgent's "complex task" branch contains a **hardcoded loop over ALL registered tools** with an **identical dummy payload**:

```python
# Line 186:
for tool in tools:                                  # Loops ALL tools (filesystem, terminal, browser)
    yield Event(
        type=EventType.TOOL_CALL,
        source="mock_agent",
        payload={
            "tool": tool.name,
            "args": {"action": "demo", "path": "."},  # <-- LINE 196: HARDCODED DUMMY PAYLOAD
        },
    )
    raw = await registry.execute_tool(
        tool.name,
        action="read",   # <-- LINE 205: Actually executes with different args
        path=".",         # <-- LINE 207
    )
```

**There are TWO hardcoded payloads at play:**
- **TOOL_CALL event payload** (line 196): `{"action": "demo", "path": "."}` — what the UI FRONTEND displays
- **Actual execution args** (lines 205-207): `action="read", path="."` — what actually runs

Neither payload reflects the actual user intent ("Create a file").

### Secondary Root Cause: `backend/moza/api/routes/chat.py`, lines 25-29

The route handler ALWAYS creates a **MockAgent** for every request:

```python
def _create_agent(agent_type: str) -> AgentInterface:
    if agent_type == "openhands":
        from moza.agents.openhands_adapter import OpenHandsAdapter
        return OpenHandsAdapter()
    return MockAgent()  # <-- DEFAULT for ALL tasks!
```

The config defaults to `agent_type = "mock"` in `backend/moza/config/models.py:52`. The **real LiteLLMToolAgent is never wired into the API route**.

---

## 3. Why All Tools Get The Same Payload

The `for` loop at `mock_agent.py:186` iterates over ALL tools returned by `registry.get_all()`:

```python
tools = registry.get_all()
for tool in tools:                        # filesystem, terminal, browser
    # ... same payload for EACH tool ...
```

At time of writing, `registry.get_all()` returns exactly 3 tools (confirmed by startup logs):
- `filesystem v1.0.0`
- `terminal v1.0.0`
- `browser v1.0.0`

Each iteration uses the **identical** `{"action": "demo", "path": "."}`. This is fundamentally **not a real agent** — it is a **test/demo stub** that was never intended for production use.

---

## 4. Source of `action="demo"` vs `action="read"` Confusion

| Location | Payload | Purpose |
|----------|---------|---------|
| `mock_agent.py:196` (TOOL_CALL event) | `{"action": "demo", "path": "."}` | What the FRONTEND renders in the tool call bubble |
| `mock_agent.py:205` (`execute_tool()`) | `action="read", path="."` | What actually executes in the backend |
| `test_e2e_flow.py:61` (test assertion) | `{"action": "read", "path": "."}` | Expected test value (does NOT match line 196!) |

The `"demo"` value is a **cosmetic display string** sent to the UI. The actual execution uses `action="read"`. Neither matches the user's request.

---

## 5. Recommended Fix Strategy

No code changes implemented yet. High-level approach:

### Fix 1: Wire LiteLLMToolAgent into the API Route
- Update `chat.py:_create_agent()` to instantiate `LiteLLMToolAgent` from config
- The config already has provider settings (groq/llama-3.3-70b-versatile) used by live benchmarks
- Remove fallback to MockAgent; MockAgent should remain for tests only

### Fix 2: Remove the Dummy Tool Loop from MockAgent (or gate it)
- `mock_agent.py:186-242` should either be removed or gated behind a test-only flag
- The "complex task" simulation with dummy payloads should NOT be the default production path

### Fix 3: Keep Intent Classifier as Pre-Gate
- The orchestrator-level `classify_intent()` is working correctly (proven by Test 2)
- It should remain as the first line of defense before dispatching to LiteLLMToolAgent

---

## 6. Code Locations (GitHub Links)

| File | Line(s) | Role |
|------|---------|------|
| [`backend/moza/agents/mock_agent.py`](https://github.com/tariqtharwat-OPS/Moza/blob/main/backend/moza/agents/mock_agent.py) | 186-241 | Hardcoded tool loop with dummy payload |
| [`backend/moza/api/routes/chat.py`](https://github.com/tariqtharwat-OPS/Moza/blob/main/backend/moza/api/routes/chat.py) | 25-29 | Always returns MockAgent (no LiteLLM path) |
| [`backend/moza/config/models.py`](https://github.com/tariqtharwat-OPS/Moza/blob/main/backend/moza/config/models.py) | 52 | `agent_type` defaults to `"mock"` |
| [`backend/moza/orchestrator/orchestrator.py`](https://github.com/tariqtharwat-OPS/Moza/blob/main/backend/moza/orchestrator/orchestrator.py) | 109-151 | Intent classifier (working correctly) |

---

## 7. Evidence: Actual Test Log Files

- Test 1 log: `python C:\Users\eg_di\AppData\Local\Temp\opencode\test_trace.py` (see Section 1)
- Test 2 log: Section 1 (truncated by console encoding, but first 5 events captured)
