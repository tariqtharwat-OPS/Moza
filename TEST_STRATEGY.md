# MOZA Test Strategy & Capability Certification Framework

> Replaces "counting passing tests" with "certifying real-world capabilities."
> **Version:** 2.0 — Phase 4.0 (Executive Mind + Workspace UI)

---

## 1. Current Test Inventory Audit

### 1.1 Existing Test Categories

| Category | Count | Location | Assessment |
|----------|-------|----------|------------|
| **Unit — Approval Service** | 5 | `tests/unit/test_approval_service.py` | ✅ Solid — tests approve/reject/invalid flows with custom test agents |
| **Unit — Browser Tool** | 7 | `tests/unit/test_browser_tool.py` | ✅ Solid — covers registration, metadata, missing params, unknown actions, lifecycle, cleanup |
| **Unit — Capability Manager** | 11 | `tests/unit/test_capability_manager.py` | ✅ Solid — covers allow/deny, per-agent configs, tool execution gating |
| **Unit — Context Builder** | 9 | `tests/unit/test_context_builder.py` | ✅ Solid — covers all 7 sections, empty states, edge cases |
| **Unit — Environment** | 16 | `tests/unit/test_environment.py` | ✅ Solid — covers 6 sub-domains, backward compat, serialization, resource manager |
| **Unit — Event Recorder** | 5 | `tests/unit/test_event_recorder.py` | ✅ Solid — covers record/replay, nonexistent sessions, multi-event |
| **Unit — Groq Config** | 9 | `tests/unit/test_groq_config.py` | ✅ Solid — covers provider config, agent config, env example validation |
| **Integration — E2E Flow** | 13 | `tests/integration/test_e2e_flow.py` | ✅ Solid — covers SSE stream, tool execution, approval flow, event recorder |
| **Integration — Replay API** | 6 | `tests/integration/test_replay_api.py` | ✅ Solid — covers list, get, events, replay with seeded data |
| **E2E — Real Browser UI** | 2 | `tests/e2e/test_real_browser_ui.py` | ✅ Good — CORS preflight + real browser interaction (requires servers running) |
| **E2E — Agent Behavior Patterns** | 6 | `tests/e2e/test_agent_behavior_patterns.py` | ⚠️ New — covers greeting, simple Q, tool task, mixed, Arabic, casual greeting (requires servers running) |
| **E2E — Frontend Runtime Integrity** | 2 | `frontend/tests/e2e/test_frontend_runtime_integrity.py` | ✅ Verifies zero 404s on core JS/CSS assets, logo/chat visible, no console errors |
| **E2E — Executive Mind & UI Audit** | 2 | `frontend/tests/e2e/test_executive_intent_and_ui_audit.py` | ✅ Headed mode — proves "اهلا" triggers ZERO tool calls, UI layout integrity |
| **Unit — Intent Classifier** | 13 | `tests/unit/test_intent_classifier.py` | ✅ New — covers Arabic/English greetings, short questions, task detection |
| **Live — Benchmarks** | 5 | `tests/live/` | ✅ Canonical — recovery, software engineer, browser live, autonomous research, multi-step agent |
| **Total** | **94** | | |

### 1.2 Redundancy & Weakness Flags

| Issue | File(s) | Recommendation |
|-------|---------|----------------|
| **Mock agent used for E2E coverage** | `test_e2e_flow.py` uses `_E2ETestAgent` (not real LLM) | Acceptable for unit/integration — real LLM is tested via live benchmarks |
| **E2E tests require running servers** | `tests/e2e/*.py` | Acceptable — browser E2E inherently needs frontend + backend; document as hard requirement |
| **No vision/approval/memory coverage** | N/A | Deliberate — those capabilities are not implemented yet |
| **No performance benchmarks** | N/A | Future: add latency/throughput/token-efficiency metrics |
| **No stress/load tests** | N/A | Future: add concurrent session, large context, rapid tool-call tests |

---

## 2. Capability Certification Matrix

> **Primary quality metric:** Number of certified capabilities (not test count).
> Each capability is proven by a Canonical Benchmark that exercises the full stack.

| # | Capability | Status | Proved By | Certified Since |
|---|------------|--------|-----------|-----------------|
| 1 | **Direct Conversational Response** | ✅ Certified | `test_agent_behavior_patterns.py` (greeting, simple Q, Arabic, casual greeting) | Phase 3.3.5 |
| 2 | **Tool Selection Intelligence** | ✅ Certified | `test_agent_behavior_patterns.py` (tool task, mixed interaction) | Phase 3.3.5 |
| 3 | **Filesystem Read/Write/List** | ✅ Certified | Phase 2.13 Software Engineer Benchmark | Phase 3.2.5 |
| 4 | **Terminal Command Execution** | ✅ Certified | Phase 2.12 Recovery Loop + Phase 2.13 SWE Bench | Phase 3.2.5 |
| 5 | **Browser Navigation & Extraction** | ✅ Certified | Phase 3.1 Browser Live + Phase 3.2 Autonomous Research | Phase 3.2.5 |
| 6 | **Multi-Page Research Synthesis** | ✅ Certified | Phase 3.2 Autonomous Research Benchmark | Phase 3.2.5 |
| 7 | **Recovery from Tool Failure** | ✅ Certified | Phase 2.12 Recovery Loop Benchmark | Phase 3.2.5 |
| 8 | **LLM Error Resilience** | ✅ Certified | Phase 3.2 auto-retry on Groq 400 | Phase 3.2.5 |
| 9 | **SSE Real-Time Streaming** | ✅ Certified | Phase 3.3 Frontend E2E tests | Phase 3.3 |
| 10 | **Multi-Step ReAct Reasoning** | ✅ Certified | Phase 2.10 Multi-Step Agent test | Phase 3.2.5 |
| 11 | **Approval Flow (Human-in-Loop)** | ✗ Not Certified | Approval Service implemented but no Canonical Benchmark | — |
| 12 | **Capability Gating** | ✗ Not Certified | Capability Manager implemented but no Canonical Benchmark | — |
| 13 | **Vision-Enhanced Reasoning** | ✗ Not Certified | Not implemented | — |
| 14 | **Long/Short-Term Memory** | ✗ Not Certified | Not implemented | — |
| 15 | **Computer Use (OS-level)** | ✗ Not Certified | Not implemented | — |
| 16 | **Multi-Agent Orchestration** | ✗ Not Certified | Not implemented | — |
| 17 | **Self-Improvement (Controlled Evolution)** | ✗ Not Certified | Architecture defined, not implemented | — |
| 18 | **CORS & Network Resilience** | ✅ Certified | `test_real_browser_ui.py` CORS preflight + zero-error console check | Phase 3.3 |
| 19 | **Frontend Runtime Integrity** | ✅ Certified | `frontend/tests/e2e/test_frontend_runtime_integrity.py` — zero 404s on core JS/CSS assets, logo/chat visible, clean browser console | Phase 3.3.5 Patch |
| 20 | **Executive Mind Intent Classification** | ✅ Certified | `classify_intent()` in `intent_classifier.py` — orchestrator-level deterministic routing, "اهلا" → 0 tool calls proven by `test_executive_intent_and_ui_audit.py` | Phase 4.0 |
| 21 | **Workspace UI (3-Panel Layout)** | ✅ Certified | `MainLayout.tsx` — 250px sidebar + center chat + 300px collapsible execution panel; Welcome Card, blended logo, Recent Sessions | Phase 4.0 |

---

## 3. Layered Testing Model (Layers 0–6)

```
Layer 6: Canonical Capability Benchmarks  ← CERTIFICATION GATE
 Layer 5: Frontend E2E (Playwright)
  Layer 4: Backend API (FastAPI routes + SSE)
   Layer 3: Orchestrator (Task lifecycle + Event Bus)
    Layer 2: Agent Loop (ReAct + Tool Calls)
     Layer 1: Individual Tools (Filesystem, Terminal, Browser)
      Layer 0: Utilities (Config, Models, Event Recorder)
```

### Layer 0 — Utilities
- **What:** Config models, Pydantic schemas, Event definitions, EventRecorder, Environment abstraction
- **How tested:** Unit tests with no dependencies
- **Frameworks:** pytest, asyncio-mode=auto
- **Test files:** `tests/unit/test_groq_config.py`, `tests/unit/test_environment.py`, `tests/unit/test_event_recorder.py`

### Layer 1 — Individual Tools
- **What:** FilesystemTool, TerminalTool, BrowserTool (each in isolation)
- **How tested:** Unit tests with tool-specific fixtures (temp dirs, mock pages, etc.)
- **Frameworks:** pytest, Playwright (for browser), tempfile for filesystem
- **Test files:** `tests/unit/test_browser_tool.py`

### Layer 2 — Agent Loop
- **What:** ReAct loop, tool selection, recovery from tool errors
- **How tested:** Integration tests with mock agents + real tools; live tests with real LLM
- **Frameworks:** pytest, LiteLLM (live), Custom Test Agents
- **Test files:** `tests/integration/test_e2e_flow.py`, `tests/live/test_recovery_loop.py`, `tests/live/test_multi_step_agent.py`

### Layer 3 — Orchestrator
- **What:** Task lifecycle (PENDING→RUNNING→COMPLETED/FAILED), EventBus pub/sub, capability gating, approval flow
- **How tested:** Integration tests with custom agents triggering state transitions
- **Frameworks:** pytest, asyncio
- **Test files:** `tests/integration/test_e2e_flow.py` (approval + state machine tests), `tests/unit/test_approval_service.py`, `tests/unit/test_capability_manager.py`

### Layer 4 — Backend API
- **What:** FastAPI routes (`/v1/task/execute`, `/v1/task/{id}/approve`, `/v1/sessions/...`), SSE streaming, replay
- **How tested:** Integration tests with httpx ASGI transport (no real HTTP server)
- **Frameworks:** pytest, httpx, ASGITransport
- **Test files:** `tests/integration/test_e2e_flow.py` (SSE tests), `tests/integration/test_replay_api.py`

### Layer 5 — Frontend E2E
- **What:** Next.js UI rendering, event stream consumption, BrowserVisualizer, TerminalComponent, InputArea
- **How tested:** Real browser (Playwright) navigating to localhost:3000, simulating user input, verifying DOM
- **Frameworks:** Playwright (sync API), pytest
- **Test files:** `tests/e2e/test_real_browser_ui.py`, `tests/e2e/test_agent_behavior_patterns.py`, `frontend/tests/e2e/test_frontend_runtime_integrity.py`
- **Requires:** Both backend AND frontend servers running

### Layer 6 — Canonical Capability Benchmarks (CERTIFICATION GATE)
- **What:** Full-stack capabilities that prove the agent can complete realistic tasks autonomously
- **How tested:** Live E2E with real LLM (Groq/OpenRouter), real Playwright browser, real terminal subprocess
- **Frameworks:** pytest, LiteLLM, Playwright, live HTTP servers (for fixtures)
- **Test files:** `tests/live/test_recovery_loop.py`, `tests/live/test_software_engineer_benchmark.py`, `tests/live/test_browser_live_benchmark.py`, `tests/live/test_autonomous_research_benchmark.py`
- **Certification Rule:** A capability is certified ONLY when its Layer 6 benchmark passes on `main`

---

## 4. Proposed Benchmark Structure (YAML-Driven)

### 4.1 Rationale

Currently, each benchmark is a standalone Python test file. Moving forward, benchmarks should be defined by **YAML spec files** that describe:
- What capability is being certified
- Exact steps the agent must perform
- Exit criteria (assertions)
- Expected artifacts

This enables:
- Non-developers to define benchmarks
- Auto-generation of test harness code
- Benchmark portability across agent implementations
- Clear pass/fail criteria per capability

### 4.2 Proposed YAML Schema

```yaml
capability: "string"           # Capability name from the matrix
version: "1.0.0"               # Benchmark spec version
description: "..."             # Human-readable description
user_story: "As a [role], I want to [goal] so that [benefit]."

required_capabilities:
  - "Capability A"
  - "Capability B"

required_tools:
  - "filesystem"
  - "terminal"

steps:
  - id: "step-1"
    description: "User sends greeting"
    input:
      type: "chat"
      content: "hi how are you?"
    expected:
      tool_calls: 0
      response_contains: ["great", "fine", "hello", "hi"]
      max_duration_ms: 15000

  - id: "step-2"
    description: "User requests file creation"
    input:
      type: "chat"
      content: "Create a file named test.txt"
    expected:
      tool_calls: 1
      tool_names: ["filesystem"]
      response_contains: ["created", "written"]
      max_duration_ms: 30000

exit_criteria:
  all_steps_pass: true
  zero_console_errors: true
  zero_network_errors: true
  artifacts:
    - path: "test.txt"
      must_exist: true
      min_size_bytes: 1

certification_rules:
  type: "strict"
  fails_if:
    - "tool_invoked_for_greeting"
    - "console_error_detected"
    - "timeout_exceeded"
```

### 4.3 Future: YAML → Test Harness

The YAML specs in `benchmarks/` will eventually drive a test harness engine that:
1. Parses the YAML spec
2. Connects to the backend API
3. Sends the specified chat inputs
4. Intercepts SSE events via EventBus subscription
5. Validates tool calls, responses, timing, and artifacts
6. Produces a structured certification report

This harness is **Phase 4.5** and NOT implemented yet. The current YAML files serve as executable specifications.

---

## 5. Regression Freeze Protocol

> A capability is **frozen** once certified. No code change may break a certified capability.

| Rule | Detail |
|------|--------|
| **Frozen capabilities** | See Capability Certification Matrix (✅ Certified rows) |
| **Breach penalty** | PR rejected. Fix must be submitted with updated benchmark. |
| **Emergency override** | Only by explicit `manager-approve` in commit message + 2 reviewer sign-off |
| **New capability rule** | Must include YAML spec + Canonical Benchmark before merging |
| **Test regression rule** | Layer 0–5 tests must pass at 100% on every PR. Layer 6 benchmarks must pass before release. |

---

## 6. Tooling & CI Requirements

| Tool | Purpose | Status |
|------|---------|--------|
| pytest | Test runner | ✅ Active |
| Playwright | Browser automation | ✅ Active |
| httpx (ASGITransport) | Backend API integration tests | ✅ Active |
| YAML spec parser | Benchmark definition (future) | ✗ Planned |
| Benchmark runner | Auto-execute YAML specs (future) | ✗ Planned |
| CI (GitHub Actions) | Automated PR validation | ✗ Planned |
| Coverage reporting | Line/branch coverage per layer | ✗ Planned |
| Performance metrics | Latency p50/p95/p99, token consumption | ✗ Planned |
