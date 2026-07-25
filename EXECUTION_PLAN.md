# MOZA Execution Plan & Tracker

## Core Philosophy
USE > INTEGRATE > EXTEND > BUILD | Vertical Slices Approach

## Architecture Mandates
1. **Session & Task Centric**: Core domain = Session (Workspace + Task + Execution History + Artifacts).
2. **Agent as Interface**: `AgentInterface` ABC; OpenHands/Aider/Cline = adapters.
3. **Event Bus**: In-memory Pub/Sub. UI streams structured `Event` events (agent_thinking/tool_call/tool_result/terminal_output/llm_token), not raw text.
4. **Tool Registry**: `BaseTool` ABC + `ToolRegistry`. MCP-ready metadata (version, parameters, returns, requires_confirmation, is_destructive). Tools = Filesystem, Terminal, Browser.
5. **Orchestrator Layer**: API route → TaskService → Orchestrator → Agent → Event. Decouples API from agent execution.
6. **Golden Rule of Mutation**: Agents MUST NEVER write to the Workspace directly. All mutations MUST flow through: Agent → ToolRegistry → Tool Execution → Event Emission → Workspace Update.

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
- [x] MCP-ready Tool Registry metadata (version, parameters, returns, confirmation, destructive flags).
- [x] Strict Event schema with 12 event types.
- [x] Session as root domain model with Workspace, Tasks, ExecutionHistory, Artifacts.
- [ ] Integrate OpenHands SDK as the coding agent adapter.
- [ ] Implement xterm.js + node-pty in Electron.
- [ ] File system operations (read/write/diff view).
- [ ] Agent streaming UI (structured events display in frontend).
*Notes: Phase 2 Domain Models refined with Session root, strict Event schema, Orchestrator layer, and MCP-ready Tool Registry metadata. Skeleton is 100% bulletproof, ready for real agent integration.*

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
