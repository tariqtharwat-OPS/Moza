# MOZA Execution Plan & Tracker

## Core Philosophy
USE > INTEGRATE > EXTEND > BUILD | Vertical Slices Approach

## Execution Phases
### Phase 1: The Neural Link (Chat & LLM Pipeline) - [x]
- [x] Backend: FastAPI setup, Pydantic config models, LiteLLM client.
- [x] Backend: `/v1/chat/completions` route with SSE Streaming.
- [ ] Frontend: Next.js basic chat UI.
- [ ] Desktop: Electron shell + API connection.
- [ ] Integration: End-to-end streaming chat test.
*Notes: Backend foundation, LiteLLM adapter (clean adapter pattern), and SSE streaming route completed and approved. Moving to Frontend chat UI.*

### Phase 2: The Hands (Coding Agent & Terminal) - [ ]
- [ ] Integrate OpenHands SDK as the coding agent.
- [ ] Implement xterm.js + node-pty in Electron.
- [ ] File system operations (read/write/diff view).
- [ ] Agent streaming UI (token-by-token display).
*Notes:*

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
