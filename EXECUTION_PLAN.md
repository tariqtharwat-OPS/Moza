# MOZA Execution Plan & Tracker

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

### Phase 2.6: Real-World Execution Testing (OpenRouter Chat-Only Sanity Check) - [ ]
- [ ] Create `.env` file with API key placeholders (gitignored).
- [ ] Fix `config.yaml` env var expansion (`${VAR}` → `os.environ`) and `.env` loading via `python-dotenv`.
- [ ] Create isolated `POST /v1/test/chat` route (bypasses Orchestrator, Tools, Agents, EventBus — direct LLM pipe).
- [ ] Run backend and verify SSE streaming from OpenRouter with `curl`.
*Notes: Pure LLM connectivity test. No orchestration, no tools, no agents. Proves the LLM pipe works in the real environment before Phase 3 begins.*

### Phase 3: The Senses (Browser & Vision) - [ ]
- [ ] Integrate Browser-Use agent.
- [ ] Visual feedback for browser actions in UI.
*Notes:*

### Phase 4: The Brain (Memory & RAG) - [ ]
- [ ] Integrate Mem0 for long/short-term memory.
- [ ] Integrate LlamaIndex for local RAG.
*Notes:*

### Phase 5: Production & Polish - [ ]
- [ ] Plugin system setup.
- [ ] Sandbox security (Docker/gVisor).
- [ ] UI Polish (incorporating the existing logo).
*Notes:*
