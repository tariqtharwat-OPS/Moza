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

### Phase 3: The Senses (Browser & Vision) - [≈]
- [x] Create `BrowserTool` wrapping Playwright with 11 actions (navigate, click, type, extract_text, screenshot, scroll, back, forward, get_url, execute_js, close).
- [x] Register BrowserTool in tool registry at startup.
- [x] `BrowserVisualizer` React component with screenshot display, URL/title bar, action log.
- [x] Wire BrowserVisualizer into ChatInterface (browser events routed to dedicated component).
- [x] 7 unit tests for BrowserTool (registry, metadata, validation, lifecycle, cleanup).
- [ ] End-to-end browser automation test with real Playwright browser.
*Notes: BrowserTool uses Playwright directly (headless Chromium, 1280x720 viewport). Screenshots returned as base64 data URIs in event payload metadata. `requires_confirmation: True` for safety. Dependency: `playwright>=1.50.0`. Run `playwright install chromium` after pip install.*

### Phase 4: The Brain (Memory & RAG) - [ ]
- [ ] Integrate Mem0 for long/short-term memory.
- [ ] Integrate LlamaIndex for local RAG.
*Notes:*

### Phase 5: Production & Polish - [ ]
- [ ] Plugin system setup.
- [ ] Sandbox security (Docker/gVisor).
- [ ] UI Polish (incorporating the existing logo).
*Notes:*
