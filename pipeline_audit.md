# Pipeline Audit: Tool Determinism in MOZA AI OS

## End-to-End Flow Trace

```
User Input → Router.route() → LLM (via MozaOrchestrator or fallback)
    → NormalizedResponse.content + NormalizedResponse.tool_calls
    → LiteLLMToolAgent.execute() ReAct loop
        ├─ Path A: tool_calls present → GuardEngine → ToolRegistry.execute_tool()
        ├─ Path B: no tool_calls but content → _parse_text_tool_calls() [REGEX PARSER]
        └─ Path C: no tool_calls, no content → TASK_COMPLETED
    → Orchestrator._run_agent() → EventBus.publish()
    → EventSourceResponse event_stream() → SSE → frontend
```

---

## 1. Component-by-Component Analysis

### 1.1 LLMRouter (`router.py`)

#### `_route_with_orchestrator()` (lines 222-317)

```python
# Line 254-267
kwargs = {}
if temperature is not None:
    kwargs["temperature"] = temperature
if max_tokens is not None:
    kwargs["max_tokens"] = max_tokens
if tools:
    kwargs["tools"] = tools
# ... tool_choice is NEVER passed to the orchestrator
orch_result = await self._orchestrator.complete_with_tools(orchestrator_messages, **kwargs)
```

**Finding:** `tool_choice` parameter is **never passed** to `MozaOrchestrator.complete_with_tools()`. Even though `route()` accepts `tool_choice` as a parameter and the docstring mentions it, it is completely ignored in this method. The LLM backend receives no instruction to emit tool calls.

#### `_route_with_fallback()` (lines 319-350)

```python
# Line 331-340
kwargs = self._build_kwargs(
    model=provider.model,
    api_key=provider.api_key or "",
    base_url=provider.base_url or "",
    messages=messages,
    tools=tools,
    temperature=temperature,
    max_tokens=max_tokens,
    tool_choice=tool_choice,   # ← only this path receives tool_choice
)
```

```python
# Line 167 (inside _build_kwargs)
kwargs["tool_choice"] = tool_choice or "auto"
```

**Finding:** In fallback mode, `tool_choice` defaults to `"auto"` (via the `or "auto"` on line 167). `tool_choice: "auto"` means the LLM may or may not emit a tool call — it is **probabilistic**, not deterministic.

#### Agent initialization (`litellm_tool_agent.py`:38)

```python
self._force_tool_choice: str | None = None
```

This is initialized to `None` and only set to `"required"` inside the hallucination guard (line 622). On every other call, it remains `None`, flowing through to either `"auto"` or unset — never `"required"` by default.

### 1.2 Agent Execute — The Core ReAct Loop (`litellm_tool_agent.py`)

#### LLM Call — Deterministic structure, non-deterministic content (lines 468-524)

```python
# Line 469-475 (router path)
result = await self._router.route(
    messages=normalized_msgs,
    tools=tools,
    browser_mode=self._browser_mode,
    tool_choice=self._force_tool_choice,   # ← None → never "required"
)

# Line 493-498 (direct path)
kwargs = {
    "model": self._provider.model,
    "messages": normalized_msgs,
    "tools": tools,
    "tool_choice": self._force_tool_choice or "auto",   # ← falls back to "auto"
    "parallel_tool_calls": False,
}
raw = await litellm.acompletion(**kwargs)
```

**Finding:** The LLM API call itself is inherently **probabilistic** — even with `tool_choice: "required"`, LLMs occasionally break. However, the absence of `tool_choice="required"` on normal calls means the LLM has an even freer choice to emit plain text.

#### Text-to-Tool Parser — NON-DETERMINISTIC (lines 552-563, 185-371)

```python
# Line 552-563 (in execute())
if not tool_calls and content:
    try:
        available_tools_list = registry.get_all()
        parsed_calls = LiteLLMToolAgent._parse_text_tool_calls(
            content, available_tools_list
        )
        if parsed_calls:
            logger.info(...)
            tool_calls = parsed_calls   # ← overwrites the LLM's silence with our interpretation
```

`_parse_text_tool_calls()` (lines 185-371) is a **regex-heavy heuristic engine** with 4 strategies:

| Strategy | Lines | Mechanism | Determinism |
|----------|-------|-----------|-------------|
| 1: `<function_call>` XML tags | 193-229 | Regex + `ast.literal_eval` or `json.loads` | High (if LLM outputs clean XML) |
| 2: JSON code blocks | 232-276 | Regex ` ```json ... ``` ` + eval | Medium (depends on markdown formatting) |
| 3: Inline JSON extraction | 279-334 | Manual brace-matching cursor scan | Low (fragile, order-dependent) |
| 4: Keyword extraction | 336-371 | Regex word-matching on lowered text | **Very Low** — pure keyword heuristics |

**Critical non-determinism sources:**
- Strategy 4 (line 336-371) uses hardcoded keyword lists. If the LLM says "I'll create the file" vs "I will create a file", both match, but the regex on line 350 (`r'(?:to|in|at|:)\s*([A-Za-z]:\\[^\s"\']+)'`) may or may not extract a path depending on LLM phrasing.
- If both strategy 1 and strategy 2 match, only strategy 1 is used (early return). The order-of-strategy-examination is fixed, so this is technically deterministic in isolation, but different LLM text outputs will produce different parse outcomes.
- The `uuid4` IDs in line 223, 270, etc. are unique but irrelevant to determinism of *which* tool is selected.

#### Semantic Hallucination Guard — NON-DETERMINISTIC (lines 568-624)

```python
# Line 568-624
if not tool_calls and content:
    available_tools_list = registry.get_all()
    required_tools = LiteLLMToolAgent._semantic_requires_tool(
        task.description if task else "", available_tools_list  # ← checks TASK description, NOT the LLM response
    )
```

`_semantic_requires_tool()` (lines 374-402):

```python
action_map: dict[str, list[str]] = {
    "browser": ["search", "browse", "navigate", "website", "web", "url", ...],
    "filesystem": ["write", "save", "create", "file", "folder", ...],
    "terminal": ["run", "execute", "command", "terminal", "shell", ...],
}
for tool_name, keywords in action_map.items():
    if any(kw in lowered for kw in keywords):
        ...
        required.append(tool_name)
```

**Finding:** This checks the **task description** for keywords, not the LLM's actual response semantics. It's a crude keyword-in-string check. "How do I run Python" would match "terminal" for `run` and "execute". "Write a file" would match "filesystem" for `write`, `save`, `create`, and `file`. The logic is deterministic in code but **semantically unreliable** — it cannot determine whether the user actually needs a tool.

When hallucinations are detected (lines 585-623):
- After 3 hallucinations, the loop treats the task as conversational and exits (line 590).
- On each retry, it sets `self._force_tool_choice = "required"` (line 622), which **does** force tool_choice for the next LLM call. But this only happens AFTER the LLM already failed to produce tool calls.

### 1.3 Intent Classifier (`intent_classifier.py`)

#### `classify_intent()` (lines 124-142)

Deterministic keyword-based classification. Checks greetings, acknowledgements, WH-questions. This is deterministic — same input always maps to the same `IntentType`.

#### `get_conversational_reply()` (lines 145-154)

```python
def get_conversational_reply(user_input: str) -> str:
    from random import choice
    text = user_input.strip()
    for g in _GREETING_AR:
        try:
            if g in text:
                return choice(_ARABIC_REPLIES)   # ← NON-DETERMINISTIC
        except Exception:
            pass
    return choice(_ENGLISH_REPLIES)          # ← NON-DETERMINISTIC
```

**Finding:** Uses `random.choice()` to pick from 3 Arabic or 3 English replies. This is **NON-DETERMINISTIC** — different invocations produce different messages for the same user input.

### 1.4 Orchestrator (`orchestrator.py`)

#### `_run_agent()` (lines 102-216)

The flow here is a **deterministic dispatcher**:

- Lines 110-152: Intent classification → if conversational, use the random reply (non-determinism inherited from `get_conversational_reply`).
- Line 155: `async for event in self._agent.execute(context):` — deterministic iteration over the agent's generator.
- Lines 156-158: `session.execution_history.append(event)` → `self._event_bus.publish(session_id, event)` → deterministic pub/sub.
- Lines 160-177: User approval flow — deterministic event wait/resolve.

### 1.5 EventBus (`event_bus.py`)

Pure pub/sub with `asyncio.Queue`. Deterministic — events are pushed to queues and retrieved in FIFO order. No probability involved.

### 1.6 API Chat Route (`chat.py`)

#### `task_execute()` (lines 39-77)

- Line 55: `await task_service.submit_task(...)` → dispatches to Orchestrator.
- Lines 57-76: SSE generator reads from the EventBus queue. If `event is None` (lines 69-70), break. `EventSourceResponse(event_stream())` streams events as `{"event": "step", "data": event.model_dump_json()}`.
- **Fully deterministic** — pure message passing.

#### `_create_agent()` (lines 27-36)

Default `max_steps=15` (line 32). No randomness.

### 1.7 Frontend API (`api.ts`)

#### `streamTask()` (lines 13-59)

Parses SSE with pattern: `event: step` followed by `data: <JSON>`. Parses JSON and yields. **Fully deterministic** — same event stream, same parsing.

---

## 2. The Exact Breakpoints of Non-Determinism

### Breakpoint 1: `_route_with_orchestrator()` — Missing `tool_choice`

| Field | Detail |
|-------|--------|
| **File** | `D:\Moza\backend\moza\gateway\router.py` |
| **Lines** | 222-267 |
| **Line** | 265 (`complete_with_tools` call without `tool_choice`) |
| **Issue** | `tool_choice` parameter arrives at `route()` but is never passed to `MozaOrchestrator.complete_with_tools()`. The orchestrator's LLM backend receives no instruction to emit tool calls. |
| **Impact** | When orchestrator mode is active (the default per `config.yml`: `use_orchestrator: true`), the LLM can freely choose to reply with plain text instead of tool calls. |

### Breakpoint 2: `_route_with_fallback()` — Default to `tool_choice: "auto"`

| Field | Detail |
|-------|--------|
| **File** | `D:\Moza\backend\moza\gateway\router.py` |
| **Lines** | 319-350 |
| **Line** | 167 (`tool_choice or "auto"`) |
| **Issue** | When no explicit `tool_choice` is set, defaults to `"auto"` which permits plain-text LLM responses. |
| **Impact** | In fallback mode, LLM always has option to respond narratively instead of emitting tool calls. |

### Breakpoint 3: `LiteLLMToolAgent.execute()` — Default `_force_tool_choice = None`

| Field | Detail |
|-------|--------|
| **File** | `D:\Moza\backend\moza\agents\litellm_tool_agent.py` |
| **Lines** | 38, 474, 498 |
| **Line** | 38 (`self._force_tool_choice: str \| None = None`) |
| **Issue** | Initialized to `None`. Only set to `"required"` inside hallucination guard (line 622) as a recovery mechanism. On every normal ReAct loop iteration, it propagates as `None` → `"auto"`. |
| **Impact** | The first call to the LLM has no tool enforcement at all. |

### Breakpoint 4: `_parse_text_tool_calls()` — Regex Heuristic Parser

| Field | Detail |
|-------|--------|
| **File** | `D:\Moza\backend\moza\agents\litellm_tool_agent.py` |
| **Lines** | 185-371 |
| **Line** | 552-563 (invocation) |
| **Issue** | Four strategies of increasing fragility detect tool calls in free-form LLM text. Strategy 4 (line 336-371) is pure keyword spotting with no validation. |
| **Impact** | When the LLM describes an action in text instead of emitting structured calls, the parser guesses which tool to use. Two different LLM descriptions of the same intent can produce different tool selections. |

### Breakpoint 5: `_semantic_requires_tool()` — Keyword Matching on Task Description

| Field | Detail |
|-------|--------|
| **File** | `D:\Moza\backend\moza\agents\litellm_tool_agent.py` |
| **Lines** | 374-402 |
| **Line** | 570 (invocation) |
| **Issue** | Uses substring matching on the lowered task description. Cannot distinguish "write Python code" (filesystem) from "write a story" (no tool). |
| **Impact** | If the LLM responds with text for a "write" task, the guard detects it and retries 3x. But the guard checks the task description, not the LLM response semantics. |

### Breakpoint 6: `get_conversational_reply()` — Random Reply Selection

| Field | Detail |
|-------|--------|
| **File** | `D:\Moza\backend\moza\core\intent_classifier.py` |
| **Lines** | 145-154 |
| **Line** | 151, 154 (`random.choice()`) |
| **Issue** | Different replies are randomly selected for identical inputs. |
| **Impact** | Same user greeting → different bot response every time. |

---

## 3. LLM → ToolDispatcher Flow: Deterministic or Probabilistic?

**Answer: Probabilistic at two levels.**

### Level 1: LLM API Response (Probabilistic)

The LiteLLM acall (`router.py:196`) produces a response that depends on:
- The model's inherent stochasticity (temperature is passed through when set)
- The absence of `tool_choice="required"` at the first call (always `None` → `"auto"`)

Even with `tool_choice="required"`, LLMs occasionally produce text. The absence of `tool_choice="required"` makes this worse.

### Level 2: Text-to-Tool Extraction (Heuristic, quasi-deterministic but semantically fragile)

When the LLM responds with text instead of structured tool calls:
- `_parse_text_tool_calls()` (line 555) extracts tools from text using regex heuristics
- The **extraction mechanism** is deterministic (same text → same parse)
- But the **semantic mapping** is fragile (different valid text descriptions of the same intent may match different strategies or keywords)

So the extraction is technically deterministic, but it introduces non-determinism because: **the LLM's free-text output is itself non-deterministic**, and the parser's output depends on exactly what text the LLM produces.

---

## 4. Is `tool_choice="required"` Enforced at the API Level?

**No.** In every code path:

| Code Path | `tool_choice` Value | Enforced? |
|-----------|-------------------|-----------|
| Orchestrator mode (`_route_with_orchestrator`) | Not passed to orchestrator at all | **Never** |
| Fallback mode (`_route_with_fallback`) | Defaults to `"auto"` (line 167) | **Never** |
| First ReAct loop iteration | `None` propagated to both paths (line 474, 498) | **Never** |
| Hallucination recovery (lines 616-624) | Set to `"required"` only on retry, only as internal flag | **Partially (on retry only)** |

`tool_choice="required"` is only ever set internally (`_force_tool_choice = "required"` at line 622) as a signal for the **next LLM call** after a hallucination is detected. But:
1. It only applies to the next iteration after the LLM already failed.
2. In orchestrator mode, it's silently dropped (never passed through `route()` in orchestrator path).

---

## 5. Summary Table: Decision Points

| Decision Point | File | Lines | Deterministic? | Fix Required? |
|---------------|------|-------|---------------|---------------|
| Intent classification (orchestrator pre-check) | `intent_classifier.py` | 124-142 | **Yes** — keyword sets | No (but narrow — only for greetings) |
| Conversational reply generation | `intent_classifier.py` | 145-154 | **No** — `random.choice()` | **Yes** — pick deterministically |
| LLM routing to provider via orchestrator | `router.py` | 222-317 | **No** — no `tool_choice` passed | **Yes** — pass `tool_choice` to orchestrator |
| LLM routing to single provider (fallback) | `router.py` | 319-350 | **No** — defaults to `"auto"` | **Yes** — default to `"required"` or `"auto"` with guard |
| LLM response content (probabilistic model output) | `router.py` | 196; direct: `litellm_tool_agent.py:510` | **No** — all LLMs are probabilistic | Acknowledged (not fixable without constraints) |
| `tool_choice` parameter resolution | `litellm_tool_agent.py` | 38, 474, 498 | **No** — always `None` at first call | **Yes** — default to `"required"` for tool-capable tasks |
| Text-to-tool parsing (heuristic) | `litellm_tool_agent.py` | 185-371 | **Quasi** — deterministic parse, fragile semantics | **Yes** — add schema validation for parsed args |
| Semantic hallucination detection | `litellm_tool_agent.py` | 374-402 | **Quasi** — keyword matching on task desc | Partially — use an LLM-based guard for accuracy |
| Hallucination retry with `tool_choice="required"` | `litellm_tool_agent.py` | 573-624 | Yes — deterministic retry loop | Partial — the `"required"` signal is dropped in orchestrator mode |
| Tool execution (`ToolRegistry.execute_tool`) | `tools/registry.py` | 88-92 | Yes | No |
| GuardEngine checks | (external module) | agent:679 | Yes | No |
| EventBus pub/sub | `event_bus.py` | 26-37 | Yes | No |
| SSE streaming (`EventSourceResponse`) | `chat.py` | 57-77 | Yes | No |
| Frontend SSE parsing | `api.ts` | 13-59 | Yes | No |

---

## 6. Architecture Diagram — Where Non-Determinism Enters

```
User Input (deterministic)
    │
    ▼
┌─────────────────────────────────┐
│ Intent Classifier               │
│ classify_intent()               │ ← DETERMINISTIC (keyword sets)
│ get_conversational_reply()      │ ← NON-DETERMINISTIC (random.choice)
└────────────┬────────────────────┘
             │
             ├─ CONVERSATIONAL → random reply → EventBus → SSE → UI
             │
             ▼
┌─────────────────────────────────┐
│ LLMRouter.route()               │
│   _route_with_orchestrator()    │ ← NON-DETERMINISTIC: tool_choice DROPPED
│   _route_with_fallback()        │ ← NON-DETERMINISTIC: tool_choice→"auto"
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ LiteLLM acompletion()           │ ← NON-DETERMINISTIC: model outputs free text
│ (if no tool_choice="required")  │
└────────────┬────────────────────┘
             │
             ▼  NormalizedResponse {content, tool_calls}
┌─────────────────────────────────┐
│ Agent.execute() ReAct Loop       │
│                                 │
│ if tool_calls present:          │
│   GuardEngine → ToolExecute()   │ ← DETERMINISTIC (validated tool call)
│                                 │
│ if text only:                   │
│   _parse_text_tool_calls()      │ ← NON-DETERMINISTIC: heuristic regex parser
│   _semantic_requires_tool()     │ ← QUASI-DETERMINISTIC: keyword matching
│   retry 3x with tool_choice     │ ← "required" signal dropped in orchestrator mode
│                                 │
│ if no tool_calls after 3 fails: │
│   TASK_COMPLETED (text response)│ ← Acceptable fallback
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Orchestrator._run_agent()        │ ← DETERMINISTIC dispatcher
│     → EventBus.publish()         │ ← DETERMINISTIC pub/sub
│     → EventSourceResponse       │ ← DETERMINISTIC SSE
│         → frontend api.ts       │ ← DETERMINISTIC SSE parser
└─────────────────────────────────┘
```

---

## 7. Recommended Fixes (Priority Order)

### Fix 1: Pass `tool_choice` through orchestrator path
**File:** `router.py:265`
**Change:** Pass `tool_choice` parameter to `self._orchestrator.complete_with_tools()`.

### Fix 2: Default to `tool_choice="required"` when tools are provided
**File:** `litellm_tool_agent.py:498` and `router.py:167`
**Change:** Change `"auto"` to `"required"` when tools list is non-empty.

### Fix 3: Remove `random.choice()` from conversational reply
**File:** `intent_classifier.py:151,154`
**Change:** Use a first reply on first call, then cycle through replies, or make it deterministic by input content.

### Fix 4: Add post-parse validation to `_parse_text_tool_calls()`
**File:** `litellm_tool_agent.py:220-229` (and similar blocks)
**Change:** After parsing tool name + arguments, validate against the tool's schema before accepting the result.

### Fix 5: Fix hallucination guard to not silently drop `tool_choice`
**File:** `router.py:265`
**Change:** Ensure the orchestrator path respects `tool_choice`, or handle `tool_choice` at the agent level instead of router.
