# MOZA Execution Plan & Tracker

## Core Philosophy
USE > INTEGRATE > EXTEND > BUILD | Vertical Slices Approach

## Architecture Mandates
1. **Session & Task Centric**: Core domain = Session (Workspace + Task + Execution History).
2. **Agent as Interface**: `AgentInterface` ABC; OpenHands/Aider/Cline = adapters.
3. **Event Bus**: In-memory Pub/Sub. UI streams structured `ExecutionStep` events (thought/tool_call/result), not raw text.
4. **Tool Registry**: `BaseTool` ABC + `ToolRegistry`. MCP-ready. Tools = Filesystem, Terminal, Browser.

## Execution Phases
### Phase 1: The Neural Link (Chat & LLM Pipeline) - [x]
- [x] Backend: FastAPI setup, Pydantic config models, LiteLLM client.
- [x] Backend: `/v1/chat/completions` route with SSE Streaming.
- [x] Frontend: Next.js basic chat UI.
- [x] Desktop: Electron shell + API connection.
- [x] Integration: End-to-end streaming chat test.
*Notes: Backend, LiteLLM adapter (clean pattern), Frontend SSE Chat UI, Electron shell with robust child process management complete.*

### Phase 2: The Hands (Coding Agent & Terminal) - [ ]
- [x] Domain models & interfaces: Session, Task, ExecutionStep, AgentInterface, ToolRegistry, EventBus.
- [x] Mock agent yielding structured ExecutionStep events (thought/tool_call/result/message).
- [ ] Integrate OpenHands SDK as the coding agent adapter.
- [ ] Implement xterm.js + node-pty in Electron.
- [ ] File system operations (read/write/diff view).
- [ ] Agent streaming UI (structured events display).
*Notes: Step 1 (contracts + mock) complete. Step 2 (real agent integration) next.*

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
