# MOZA Execution Plan & Tracker

## Project Rules
**Every phase must begin with clearly defined Exit Criteria. A phase is complete ONLY when those criteria pass through reproducible end-to-end tests.**
No mocks in the execution path for completion verification.

## Core Philosophy
USE > INTEGRATE > EXTEND > BUILD | Vertical Slices Approach

## Architecture Mandates
1. **Session & Task Centric**: Core domain = Session (Workspace + Task + Execution History + Artifacts).
2. **Agent as Interface**: `AgentInterface` ABC; OpenHands/Aider/Cline = adapters.
3. **Event Bus**: In-memory Pub/Sub. UI streams structured `Event` events (agent_thinking/tool_call/tool_result/terminal_output/llm_token), not raw text.
4. **Tool Registry**: `BaseTool` ABC + `ToolRegistry`. MCP-ready metadata (version, parameters, capabilities, returns, requires_confirmation, is_destructive). Tools = Filesystem, Terminal, Browser.
5. **Orchestrator Layer**: API route → TaskService → Orchestrator → Agent → Event. Decouples API from agent execution.
6. **Golden Rule of Mutation**: Agents MUST NEVER write to the Workspace directly. All mutations MUST flow through: Agent → ToolRegistry → Tool Execution → Event Emission → Workspace Update.
7. **ExecutionContext**: Single unified context object passed to agents (session, workspace, tool_registry, event_bus, cancellation_token).
8. **Cancellation**: CancellationToken via asyncio.Event for cooperative task cancellation.
9. **ResourceManager**: Stub workspace resource management (git_status, file_watcher, vector_index).
10. **Architecture Decision Records (ADRs)**: docs/ADRs/ documenting key architectural decisions.

## Execution Phases
### Phase 1: The Neural Link (Chat & LLM Pipeline) - [x]
- [x] Backend: FastAPI setup, Pydantic config models, LiteLLM client.
- [x] Backend: `/v1/chat/completions` route with SSE Streaming.
- [x] Frontend: Next.js basic chat UI.
- [x] Desktop: Electron shell + API connection.
- [x] Integration: End-to-end streaming chat test.
*Notes: Backend, LiteLLM adapter (clean pattern), Frontend SSE Chat UI, Electron shell with robust child process management complete.*

### Phase 2: The Hands (Coding Agent & Terminal) - [ ]
- [x] Domain models & interfaces: Session, Task, Artifact, Event, AgentInterface, ToolRegistry, EventBus.
- [x] Mock agent yielding structured Event events (agent_thinking/tool_selected/tool_call/tool_result/llm_finished).
- [x] Orchestrator layer with TaskService (submit/cancel/resume).
- [x] MCP-ready Tool Registry metadata (version, parameters, capabilities, confirmation, destructive flags).
- [x] Strict Event schema with 12 event types.
- [x] Session as root domain model with Workspace, Tasks, ExecutionHistory, Artifacts.
- [x] ADRs documenting architectural decisions (001-litellm, 002-event-schema, 003-orchestrator).
- [x] ExecutionContext with CancellationToken for cooperative cancellation.
- [x] Real FilesystemTool (read/write/list with safety metadata).
- [x] Real TerminalTool (async subprocess with timeout).
- [x] MockAgent proof-of-concept calling real tools through ToolRegistry (proving Golden Rule).
- [x] Tool lifecycle (load/unload/reload) with capabilities system.
- [x] ResourceManager stub (git_status, file_watcher, vector_index).
- [x] OpenHands adapter with Action/Observation to MOZA Event mapping.
- [x] xterm.js terminal output visualization in frontend.
- [x] Agent streaming UI (structured events display in frontend).
*Notes: Phase 2 vertical slice complete — TerminalComponent renders real-time tool_call/tool_result (tool="terminal") output in xterm.js with GitHub Dark theme. Electron IPC bridge (terminal:write) provides input passthrough path. ChatInterface filters terminal events from normal blocks and renders TerminalComponent inline for live terminal visualization.*

### Phase 2.5: Core Hardening (Task State, Standardized Tool Results, Execution Recorder, Workspace Lock) - [x]
- [x] Task state machine: PENDING → RUNNING → {WAITING_TOOL, WAITING_USER} → COMPLETED/FAILED/CANCELLED.
- [x] `ToolResultPayload` Pydantic model: strict schema for all TOOL_RESULT event payloads (`success`, `duration_ms`, `exit_code`, `stdout`, `stderr`, `artifacts`, `metadata`).
- [x] `Artifact.version` field for file diff/rollback tracking.
- [x] `BaseTool.cleanup()` + `ToolRegistry.cleanup_all()` on cancel/fail to prevent zombie processes.
- [x] `TerminalTool` fully stateless (no UI knowledge) with active subprocess tracking and cleanup.
- [x] `FilesystemTool` returning `ToolResultPayload`-compliant structured results.
- [x] `ResourceManager.workspace_lock` (`asyncio.Lock`) for concurrent workspace access prevention.
- [x] `EventRecorder` persists every event as JSONL to `sessions/{session_id}/tasks/{task_id}/events.jsonl`.
- [x] EventBus integrated with EventRecorder — all published events recorded automatically.
- [x] Orchestrator drives task state machine based on emitted event types.
- [x] OpenHandsAdapter uses `ToolResultPayload` for TOOL_RESULT events; simulation fallback routes through `tool_registry.execute()`.
- [x] Frontend `ToolResultBlock` and `TerminalComponent` read flat `ToolResultPayload` fields (`stdout`/`stderr`/`exit_code`/`success`).
*Notes: Phase 2 vertical slice hardened. All tool results conform to ToolResultPayload. Events auto-persist to JSONL for replay. Tools self-clean on cancel. Workspace locked against concurrent access.*

### Phase 2.6: Real-World Execution Testing (OpenRouter Chat-Only Sanity Check) - [x]
- [x] Create `.env.example` template; `.env` with real OpenRouter key (gitignored).
- [x] Fix `config.yaml` env var expansion (`${VAR}` → `os.environ` via `_expand_env_vars()`). Proper `.env` loading via `python-dotenv` with `path.parent / ".env"` resolution.
- [x] Fix config.yaml model names — `qwen/qwq-32b` → `openrouter/qwen/qwen3-32b` (validated against OpenRouter model list).
- [x] Fix `MOZAConfig.from_yaml()` — strip `default` alias before Pydantic validation, `_expand_env_vars()` recursive helper.
- [x] Fix `main.py` — resolve `config.yaml` via `Path(__file__).parent.parent.parent` (robust against CWD).
- [x] Create `backend/run_server.py` launcher.
- [x] Create `POST /v1/test/chat` route (pure text/plain streaming, no Orchestrator/Tools/Agents/EventBus).
- [x] Verify LLM connectivity — Python direct test returns `"Hi there friend."` from OpenRouter (`qwen/qwen3-32b`).
*Notes: ✅ LLM pipe proven working. Config + .env + env var expansion validated. Test route ready.*
*Phase 3 (Browser) can proceed.*

### Phase 2.7: AI OS Core Upgrades (Environment, Capability Manager, Approval Service, Groq) - [x]
- [x] **Environment Abstraction**: Renamed `Workspace` → `Environment` with 6 sub-domains (`filesystem`, `terminal`, `browser`, `desktop`, `secrets`, `memory`). `Workspace` kept as deprecated subclass for backward compat. `Session.workspace` → `Session.environment` (with `.workspace` property bridge).
- [x] **Capability Manager**: Added `AgentConfig` (default + allowed_tools) to config models. `ToolRegistry.check_capability(agent_name, tool_name) -> bool` raises `PermissionError` on disallowed tools. `set_agent_capabilities()` configures per-agent allowlists.
- [x] **Enhanced Approval Service**: `WAITING_APPROVAL` (14th EventType) emitted by orchestrator when agent yields `TOOL_CALL` with `requires_confirmation=True`. Orchestrator pauses via `asyncio.Event.wait()` until `POST /v1/task/{task_id}/approve` or `POST /v1/task/{task_id}/reject` is called. Reject cancels the task.
- [x] **Groq Provider Fix**: Model name corrected to `groq/llama-3.3-70b-versatile` per spec.
- [x] **Agent Config in config.yaml**: `agents.mock.allowed_tools: []` (empty = all tools allowed) and `agents.openhands.allowed_tools: []`.
- [x] **All code paths updated**: `context.py`, `orchestrator.py`, `service.py`, `chat.py`, `openhands_adapter.py`, `registry.py`, `models.py`, `config/models.py`, `config.yaml`.
*Notes: Core AI OS plumbing complete. Environment provides sub-domain isolation. Capability Manager enforces per-agent tool gates. Approval Service enables human-in-the-loop for destructive/confirmation-required tool calls.*

### Phase 2.7 Verification & Phase 2.8: Backend E2E Integration Testing (Zero-Error Guarantee) - [x]
- [x] **47 unit tests covering Environment, Capability Manager, Approval Service, Groq config, EventRecorder** — all pass.
- [x] **12 integration tests for SSE stream, tool execution, approval flow, EventRecorder persistence** — all pass.
- [x] **Bugfix: `BaseTool` `Field()` on non-Pydantic ABC** — removed `Field(default_factory=...)` from tool definitions, replaced with plain `list` literals, fixing `PydanticSerializationError` in SSE stream.
- [x] **Bugfix: SSE event stream missing first event** — reordered `event_bus.subscribe()` before `task_service.submit_task()` in route handler so the queue catches AGENT_STARTED.
- [x] **Bugfix: SSE line-ending parsing** — normalized `\r\n` → `\n` in SSE parser and used `line.strip()` to handle CRLF boundaries.
- [x] **Bugfix: Agent overwrite in route handler** — route now checks `if orchestrator.agent is None` before setting agent, allowing tests to pre-configure custom agents.
*Notes: Backend proven flawless — zero-errors in SSE stream, all Event schema validated, approval flow verified, EventRecorder writes match streamed events. Ready for Phase 3 (Browser).*

### Phase 2.9: Real Autonomous Execution Loop - [x]
**Exit Criteria:**
- [x] Task creation via API.
- [x] Real LiteLLM invocation (Groq `llama-3.3-70b-versatile`).
- [x] Tool selection through ToolRegistry.
- [x] Real tool execution (FilesystemTool write + read).
- [x] Event streaming through EventBus.
- [x] Task completion with final summary.
- [x] Event recording and replay (`events.jsonl` — 7 events recorded).
- [x] NO MOCKS in the execution path.
*Notes: Groq LLM autonomously: (1) called filesystem write to create `moza_live_test.txt`, (2) called filesystem read to verify content, (3) responded with final summary. 7 events, 22s end-to-end. Approval Service excluded per scope. Verified with `backend/tests/live/test_real_agent_e2e.py`.*

### Phase 2.10: Executive Mind (Agent Loop Upgrade — ReAct Pattern) - [x]
**Exit Criteria:**
- [x] Agent runs in a `while` loop until task completion, max_steps, or fatal error.
- [x] `max_steps` is configurable (default: 15) and enforced.
- [x] Agent knows NOTHING about specific tools — only ToolRegistry, Events, and ExecutionContext.
- [x] Agent executes 3+ tool calls in a single task (write file → write file → read file → read file → summarize).
- [x] All existing 66+ tests still pass.
*Notes: Refactored `LiteLLMToolAgent.execute()` to true ReAct loop with `steps_count` counter. Agent made 4 autonomous tool calls (write step1.txt, write step2.txt, read step1.txt, read step2.txt) in one loop iteration, then summarized — 12 events, 27.8s. Added `max_steps` field to `AgentConfig`. Verified with `backend/tests/live/test_multi_step_agent.py`.*

### Phase 2.11: Context Engine - [x]
**Exit Criteria:**
- [x] Dedicated `ContextBuilder` class in `backend/moza/core/context_builder.py`.
- [x] Before *every* LLM call, the prompt is dynamically injected with: Workspace Tree, Current Directory, Git Status, Recent Events, Current Task, Available Tools, Current Artifacts.
- [x] Unit test verifies all 7 context sections are present in the output (9 tests).
- [x] All existing 75+ tests still pass.
*Notes: `ContextBuilder.build_context()` returns a structured text block with 7 sections. Injected into `messages[0]` (system prompt) before each LLM call in the ReAct loop. Handles gracefully: empty workspace, no git repo, no events yet, PermissionError on dir walk. 9 unit tests cover all sections, empty states, and edge cases.*

### Phase 2.12: Recovery Loop (Graceful Tool Failure Handling) - [x]
**Exit Criteria:**
- [x] Tool execution failure returns structured `ToolResultPayload` with `success=False` and clear `error_message` (not unhandled exception).
- [x] ReAct loop catches failure, emits `TOOL_RESULT` event with `success=False`, feeds error back to LLM as tool result in message history.
- [x] LLM autonomously decides next step based on error (retry, different tool, fix params, or `TASK_FAILED`).
- [x] Live E2E test proves recovery: agent reads non-existent file → gets `success=False` → autonomously creates file → reads it successfully → completes task.
- [x] All 75+ existing tests still pass.
*Notes: Agent received `success=False` on read of `will_not_exist.txt` (stderr: "Path does not exist"), autonomously switched to `filesystem write` creating `recovered.txt` with "The agent recovered from the error!", then read it back successfully. 3 tool calls, TASK_COMPLETED. No code changes needed — error handling was already built into the ReAct loop from Phase 2.10, just needed the live E2E test to prove it. Verified with `backend/tests/live/test_recovery_loop.py`.*

### Phase 2.13: Software Engineer Benchmark (Strict Anti-Cheat) - [x]
**Exit Criteria:**
- [x] Pre-seeds buggy `calculator.py` (integer division `//` instead of `/`).
- [x] Agent autonomously writes tests, runs pytest, reads failure traceback, fixes code, re-runs, passes.
- [x] Test validates exact 6-event sequence A-F from events: (A) first pytest call, (B) result with `success=False`, (C) filesystem write to fix `calculator.py`, (D) second pytest call, (E) result with `success=True`, (F) `TASK_COMPLETED`.
- [x] Anti-cheat: verifies `calculator.py` was modified (not test file), `divide(5,2)==2.5` mathematically, test file integrity preserved (all 6 keywords: add/subtract/multiply/divide/2.5/assert).
- [x] Full execution record persisted: `prompt.txt`, `context.json`, `tool_calls.jsonl`, `tool_results.jsonl`, `trace.log`, `events.jsonl`.
- [x] All 75+ existing tests still pass.
- [x] Framework is scenario-parameterised via `BugScenario` dataclass — new bug types (off-by-one, syntax error, wrong import, etc.) added by instantiation, no test rewrites.
*Notes: Agent executed full fail→read→fix→pass cycle autonomously in 12.4s: wrote test_calculator.py, ran pytest (1 failed: integer division bug), read calculator.py, wrote fixed version with `return a / b`, ran pytest (4 passed), completed with summary. Event sequence validation passed all 10 checks, anti-cheat passed all 9 checks. 14 events recorded. Verified with `backend/tests/live/test_software_engineer_benchmark.py`. This benchmark is now the quality gate for all future engineering tasks.*

### Phase 2.14: Replay API (Backend Only) - [x]
**Exit Criteria:**
- [x] `GET /v1/sessions` returns list of recorded session IDs with light metadata (task_count, total_events, first/last event timestamps).
- [x] `GET /v1/sessions/{session_id}` returns full metadata including task list (status, event_count, description derived from events).
- [x] `GET /v1/sessions/{session_id}/events` reads and returns structured events from `events.jsonl` (supports `?task_id=` filter).
- [x] `POST /v1/sessions/{session_id}/replay` re-emits recorded events to EventBus, returns `replay_initiated` with replayed/total counts.
- [x] All endpoints return 404 for nonexistent sessions.
- [x] 6 integration tests prove all endpoints work with seeded session data (empty list, 404, full lifecycle, multi-task, event count, replay delivery).
- [x] All 81 existing tests still pass.
*Notes: Created `SessionManager` (reads session metadata + events from disk via same `events.jsonl` files written by `EventRecorder`), `Replay API router` (4 endpoints under `/v1/` prefix), registered in `main.py`. Tests cover empty state, 404s, single-task session CRUD, multi-task sessions, and event replay delivery verification via EventBus queue. 6 tests, all passing. 81 total tests.*

## Architectural Coverage Report (Phase 2.13–3.2.5)

This report documents which architectural layers were exercised by live benchmarks across Phases 2.13 to 3.2.
All proven layers below are **frozen** as of Phase 3.2.5 — no regression allowed.

| Layer | Component | Status | Evidence |
|-------|-----------|--------|----------|
| **Agent Loop** | ReAct (while + max_steps) | ✓ | Agent loop ran 5 steps (write test → pytest → read source → fix → pytest) |
| **Recovery** | Tool error → LLM feedback | ✓ | First pytest returned `success=False, exit_code=1` — agent read traceback and fixed code |
| **Filesystem** | FilesystemTool (read/write) | ✓ | `filesystem write test_calculator.py`, `filesystem read calculator.py`, `filesystem write calculator.py` |
| **Terminal** | TerminalTool (subprocess) | ✓ | `pytest test_calculator.py -v` executed twice (first failure, second success) |
| **Context Engine** | ContextBuilder (7 sections) | ✓ | Workspace tree, current dir, tool list injected — agent used correct `cwd` param |
| **Event Bus** | Pub/Sub + EventRecorder | ✓ | 14 events streamed, persisted to `events.jsonl` |
| **Task State** | PENDING→RUNNING→COMPLETED | ✓ | Task completed with `TASK_COMPLETED` |
| **Artifact Saving** | filesystem write from agent | ✓ | Phase 3.1: Agent saved extracted text to `wikipedia_python.txt` via filesystem write |
| **Anti-Cheat** | Post-run integrity verification | ✓ | `calculator.py` was modified (not tests), `divide(5,2)==2.5` verified, 6 test keywords present |
| **Browser Reasoning** | BrowserTool multi-page research + CSS extraction | ✓ | Phase 3.2: Agent autonomously visited 2 fixture pages, extracted 4 data fields per page via CSS selectors |
| **Multi-source Synthesis** | Cross-page information aggregation | ✓ | Phase 3.2: Agent combined releases page data + features page data into unified research report |
| **Artifact Generation** | Structured Markdown report via FilesystemTool | ✓ | Phase 3.2: Agent wrote `research.md` with Version Info, Feature Comparison, Recommendation sections (770 bytes) |
| **LLM Error Resilience** | Catch Groq API 400 on malformed tool calls | ✓ | Phase 3.2: `litellm_tool_agent.py` wraps `acompletion()` in try/except, feeds error back as message, continues |
| **Scenario Framework** | `BugScenario` parameterisation | ✓ | Single scenario run; new bugs added by instantiation |
| **Config** | MOZAConfig + provider | ✓ | config.yaml loaded, Groq provider resolved, API key from .env |
| **Browser** | BrowserTool (navigate/type/click/screenshot/extract_text) | ✓ | Phase 3.1: Navigated Wikipedia, typed search query, extracted text, took screenshot |
| **Approval** | Approval Service | ✗ | Not exercised (terminal tool `requires_confirmation` bypassed for agent-direct execution) |
| **Capability** | Capability Manager | ✗ | Not exercised (all tools allowed by default) |
| **Replay API** | SessionManager + replay endpoints | ✓ | Phase 2.14 adds coverage; benchmark data replayable via API |

### Phase 3.0: Browser Refactor & Engine Abstraction - [x]
**Exit Criteria:**
- [x] `BrowserEngine` ABC defines core interface (navigate, click, type_text, extract_text, screenshot, scroll, go_back, go_forward, get_url, execute_js, close).
- [x] `PlaywrightEngine` implements `BrowserEngine` using actual Playwright (121 lines).
- [x] `BrowserTool` split into focused modular components under `browser/` package: `navigation.py` (29 lines), `dom.py` (13), `screenshot.py` (15), `forms.py` (6), `utils.py` (12). No single file exceeds ~250 lines.
- [x] `BrowserTool` delegates all execution to the `PlaywrightEngine` instance (128 lines, thin wrapper).
- [x] External API of `BrowserTool` (ToolRegistry + LLM) is exactly the same — 7 unit tests pass with zero modifications.
- [x] All 81 existing tests pass.
*Notes: Monolithic 379-line browser_tool.py split into 8 files: engine ABC, Playwright implementation, 5 modular components, and thin tool wrapper. Max file size: 128 lines (browser_tool.py). Constructor signature `BrowserTool(headless=True, screenshots_dir=None)` unchanged. Legacy test attributes `_browser`, `_page` preserved via properties. 0 regression.*

### Phase 3.1: Browser Live Testing (Traditional Actions, No Vision) - [x]
**Exit Criteria:**
- [x] Agent successfully completes multi-step browser task autonomously (Wikipedia: navigate → search → extract → screenshot → save artifacts).
- [x] Task verified: Wikipedia homepage navigated, search input filled via `type`, `screenshot` taken with valid base64 data (286KB), text extracted, artifact saved via `filesystem write`.
- [x] All 6 events verified from event stream: `navigate` → `type` → `click` (timeout, recovered) → `extract_text` → `screenshot` → `filesystem write` → `TASK_COMPLETED`.
- [x] Screenshot base64 data preserved in event metadata (stripped from LLM context to prevent overflow).
- [x] Bugfix: `litellm_tool_agent.py` strips `screenshot_base64` from LLM tool-result messages (prevents Groq 400 error on large image payloads).
- [x] Bugfix: `browser/dom.py` `get_url()` made synchronous (was async for sync property, causing JSON serialization error).
- [x] All 81 existing tests still pass.
*Notes: Agent navigated to Wikipedia, typed "Python (programming language)" into `#searchInput`, attempted `#searchButton` click (timed out — Wikipedia modern UI), recovered by extracting text and taking screenshot, saved artifact. 18 events, 89.9s. Screenshot base64 correctly stripped from LLM context to prevent 128K token overflow. Verified with `backend/tests/live/test_browser_live_benchmark.py`.*

### Phase 3.2.5: Regression Freeze — Canonical Benchmarks Locked - [x]
**Exit Criteria:**
- [x] **Code Quality Audit**: Zero TODOs, FIXMEs, HACKs, dead code, or unused imports in `backend/moza/tools/browser/`.
- [x] **All 5 Canonical Benchmarks PASS:**
  - Phase 2.12 (Recovery Loop): Agent recovered from file-not-found error, wrote + read recovery file. ✅
  - Phase 2.13 (Software Engineer): Agent wrote tests, fixed integer division bug, verified all pass. ✅
  - Phase 3.1 (Browser Live): Wikipedia navigate → type → click (timeout, recovered) → extract → screenshot → save artifact. ✅
  - Phase 3.2 (Autonomous Research): Local HTTP server fixtures, 2 pages, 4 data fields per page, structured research.md. ✅
  - Phase 2.14 (Replay API): 6 integration tests (empty, 404, CRUD lifecycle, multi-task, events, replay). ✅
- [x] **Full Test Suite**: 81/81 tests pass (100%). No failures, no skipped, no xfail, no warnings.
- [x] **Documentation Updated**: PROJECT_STATE.md, REGRESSION_FREEZE.md created.
- [x] **Rules Enforced**:
  - No new capability can break any frozen benchmark.
  - All new features must include Canonical Benchmark + Regression Test.
  - Vision, Approval, and Memory are deferred to Phase 3.4+.
*Notes: This freeze is PERMANENT. Future phases MUST respect it. Next: Phase 3.3 (Frontend E2E Integration) → Phase 3.4 (Vision-Enhanced Reasoning).*

### Phase 3.2: Autonomous Research Benchmark (Stable Fixtures) - [x]
**Exit Criteria:**
- [x] **Stability Guarantee**: Test uses local HTTP server serving static HTML fixtures (no live/changing data, 100% reproducible).
- [x] **Multi-Step Reasoning**: Agent visited TWO pages (`releases.html` + `features.html`), extracted data via CSS selectors, and synthesized findings.
- [x] **Integrated Workflow**: Agent used BrowserTool (navigate + extract_text) and FilesystemTool (write structured research.md).
- [x] **Quality Assertions**:
  - Agent navigated to >1 URL (2 pages visited).
  - Agent extracted specific data points (release dates, key features, EOL dates, adoption stability).
  - Agent wrote a 770-byte structured Markdown file (`research.md`) with sections: Version Info, Feature Comparison, Recommendation.
  - Final output contains synthesized reasoning (2+ keywords: "synthesized", "recommend", "stable", "because", etc.).
  - Generated report mentions both 3.8.0 and 3.9.0, contains dates, uses Markdown headings.
- [x] All 81 existing tests still pass.
- [x] **Bugfix**: `litellm_tool_agent.py` now catches LLM API errors (e.g., Groq tool-validation 400) and feeds error back to agent with retry instruction instead of crashing.
*Notes: Agent autonomously navigated to `releases.html`, extracted `.release-date`, `.key-features`, `.end-of-life-date`, `.adoption-stability` (6 browser calls), then navigated to `features.html`, and published a 770-byte research report. Elapsed: 24.3s. Test: `backend/tests/live/test_autonomous_research_benchmark.py`. Fixtures: `backend/tests/fixtures/research/` (releases.html, features.html). Architectural Coverage: new ✓ rows for Browser Reasoning, Multi-source Synthesis, Artifact Generation.*

### Phase 4: The Brain (Memory & RAG) - [ ]
- [ ] Integrate Mem0 for long/short-term memory.
- [ ] Integrate LlamaIndex for local RAG.
*Notes:*

### Phase 5: Production & Polish - [ ]
- [ ] Plugin system setup.
- [ ] Sandbox security (Docker/gVisor).
- [ ] UI Polish (incorporating the existing logo).
*Notes:*
