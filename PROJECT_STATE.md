# PROJECT_STATE.md — MOZA Living Context Document

> **Purpose:** Single source of truth for any AI agent or developer joining the project.
> **Last Updated:** Phase 3.2 (Autonomous Research Benchmark)
> **Repository:** https://github.com/tariqtharwat-OPS/Moza

---

## 1. Core Philosophies (The 7 Golden Rules)

### Stability First
Tests must remain valid for years. Use static HTML fixtures and local HTTP servers — never live, changing data. Every benchmark must be 100% reproducible.

### Canonical Benchmarks
Few deep E2E tests > hundreds of shallow unit tests. Each phase proves the agent can autonomously complete a realistic, multi-step task in a real environment.

### Architectural Coverage
Every phase must explicitly state what architectural layers it proved. Coverage is tracked in the Architectural Coverage Map (below) and `EXECUTION_PLAN.md`.

### Capability Before Features
Build capabilities (e.g., "agent can research and synthesize across multiple pages"), not just components. A component without a proven capability is technical debt.

### No Regression
No new capability breaks an old one. 100% test pass rate required before any phase can be marked complete. Current baseline: 81 tests.

### Every Capability Has a Demo
Proof of concept via raw E2E logs captured in benchmark output. Every architectural layer in the coverage map links to evidence.

### Zero Technical Debt Before Next Phase
Refactor before adding new features. Monolithic code must be split, error paths hardened, and edge cases handled before moving to the next phase.

---

## 2. Current Status

| Property | Value |
|----------|-------|
| **Current Phase** | Phase 3.2 — Autonomous Research Benchmark |
| **Total Passing Tests** | 81 |
| **Last Successful Benchmark** | Phase 3.1 — Browser Live Testing (Wikipedia search, extraction, screenshot, artifact saving) |
| **Latest Model** | Groq `llama-3.3-70b-versatile` |
| **Engine Architecture** | ReAct loop via `LiteLLMToolAgent` (backend only, no UI) |
| **Browser Engine** | `PlaywrightEngine` implementing `BrowserEngine` ABC (headless Chromium, 1280x720) |
| **Context Strategy** | 7-section `ContextBuilder` (task, tools, workspace tree, git status, recent events, artifacts, environment) |

### Phase 3.2 Exit Criteria (Confirmed)
- ✅ Stability guarantee: local HTTP server + static HTML fixtures (no live data)
- ✅ Multi-step reasoning: agent visited 2 pages, extracted 4 data fields per page via CSS selectors
- ✅ Integrated workflow: BrowserTool (6 calls) + FilesystemTool (write)
- ✅ Quality assertions: >1 URL visited, specific data extracted, 770-byte structured `research.md`, synthesized reasoning confirmed
- ✅ LLM error resilience: `litellm_tool_agent.py` catches Groq API errors and retries
- ✅ All 81 existing tests pass — zero regression

---

## 3. Architectural Coverage Map

Legend: ✓ = Proved by live benchmark, ✗ = Not yet exercised, ≈ = Partial

| Layer | Component | Status | Proved In |
|-------|-----------|--------|-----------|
| **Agent Loop** | ReAct (while + max_steps + yield events) | ✓ | Phase 2.13 |
| **Recovery** | Tool error → LLM feedback | ✓ | Phase 2.13 |
| **Filesystem** | FilesystemTool (read/write) | ✓ | Phase 2.13 |
| **Terminal** | TerminalTool (subprocess) | ✓ | Phase 2.13 |
| **Context Engine** | ContextBuilder (7 sections) | ✓ | Phase 2.13 |
| **Event Bus** | Pub/Sub + EventRecorder | ✓ | Phase 2.13 |
| **Task State** | PENDING→RUNNING→COMPLETED | ✓ | Phase 2.13 |
| **Artifact Saving** | filesystem write from agent | ✓ | Phase 3.1 |
| **Browser DOM** | BrowserTool (navigate, click, type, extract_text, screenshot) | ✓ | Phase 3.1 |
| **Replay API** | SessionManager + replay endpoints | ✓ | Phase 2.14 |
| **Browser Reasoning** | Multi-page research + CSS extraction | ✓ | Phase 3.2 |
| **Multi-source Synthesis** | Cross-page information aggregation | ✓ | Phase 3.2 |
| **Artifact Generation** | Structured Markdown report | ✓ | Phase 3.2 |
| **LLM Error Resilience** | Catch API 400 on malformed tool calls | ✓ | Phase 3.2 |
| **Config** | MOZAConfig + provider resolution | ✓ | Phase 2.13 |
| **Approval** | Approval Service | ✗ | — |
| **Capability** | Capability Manager | ✗ | — |
| **Vision** | Screenshot → LLM reasoning | ✗ | — |
| **Computer Use** | OS-level mouse/keyboard | ✗ | — |
| **Multi-Agent** | Agent orchestration | ✗ | — |

---

## 4. Immediate Next Steps

### Phase 3.3: Vision-Enhanced Browser Reasoning (Screenshots + DOM)
- Add vision capability: feed screenshot images to LLM alongside DOM text for richer reasoning
- Agent must navigate a page, screenshot it, and use the screenshot content (not just DOM text) to answer a visual question
- All 81+ existing tests must still pass

### Phase 4: The Brain (Memory & RAG)
- Integrate Mem0 for long/short-term memory
- Integrate LlamaIndex for local RAG

### Phase 5: Production & Polish
- Plugin system setup
- Sandbox security (Docker/gVisor)
- UI Polish

### Key Constraints for Next Agent
- ALL work is backend-only (no UI/frontend changes)
- No single file should exceed ~250 lines
- Screenshot base64 data (~280KB) must be stripped from LLM tool messages (existing fix in `litellm_tool_agent.py`)
- Playwright headless Chromium required for browser tests
- `dom.get_url()` is a sync property (not async)

---

## 5. Key Files & Locations

| File | Purpose |
|------|---------|
| `EXECUTION_PLAN.md` | Full phase roadmap with exit criteria and notes |
| `PROJECT_STATE.md` | This file — living context document |
| `config.yaml` | MOZA configuration (model, providers) |
| `backend/moza/agents/litellm_tool_agent.py` | ReAct agent loop (system prompt, tool schema, error resilience) |
| `backend/moza/tools/browser_tool.py` | Thin wrapper (128 lines) delegating to PlaywrightEngine |
| `backend/moza/tools/browser_engine.py` | BrowserEngine ABC |
| `backend/moza/tools/playwright_engine.py` | Playwright implementation (121 lines) |
| `backend/moza/tools/browser/` | Modular browser components (navigation, dom, screenshot, forms, utils) |
| `backend/tests/live/` | E2E benchmark tests (the canonical proofs) |
| `backend/tests/fixtures/research/` | Static HTML fixtures for Phase 3.2 benchmark |
| `backend/tests/unit/` | Unit tests (tools, config, environment, events) |
| `backend/tests/integration/` | Integration tests (replay API, SSE flow) |

---

## 6. How to Run

```bash
# Unit + integration tests (81 tests, no live dependencies)
cd backend && python -m pytest tests/ -v

# Live benchmarks (requires Groq API key + Playwright)
cd backend && python tests/live/test_browser_live_benchmark.py
cd backend && python tests/live/test_autonomous_research_benchmark.py
```

**Note:** Live benchmarks start a real Playwright browser and call the Groq API. They require:
- `GROQ_API_KEY` in `.env`
- `playwright install chromium` after pip install
