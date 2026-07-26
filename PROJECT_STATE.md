# PROJECT_STATE.md — MOZA Living Context Document

> **Purpose:** Single source of truth for any AI agent or developer joining the project.
> **Last Updated:** Phase 4.1 — Capability Contract Model (Conversation Contract + Minimal Base Class)
> **Repository:** https://github.com/tariqtharwat-OPS/Moza

---

## 0. 🎯 THE ULTIMATE PRODUCT VISION & AI GUIDANCE RULES

### The Goal
MOZA is NOT just scripts. It is a standalone, production-ready Desktop Application (`.exe` / `.app`). The end-user must launch it with a double-click, without ever touching a terminal or managing dependencies.

### The Golden Rule
Every task must be evaluated against: *"Does this bring us closer to a shippable, robust, standalone desktop product?"*

### Strict Rules
- **No "Works on My Machine" code.** Every phase must include Build & Run verification.
- **Dependency Management:** The app must handle its own dependencies. End-users never run `npm install` or `pip install`.
- **UX First:** If a feature requires the user to open a terminal or edit a config file, it is a bug. Fix it with GUI or automated background processes.
- **Packaging Readiness:** Code must be written with PyInstaller/Electron packaging in mind (e.g., correct relative paths, no hardcoded local paths).

### System Requirements (CRITICAL)
- **Drive Format:** The project (especially the frontend) MUST reside on an **NTFS** drive. Node.js v24+ will fail with `EISDIR` errors on FAT32/exFAT drives due to `fs.readlinkSync()` incompatibility.
- **OS:** Windows 10+ (for Electron packaging). macOS/Linux support is deferred.

---

## 1. Core Philosophies (The 9 Golden Rules)

### Stability First
Tests must remain valid for years. Use static HTML fixtures and local HTTP servers — never live, changing data. Every benchmark must be 100% reproducible.

### Canonical Benchmarks
Few deep E2E tests > hundreds of shallow unit tests. Each phase proves the agent can autonomously complete a realistic, multi-step task in a real environment.

### Architectural Coverage
Every phase must explicitly state what architectural layers it proved. Coverage is tracked in the Architectural Coverage Map (below) and `EXECUTION_PLAN.md`.

### Capability Before Features
Build capabilities (e.g., "agent can research and synthesize across multiple pages"), not just components. A component without a proven capability is technical debt.

### No Regression
No new capability breaks an old one. 100% test pass rate required before any phase can be marked complete. Current baseline: 87 tests (81 unit/integration + 6 E2E).

### Every Capability Has a Demo
Proof of concept via raw E2E logs captured in benchmark output. Every architectural layer in the coverage map links to evidence.

### Zero Technical Debt Before Next Phase
Refactor before adding new features. Monolithic code must be split, error paths hardened, and edge cases handled before moving to the next phase.

### Capability Certification Framework (New)
**"Capability Coverage" replaces "Test Count" as the primary quality metric.** Every future phase must begin by defining its Capability Benchmark first. The Capability Certification Matrix in `TEST_STRATEGY.md` tracks 18 capabilities (9 certified ✓, 9 pending ✗). A capability is certified ONLY when its Layer 6 Canonical Benchmark passes on `main`.

### Controlled Evolution Architecture (New)
MOZA's self-improvement is strictly governed by Three-Tier Deployment and Four Sources of Evolution (detailed in Section 8 below). No self-modification code runs outside the `Experimental` tier. All merges to `Stable` require explicit human approval.

---

## 2. Current Status

| Property | Value |
|----------|-------|
| **Current Phase** | Phase 4.1 — Capability Contract Model (Conversation Contract) |
| **Total Passing Tests** | 94 tests (81 unit/integration + 13 intent classifier) = 100% pass rate (regression freeze intact) |
| **Capabilities Defined / Certified** | 21 defined, 11 certified ✅ (see `TEST_STRATEGY.md`) |
| **Last Successful Benchmark** | Phase 4.0 — Executive Mind (deterministic intent routing), Workspace UI (3-panel layout, welcome card, sidebar, collapsible execution panel) |
| **Latest Model** | Groq `llama-3.3-70b-versatile` |
| **Engine Architecture** | Executive Mind (Orchestrator-level `classify_intent()`) + ReAct loop via `LiteLLMToolAgent` |
| **Browser Engine** | `PlaywrightEngine` implementing `BrowserEngine` ABC (headless Chromium, 1280x720) |
| **Context Strategy** | 7-section `ContextBuilder` (task, tools, workspace tree, git status, recent events, artifacts, environment) |

### Phase 4.1 — Capability Contract Model

**Problem:** The project shifted from "test count" to "capability certification" as the primary quality metric, but there was no formal contract defining what a capability is, what it must do, and what it must NOT do.

**Philosophy:** "Capability First, not Framework First." Design the contract from real needs, not theoretical architecture.

**Deliverables:**
1. **Conversation Contract** — Comprehensive capability contract defining Purpose, Inputs, Outputs, Forbidden Behaviors, Definition of Done, Evidence Requirements, Maturity Level, and Capability History for the Conversation capability.
2. **Minimal Base Class** — `Capability` ABC with `CertificationResult` dataclass, `MaturityLevel` enum, and three abstract methods (`certify`, `get_definition_of_done`, `get_forbidden_behaviors`). NOT a full framework — only what Conversation needs.
3. **Source of Truth Updates** — PROJECT_STATE.md, TEST_STRATEGY.md, ARCHITECTURE.md (ADR-003) updated.

**Files Created:**
- `backend/moza/certification/capabilities/conversation_contract.md`
- `backend/moza/certification/capability_base.py`

**Capability-First Philosophy:**
- Each capability has a formal contract (markdown document) before any implementation
- The contract defines forbidden behaviors explicitly — not just what it should do, but what it must NOT do
- Definition of Done is the certification gate
- Maturity Level quantifies readiness (Level 0-5)
- Confidence Score quantifies reliability (0-100%)
- Future capabilities will each have their own contract before implementation begins

**Audit Trail:**
- Commit: [`b6a00a4`](https://github.com/tariqtharwat-OPS/Moza/commit/b6a00a4)
- All 76 backend unit tests pass (zero regression).

### Phase 3.3.5 — Agent Behavior Audit & Fix

**Problem:** Testing revealed the agent over-engineered simple tasks — `"Say hello in one word"` triggered `filesystem` tool with `action: "demo", path: "."` and returned technical jargon instead of "Hello".

**Root Cause:**
1. **MockAgent** (default agent): Always iterated ALL registered tools for EVERY task, including greetings
2. **LiteLLMToolAgent** system prompt: "Use tools to accomplish the task" — no guidance that direct responses are OK

**Fixes Applied:**
- `mock_agent.py`: Added `_is_simple_conversational()` heuristic detecting greetings, simple Qs, yes/no, Arabic commands (`قل مرحباً`). Simple tasks emit `AGENT_THINKING → LLM_TOKEN → LLM_FINISHED` with **zero tool calls**. Complex tasks unchanged.
- `litellm_tool_agent.py`: System prompt now asks `"DECIDE: Is this a simple conversational task? YES → Respond directly. NO → Use tools."`
- `test_agent_behavior_patterns.py` (new): 5 Playwright E2E tests for greeting, simple Q, tool task, mixed, Arabic
- `RUNNING_GUIDE.md`: Added "Agent Behavior Patterns" section with expected behavior tables

**Audit Trail:**
- Commit: [`3068532`](https://github.com/tariqtharwat-OPS/Moza/commit/3068532)
- Files: `mock_agent.py` (+116 lines), `litellm_tool_agent.py` (+4 lines), `test_agent_behavior_patterns.py` (new, 125 lines), `RUNNING_GUIDE.md` (+47 lines)
- All 81 existing tests pass (zero regression). 5 new E2E tests added.

### Phase 3.3.5 Patch — Agent Over-Tooling Prevention & UI Resilience

**Problem:** (from browser analysis) "hi how are you" triggered `filesystem` tool (`{"action":"demo","path":"."}`), returned `exit code 1 - Path is not a file: .`, and the frontend showed ugly "No screenshot available" text in the Browser Viewport.

**Root Cause:**
1. `_is_simple_conversational()` missed casual "hi how are you" — didn't match `_WH_WORDS` (no wh-word start) or `_SIMPLE_PATTERNS` (no command verb)
2. `filesystem_tool.py` read error on a directory said "Path is not a file: path" — no suggestion for alternative action
3. `BrowserVisualizer.tsx` showed bare "No screenshot available" text — poor UX for `.exe` goal

**Fixes Applied:**
- `mock_agent.py`: Added `_GREETING_ONLY` regex catching `hi`, `hey`, `hello` with any trailing text. Added `"how are you"` response entry.
- `litellm_tool_agent.py`: System prompt now starts with `"STRICT RULE — Greetings & casual conversation: ... NEVER call any tool"`
- `filesystem_tool.py`: Directory read error now says: `"Error: '{path}' is a directory, not a file. To read a file, provide a valid file path (e.g. 'readme.txt'). To list directory contents, use action='list' instead."`
- `BrowserVisualizer.tsx`: Replaced "No screenshot available" with an SVG icon + "Waiting for a browser task..." centered empty state.
- `test_agent_behavior_patterns.py`: Added `test_casual_greeting_hi_how_are_you` — asserts ZERO tool calls, friendly text, zero errors, zero console errors.

**Audit Trail:**
- Commit: [`e0caad7`](https://github.com/tariqtharwat-OPS/Moza/commit/e0caad7)
- Files: `mock_agent.py`, `litellm_tool_agent.py`, `filesystem_tool.py`, `BrowserVisualizer.tsx`, `test_agent_behavior_patterns.py`
- All 81 existing tests pass (zero regression). Frontend build succeeds. 6th E2E test added.

### Phase 3.3.5 Patch — Professional UI Redesign & Build Fix

**Problem:** Build corruption (`Cannot find module './833.js'`), bare-bones single-column UI unsuitable for `.exe` product.

**Fixes Applied:**
- Deleted `.next` and `node_modules/.cache`, clean rebuild succeeds in 44s
- Added `react-markdown` + `remark-gfm` for proper markdown rendering
- **New two-panel MainLayout**: Header (logo + connection status) → Left panel (~65%, chat messages) + Right panel (~35%, browser + tools)
- **Logo component**: 220px width from `frontend/public/logo.png`, hover opacity effect
- **StatusIndicator**: Green/red/amber glow dots with "Backend Connected/Disconnected" labels, auto-polls `/docs` every 15s
- **MessageBubble**: Markdown rendering, code blocks with language label + copy button, inline code styling, link styling, timestamp on hover, fade-in animation
- **InputArea**: Auto-resize textarea (3-8 lines, max 200px), Ctrl+Enter send shortcut, send icon button, disabled state styling
- **TypingIndicator**: Three animated bounce dots for agent thinking state
- **BrowserVisualizer**: Clean empty state (camera SVG + "Waiting for a browser task...") instead of raw "No screenshot available"
- **Enhanced globals.css**: Inter font, custom scrollbar (thin, dark), fadeIn/slideUp keyframe animations
- **ChatInterface rewrite**: Conversation history (user + agent messages), agent status indicator, events rendered inline, right panel with browser + terminal + tool execution log
- `Tailwind config`: preserved JetBrains Mono font family
- `.gitignore`: added `node_modules/`, `.next/`, `*.tsbuildinfo`

**Design Specs:**
- Dark theme: `zinc-950` background, `zinc-800/50` agent bubbles, `indigo-600/20` user bubbles
- Indigo accent for send button, amber for tool names, emerald for success
- Right panel: `w-[420px]` fixed width with scroll
- Font: Inter (body) + JetBrains Mono (code)

**Audit Trail:**
- Commit: [`112fba7`](https://github.com/tariqtharwat-OPS/Moza/commit/112fba7)
- 14 files changed, 2051 insertions, 202 deletions
- New files: `MainLayout.tsx`, `InputArea.tsx`, `Logo.tsx`, `MessageBubble.tsx`, `StatusIndicator.tsx`, `TypingIndicator.tsx`, `public/logo.png`
- All 81 backend tests pass. Frontend build succeeds.

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

### Phase 4.2: Implement Conversation Certification
- Implement the ConversationCapability class extending Capability ABC
- Execute certification against the Conversation contract
- Capture evidence (screenshots, traces, timing)
- Report CertificationResult

### Phase 5: Production & Polish
- Plugin system setup
- Sandbox security (Docker/gVisor)
- UI Polish

### Key Constraints for Next Agent
- **Read REGRESSION_FREEZE.md before writing any code.** All frozen benchmarks are PERMANENT.
- **No backend changes unless explicitly approved** (Regression Freeze active).
- **Frontend changes are allowed** but must be verified with `next build` before committing.
- No single file should exceed ~250 lines (backend) or ~450 lines (frontend components).
- Screenshot base64 data (~280KB) must be stripped from LLM tool messages (existing fix in `litellm_tool_agent.py`).
- Playwright headless Chromium required for browser tests.
- `dom.get_url()` is a sync property (not async).
- The frontend MUST be developed on an **NTFS drive** (FAT32/exFAT causes Node.js build failures).

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
| `backend/tests/e2e/test_agent_behavior_patterns.py` | E2E behavior pattern tests (greeting, simple Q, tool task, mixed, Arabic) |
| `backend/tests/e2e/test_real_browser_ui.py` | Real-browser CORS + UI interaction E2E test |
| `RUNNING_GUIDE.md` | Quick-start guide with NTFS warning, CORS, troubleshooting, agent behavior patterns |

---

## 6. How to Run

### Critical: NTFS Requirement
> **⚠️ The project MUST reside on an NTFS drive.** Node.js v24+ fails with `EISDIR` errors on FAT32/exFAT. If your `npm install` or `next build` crashes with `Error: EISDIR: illegal operation on a directory, readlink`, move the project to an NTFS drive.

### Backend (FastAPI + Uvicorn)

```bash
cd backend
set PYTHONPATH=backend
python -m uvicorn moza.main:app --host 0.0.0.0 --port 8000
```

### Frontend (Next.js 15 + React 19)

```bash
cd frontend
npm install --prefer-offline --no-audit --no-fund
npm run dev
```

> **Note:** `--prefer-offline --no-audit --no-fund` are required on first install to avoid npm audit/fund checks that can hang on slow networks.

Open **http://localhost:3000** in a browser. The backend must be running on port 8000.

### Running Tests

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
- The benchmark fixtures are at `backend/tests/fixtures/research/`

### Verifying the Frontend Build

```bash
cd frontend
npm run build
```

A successful build produces:
```
✓ Compiled successfully in ~19s
✓ Generating static pages (4/4)
Route (app)                                 Size  First Load JS
┌ ○ /                                     4.7 kB         108 kB
└ ○ /_not-found                            993 B         104 kB
```

---

## 7. Full Audit Trail (Git History)

| Date | Commit | Description |
|------|--------|-------------|
| 2026-07-26 | [`b6a00a4`](https://github.com/tariqtharwat-OPS/Moza/commit/b6a00a4) | **Phase 4.1** — Capability Contract Model (Conversation Contract + Minimal Base Class) |
| 2026-07-26 | [`602d9b2`](https://github.com/tariqtharwat-OPS/Moza/commit/602d9b2) | **Phase 4.0** — Executive Mind, Workspace UI & Capability Certification |
| 2026-07-26 | [`53d92df`](https://github.com/tariqtharwat-OPS/Moza/commit/53d92df) | **Strategic Pivot** — benchmarks/ with 4 YAML capability specs |
| 2026-07-26 | [`4917753`](https://github.com/tariqtharwat-OPS/Moza/commit/4917753) | **Strategic Pivot** — TEST_STRATEGY.md with Capability Certification Matrix |
| 2026-07-26 | [`112fba7`](https://github.com/tariqtharwat-OPS/Moza/commit/112fba7) | **Phase 3.3.5 Patch** — Build fix + professional UI redesign + logo |
| 2026-07-26 | [`e0caad7`](https://github.com/tariqtharwat-OPS/Moza/commit/e0caad7) | **Phase 3.3.5 Patch** — stricter greeting detection, fs error messages, UI empty state |
| 2026-07-26 | [`3068532`](https://github.com/tariqtharwat-OPS/Moza/commit/3068532) | **Agent Behavior Audit** — fix tool overuse for simple conversational tasks |
| 2026-07-26 | [`353f3eb`](https://github.com/tariqtharwat-OPS/Moza/commit/353f3eb) | **CORS + E2E** — CORSMiddleware, real-browser test proving zero CORS errors |
| 2026-07-26 | [`10443f5`](https://github.com/tariqtharwat-OPS/Moza/commit/10443f5) | **Docs** — Ultimate Product Vision, NTFS requirement, running guide |
| 2026-07-26 | [`b803349`](https://github.com/tariqtharwat-OPS/Moza/commit/b803349) | **Build Fixes** — Frontend E2E audit, resolve all build errors |
| 2026-07-26 | [`45cf31e`](https://github.com/tariqtharwat-OPS/Moza/commit/45cf31e) | **Orphan Fix** — remove orphan code from handleSubmit |
| 2026-07-26 | [`9bdaa7a`](https://github.com/tariqtharwat-OPS/Moza/commit/9bdaa7a) | **Phase 3.3** — Frontend E2E Integration (chat, terminal, browser, approval) |
| 2026-07-25 | [`f41a96c`](https://github.com/tariqtharwat-OPS/Moza/commit/f41a96c) | **Regression Freeze** — Phase 3.2.5, all canonical benchmarks pass |
| 2026-07-25 | [`ce42277`](https://github.com/tariqtharwat-OPS/Moza/commit/ce42277) | **SSOT** — PROJECT_STATE.md as single source of truth |
| 2026-07-25 | [`54e19f2`](https://github.com/tariqtharwat-OPS/Moza/commit/54e19f2) | **Phase 3.2** — Autonomous Research Benchmark |
| 2026-07-25 | [`0492a34`](https://github.com/tariqtharwat-OPS/Moza/commit/0492a34) | **Phase 3.1** — Live E2E browser benchmark |
| 2026-07-25 | [`401b6fd`](https://github.com/tariqtharwat-OPS/Moza/commit/401b6fd) | **Phase 3.0** — Abstract BrowserEngine, modular BrowserTool |
| 2026-07-25 | [`1682a82`](https://github.com/tariqtharwat-OPS/Moza/commit/1682a82) | **Phase 2.14** — Backend Replay API |
| 2026-07-24 | [`c2a3d6b`](https://github.com/tariqtharwat-OPS/Moza/commit/c2a3d6b) | **Phase 2.13** — Software Engineer Benchmark with failure-recovery |
| 2026-07-24 | [`21120f3`](https://github.com/tariqtharwat-OPS/Moza/commit/21120f3) | **Phase 2.12** — Recovery Loop for tool failures |
| 2026-07-24 | [`722f866`](https://github.com/tariqtharwat-OPS/Moza/commit/722f866) | **Phase 2.11** — ContextBuilder |
| 2026-07-24 | [`8f1d906`](https://github.com/tariqtharwat-OPS/Moza/commit/8f1d906) | **Phase 2.10** — ReAct loop with max_steps |

**Repository:** https://github.com/tariqtharwat-OPS/Moza

---

## 8. Controlled Evolution Architecture (Self-Improvement Framework)

> MOZA's self-improvement is strictly governed to remain safe, auditable, and human-approved.

### 8.1 Three-Tier Deployment Pipeline

```
  [Experimental]  ->  [Candidate]  ->  [Stable]
      |                  |                |
  Agent proposes     Passes all        Human merges
  & tests changes    Canonical         after review
                     Benchmarks
```

| Tier | Description | Gate |
|------|-------------|------|
| **Experimental** | Agent proposes changes, runs tests, iterates autonomously. May break things. No user-facing impact. | None (agent autonomy) |
| **Candidate** | Changes pass ALL Canonical Benchmarks + existing 87 tests. Ready for human review. | Automated: 100% benchmark pass |
| **Stable** | Merged to `main` ONLY via explicit human approval (`manager-approve` in commit). | Human: manager sign-off |

### 8.2 Four Sources of Evolution

| Source | Description | How It Feeds In |
|--------|-------------|-----------------|
| **1. Research** | arXiv, new AI papers, academic publications | Agent reads paper summaries, extracts actionable patterns |
| **2. Open Source Analysis** | OpenHands, Cline, LangChain - analyzing patterns, not copying | Agent analyzes architecture docs, PRs, and issue discussions |
| **3. Benchmarks** | SWE-bench, Terminal-bench, our own 6 E2E tests | Agent runs benchmarks, identifies weaknesses, proposes fixes |
| **4. Self-Analysis** | Internal telemetry - token consumption, tool failure rates, unused modules, error logs | Agent audits telemetry daily, generates optimization proposals |

### 8.3 Evolution Backlog (Proposal Format)

Every proposed improvement MUST document all of the following before any branch is created:

```yaml
PROPOSAL: [Short Name]
STATUS: [Accepted | Rejected | Need Review]
PROBLEM: [What is broken or suboptimal?]
EVIDENCE: [Link to telemetry, benchmark failure, research paper]
PROPOSAL: [What change does the agent suggest?]
RISK: [What could go wrong? Regression risk assessment]
EXPECTED_BENEFIT: [Quantified metrics: % speedup, % fewer errors]
```

The backlog is managed via GitHub Issues with label `evolution-proposal`.

### 8.4 Explicit Prohibitions

| Prohibited | Rationale |
|------------|-----------|
| Self-modification outside `Experimental` tier | Prevents untested changes from reaching users |
| Direct `main` commits by agent | Human oversight required for all stable changes |
| Deleting or modifying Canonical Benchmarks without review | Preserves regression freeze integrity |
| Auto-merging without human approval | Safety-critical: agent cannot self-approve |

---

## 9. Capability Certification Framework

> **Primary quality metric:** Number of certified capabilities (not test count).

### 9.1 Certification Process

1. **Define** the capability benchmark spec (YAML in `benchmarks/`)
2. **Implement** the test harness and any required support code
3. **Execute** the Layer 6 Canonical Benchmark on `main`
4. **Certify** - update Capability Certification Matrix in `TEST_STRATEGY.md`
5. **Freeze** - no regression allowed; benchmark becomes permanent quality gate

### 9.2 Current Certification Status

| Metric | Value |
|--------|-------|
| Total capabilities defined | 18 |
| Certified (checkmark) | 9 |
| Not yet certified (x) | 9 |
| YAML benchmark specs | 4 (`benchmarks/001` through `004`) |
| Test strategy document | `TEST_STRATEGY.md` |

### 9.3 Future Capability Roadmap

| Phase | Capability to Certify | Benchmark Spec |
|-------|----------------------|----------------|
| 3.4 | Vision-Enhanced Browser Reasoning | `benchmarks/005_vision_reasoning.yaml` (TBD) |
| 4.0 | Long/Short-Term Memory | `benchmarks/006_memory_rag.yaml` (TBD) |
| 4.5 | Approval Flow (Human-in-Loop) | `benchmarks/007_approval_flow.yaml` (TBD) |
| 5.0 | Self-Improvement (Controlled Evolution) | `benchmarks/008_self_improvement.yaml` (TBD) |
| 5.5 | Multi-Agent Orchestration | `benchmarks/009_multi_agent.yaml` (TBD) |
