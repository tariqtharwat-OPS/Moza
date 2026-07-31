# GOVERNANCE NOTICE

This Execution Plan is governed by and strictly subordinate to the `docs/MOZA_MASTER_PLAN.md`.

All execution steps, feature additions, and architectural decisions must strictly align with the Architectural Principles, Capability Contracts, and Quality Gates defined in the Master Plan. Any conflict between this document and the Master Plan must be resolved in favor of the Master Plan for architectural matters, and an ADR must be raised if unresolved.

---

# GOVERNANCE ALIGNMENT NOTE

**Status:** Aligned with Master Plan v1.0-RATIFIED  
**Date:** 2026-07-28  
**Next Immediate Task:** A.2 — Complete State Machine Transitions (5 missing transitions)  
**Previous Version:** v4.0 (archived at `docs/archive/MOZA_EXECUTION_PLAN_v4.md`)

This Execution Plan retains all v4.0 implementation steps, timelines, and technical specifications. The Governance Notice above establishes the hierarchy. All future updates to this document must comply with the Master Plan's Evolution Governance rules (Section 18).

---

# MOZA AI Operating System — Final Execution Blueprint v4.0

## Evolution Levels Architecture | Build on Existing | Zero Regression | Incremental Evolution

**Version:** 4.0 (Final — Operational Manual for Coding Agents)  
**Date:** 2026-07-27  
**Repository:** https://github.com/tariqtharwat-OPS/Moza  
**Status:** LOCKED — This is the single source of truth. No architectural redesigns. All future work evolves the existing system.

---

## 📜 Supreme Architectural Rule

**MOZA is NOT a new project. The current repository IS the production baseline.**

This execution plan is NOT a roadmap for building MOZA.  
It is a roadmap for **EVOLVING the existing MOZA** into the final vision.

### Absolute Constraints

1. **Never replace an existing subsystem if it can be evolved.**
2. **Always extend. Always wrap. Always refactor gradually. Never rewrite.**
3. **The application MUST remain usable after every completed step.**
4. **No "big bang" rewrites. No temporary broken states. No "we will rebuild this later."**
5. **Every change must be incremental. Every level must finish with a fully working application.**

### Preservation Mandate

If MOZA can currently:
- ✅ Chat naturally (Arabic/English)
- ✅ Use tools (Filesystem, Terminal, Browser)
- ✅ Browse websites and extract data
- ✅ Write files and execute commands
- ✅ Stream responses in real-time
- ✅ Recover from tool failures
- ✅ Classify intent deterministically

Then **every future level MUST preserve these capabilities** while adding new ones.

---

## 🎯 Project Vision

MOZA is an **AI Operating System** — a cognitive platform that understands human intent, plans, executes, learns, and evolves.

**Ultimate Goal:** A digital person that works alongside you every day, knows your world as well as you do, and can eventually participate in its own development under human supervision.

**Self-Development Readiness:** If human development stops after two years, MOZA must be capable of:
- Suggesting improvements
- Discovering new technologies
- Comparing itself with competitors
- Identifying gaps
- Proposing new plugins
- Writing code
- Updating documentation
- Developing itself in an organized, supervised manner

---

## 🏗️ Architecture Philosophy

### Core Principle: "Nothing is non-extensible"

Every component is built as **Interface + Registry + Contract**, not a fixed implementation.

**Example:**
- ❌ **Wrong:** `BrowserTool` as a direct class
- ✅ **Correct:** `BrowserCapability` interface + `BrowserRegistry` + `BrowserContract`

This ensures MOZA can later:
- Add `PlaywrightBrowser`, `PuppeteerBrowser`, `ChromeDevToolsBrowser` as plugins
- Switch between them dynamically
- Develop itself by adding new capabilities

### Build Smart on Existing

- **Reuse > Refactor > Rewrite (never)**
- Every implementation must build on the existing system
- No "replace everything"
- No architecture reset
- No large refactors that temporarily break the application
- MOZA must remain usable after every approved implementation step

### Incremental Stability

Every step must produce a working system:
- Application runs
- Tests pass
- Browser demo works
- Existing capabilities continue working

No unfinished half-built architecture. No long implementation branches.

---

## ⚖️ Core Principles

1. **The LLM is a replaceable CPU. Everything else is MOZA.** Intelligence lives in architecture, not the model.
2. **No regression, ever.** A certified capability that breaks is a project halt.
3. **Capability before feature.** A component without a proven capability is technical debt.
4. **Build smart on existing.** Reuse and refactor. Never rewrite from scratch.
5. **Confidence ≥ 95% to proceed.** No exceptions.
6. **Constitution is immutable.** Identity, Golden Rules, and Forbidden Behaviors are hard-coded guards, not prompts.
7. **Extensibility is mandatory.** Every component must support future plugins and self-development.
8. **Self-Development is a future capability.** The architecture must prepare for it from the beginning, but actual implementation comes only when the foundation is mature.

---

## 🚫 Immutable Rules

These rules cannot be overridden by any implementation decision:

1. **Never break existing functionality.** Everything that currently works must continue working.
2. **Build incrementally.** Every step must produce a working system.
3. **Architecture first, implementation second.** Define contracts and interfaces before coding.
4. **Extensibility is mandatory.** Prefer Interface, Registry, Contract, Plugin, Capability, Event over direct coupling.
5. **Self-Development is prepared for from day one.** Everything before it should make self-development easy.
6. **No architectural redesigns after this document.** Future additions enter as new Capabilities within this framework.
7. **The Coding Agent must NEVER improvise outside this document.** It must read this file before every implementation cycle.
8. **The Coding Agent must NEVER continue automatically.** It must wait for explicit user approval before starting the next task.

---

## 📊 Current State Analysis (Production Baseline)

### What Works Today (As-Is)

| Component | Status | Notes |
|-----------|--------|-------|
| LLM Gateway | ✅ Working | Supports Groq/OpenRouter/Anthropic/Ollama/vLLM/LM Studio |
| Agent Loop | ✅ Working | ReAct while loop, max_steps, tool schema builder, error resilience |
| Intent Classifier | ✅ Working | Deterministic regex-based, Arabic/English, zero LLM cost |
| Orchestrator | ✅ Working | Task lifecycle, approval flow (basic), event routing |
| Event Bus | ✅ Working | Pub/Sub + JSONL persistence to disk |
| Context Builder | ✅ Working | 7-section dynamic prompt injection |
| Tool Registry | ✅ Working | BaseTool ABC, capability gating (basic), load/unload/cleanup |
| Browser Engine | ✅ Working | ABC + Playwright headless, modular components |
| Filesystem Tool | ✅ Working | Read/write/list with safety metadata |
| Terminal Tool | ✅ Working | Async subprocess with timeout, cleanup |
| Session Manager | ✅ Working | Replay API, 4 endpoints, event reading |
| Capability Base | ✅ Working | ABC with 3 methods, MaturityLevel enum, CertificationResult |
| Frontend | ✅ Working | ChatInterface, BrowserVisualizer, TerminalComponent, MainLayout |
| Desktop | ⚠️ Skeleton | Electron shell exists but minimal |

### Certified Capabilities (11/21)

| # | Capability | Maturity | Proved By |
|---|-----------|----------|-----------|
| 1 | Direct Conversational Response | PRODUCTION_READY (4) | test_agent_behavior_patterns.py |
| 2 | Tool Selection Intelligence | PRODUCTION_READY (4) | test_agent_behavior_patterns.py |
| 3 | Filesystem Read/Write/List | PRODUCTION_READY (4) | Phase 2.13 SWE Bench |
| 4 | Terminal Command Execution | PRODUCTION_READY (4) | Phase 2.12 + 2.13 |
| 5 | Browser Navigation & Extraction | PRODUCTION_READY (4) | Phase 3.1 + 3.2 |
| 6 | Multi-Page Research Synthesis | PRODUCTION_READY (4) | Phase 3.2 Autonomous Research |
| 7 | Recovery from Tool Failure | PRODUCTION_READY (4) | Phase 2.12 Recovery Loop |
| 8 | LLM Error Resilience | PRODUCTION_READY (4) | Phase 3.2 Groq 400 retry |
| 9 | SSE Real-Time Streaming | PRODUCTION_READY (4) | Phase 3.3 Frontend E2E |
| 10 | Multi-Step ReAct Reasoning | PRODUCTION_READY (4) | Phase 2.10 Multi-Step Agent |
| 11 | Executive Mind Intent Classification | PRODUCTION_READY (4) | intent_classifier.py + E2E |

### Frozen Regression Benchmarks (5 Canonical)

These are permanent quality gates. Every phase must run all 5 before sign-off.

1. **Recovery Loop** — Agent recovers from file-not-found, writes + reads recovery file.
2. **Software Engineer** — Agent writes tests, fixes integer division bug, verifies 4/4 pass.
3. **Browser Live (Wikipedia)** — Navigate → type → click (timeout, recovered) → extract → screenshot → save.
4. **Autonomous Research (Fixtures)** — 2 fixture pages, 4 data fields per page, structured research.md.
5. **Replay API Integration** — 6 integration tests: empty, 404, CRUD lifecycle, multi-task, events, replay.

---

## 🎯 Evolution Levels

The project is organized as **Evolution Levels**, not isolated phases. Each level represents a stable platform. Each level must answer:

- Why this level exists
- What becomes possible afterwards
- What remains immutable
- What is intentionally postponed
- Exit criteria

Only when a level becomes completely stable should the next level begin.

---

### Level A — Core Foundation (النواة)

**Duration:** 30-45 days  
**Status:** NOT STARTED

#### Why This Level Exists

This is the minimum required to achieve the final vision. Anything that would require rebuilding later must exist here. This is the immutable core that will never be redesigned.

#### Current Implementation Analysis

**What Already Exists:**
- `config.yaml` — runtime configuration
- `core/models.py` — basic `TaskStatus` enum (6 states)
- `orchestrator/orchestrator.py` — basic state transitions
- Golden Rules exist as text inside `litellm_tool_agent.py` system prompt
- `certification/capability_base.py` — basic ABC

**What Will Be Reused:**
- All existing tools (Filesystem, Terminal, Browser)
- Event Bus and Event Recorder
- Session Manager
- Intent Classifier
- LLM Gateway (LiteLLM adapter)
- Frontend components

**What Will Be Refactored:**
- `orchestrator.py` — integrate formal State Machine
- `litellm_tool_agent.py` — extract Golden Rules to guards
- `models.py` — expand TaskStatus to 8 states

**What New Components Will Be Added:**
- `constitution.yaml` — immutable identity
- `core/state_machine.py` — 8-state FSM
- `core/guards.py` — Golden Rules as code
- `core/identity.py` — constitution loader
- `plugins/` — plugin architecture
- `core/event_store.py` — event sourcing
- `core/config_manager.py` — hot-reload config
- `core/secrets_manager.py` — encrypted secrets
- `core/audit_logger.py` — immutable audit logs
- `core/backup_manager.py` — scheduled backups
- `core/health_checker.py` — health endpoints
- `core/circuit_breaker.py` — graceful degradation
- `core/api_versioning.py` — version management
- `core/rate_limiter.py` — rate limiting
- `core/migration_manager.py` — schema migrations
- `core/di_container.py` — dependency injection
- `core/feature_flags.py` — feature flag management
- Memory/Reflection/Learning/Evolution interfaces (empty)

**Why This Design Does NOT Break Existing Functionality:**
- All new components are additive
- Existing tools remain unchanged
- State Machine wraps existing transitions (no breaking changes)
- Guards run before LLM calls (non-invasive)
- Plugin architecture is opt-in (existing tools work without it)
- All existing tests continue to pass

#### What Becomes Possible Afterwards

- Adding new capabilities without modifying the core
- Swapping LLM providers dynamically
- Safe self-development (via Evolution Interfaces)
- Testing each component independently
- Replacing any implementation without breaking the system

#### What Remains Immutable

- Constitution (Identity + Golden Rules)
- Plugin Architecture (PluginManager + Interfaces)
- Event Bus + Event Sourcing
- Registry System (Tool, Capability, Provider)
- State Machine (8 States)
- Certification Framework
- Configuration System
- Secrets Management
- Audit Trail
- Backup & Recovery
- Health Checks
- Graceful Degradation
- API Versioning
- Rate Limiting
- Schema Migration
- Dependency Injection Container
- Feature Flags

#### What is Intentionally Postponed

| Postponed | Reason |
|-----------|--------|
| Memory Implementation | Interfaces sufficient now, implementation in Level C |
| Reflection Implementation | Interfaces sufficient now, implementation in Level C |
| Learning Implementation | Interfaces sufficient now, implementation in Level C |
| UI/UX Polish | Product level (Level B) |
| Security Hardening | Commercial level (Level D) |
| Performance Optimization | Commercial level (Level D) |

#### Definition of Done

- [ ] Plugin Architecture works (can add new plugin without modifying core)
- [ ] All Interfaces exist (Memory, Reflection, Learning, Evolution)
- [ ] Event Bus + Event Sourcing works
- [ ] Registry System works (Tool, Capability, Provider)
- [ ] State Machine (8 States) works with correct transitions
- [ ] Certification Framework exists (Capability ABC + CertificationResult)
- [ ] Configuration System with hot-reload
- [ ] Secrets Management with encryption
- [ ] Audit Trail with immutable logs
- [ ] Backup & Recovery works
- [ ] Health Checks with endpoints (`/health`, `/ready`)
- [ ] Graceful Degradation (Circuit Breaker + Fallback)
- [ ] API Versioning (`/v1/`, `/v2/`)
- [ ] Rate Limiting with quotas
- [ ] Schema Migration with versioning
- [ ] Dependency Injection Container
- [ ] Feature Flags with LaunchDarkly-like interface
- [ ] Constitution loads at startup
- [ ] Golden Rules Guards work (NoToolForGreeting, ContentPreservation, Clarification)
- [ ] 94+ existing tests pass
- [ ] 5 frozen benchmarks pass
- [ ] Frontend build succeeds
- [ ] Confidence Score: ≥ 95%

#### Regression Criteria

- All 94 existing tests pass
- All 5 frozen benchmarks pass
- No breakage of any certified capability (11/21)
- Frontend build without errors

#### Files to Create or Modify

**New Files:**
```
backend/moza/
├── plugins/
│   ├── __init__.py
│   ├── plugin_manager.py          # PluginManager
│   ├── interfaces.py              # CapabilityInterface, ToolInterface
│   └── registry.py                # PluginRegistry
├── core/
│   ├── state_machine.py           # 8-state FSM
│   ├── guards.py                  # Golden Rules Guards
│   ├── identity.py                # Constitution loader
│   ├── event_store.py             # Event Sourcing
│   ├── config_manager.py          # Hot-reload config
│   ├── secrets_manager.py         # Encrypted secrets
│   ├── audit_logger.py            # Immutable audit logs
│   ├── backup_manager.py          # Scheduled backups
│   ├── health_checker.py          # Health endpoints
│   ├── circuit_breaker.py         # Graceful degradation
│   ├── api_versioning.py          # Version management
│   ├── rate_limiter.py            # Rate limiting
│   ├── migration_manager.py       # Schema migrations
│   ├── di_container.py            # Dependency injection
│   └── feature_flags.py           # Feature flag management
├── memory/
│   ├── __init__.py
│   ├── memory_mesh.py             # Interface only
│   └── layers/
│       ├── __init__.py
│       └── base_layer.py          # Abstract base
├── reflection/
│   ├── __init__.py
│   └── base_reflection.py         # Interface only
├── learning/
│   ├── __init__.py
│   └── base_learning.py           # Interface only
└── evolution/
    ├── __init__.py
    └── base_evolution.py          # Interface only
```

**Modified Files:**
```
backend/moza/main.py               # Load constitution, init plugins
backend/moza/orchestrator/orchestrator.py  # Use FSM + Guards
backend/moza/tools/registry.py     # Extend with PluginRegistry
backend/moza/core/models.py        # Expand TaskStatus to 8 states
```

**Files That Must Never Be Touched:**
```
backend/moza/tools/filesystem_tool.py
backend/moza/tools/terminal_tool.py
backend/moza/tools/browser_tool.py
backend/moza/agents/litellm_tool_agent.py  # Only extract guards, don't rewrite
frontend/src/components/chat/ChatInterface.tsx
frontend/src/components/chat/BrowserVisualizer.tsx
```

#### Migration Strategy

1. Create `constitution.yaml` alongside `config.yaml`
2. Load constitution in `main.py` at startup (alongside config)
3. Create `state_machine.py` with 8 states
4. Wrap existing `orchestrator.py` transitions with FSM (no breaking changes)
5. Extract Golden Rules from `litellm_tool_agent.py` to `guards.py`
6. Keep existing prompt rules as fallback during transition
7. Gradually migrate to formal guards

#### Rollback Strategy

1. If State Machine breaks existing transitions, revert `orchestrator.py` to previous version
2. If Guards block valid operations, disable specific guard via feature flag
3. If Plugin Architecture causes issues, disable plugin loading in `main.py`
4. All new components have feature flags for safe rollback

#### Required Interfaces and Contracts

**CapabilityInterface:**
```python
class CapabilityInterface(ABC):
    @abstractmethod
    def name(self) -> str: pass
    
    @abstractmethod
    def version(self) -> str: pass
    
    @abstractmethod
    def execute(self, input: dict) -> dict: pass
    
    @abstractmethod
    def validate(self, input: dict) -> bool: pass
```

**ToolInterface:**
```python
class ToolInterface(ABC):
    @abstractmethod
    def name(self) -> str: pass
    
    @abstractmethod
    def actions(self) -> list[str]: pass
    
    @abstractmethod
    def execute(self, action: str, args: dict) -> dict: pass
    
    @abstractmethod
    def is_destructive(self) -> bool: pass
```

**ProviderInterface:**
```python
class ProviderInterface(ABC):
    @abstractmethod
    def chat(self, messages: list, **kwargs) -> dict: pass
    
    @abstractmethod
    def embed(self, text: str) -> list[float]: pass
    
    @abstractmethod
    def health_check(self) -> bool: pass
```

#### Future Expansion Points

1. **Plugin Marketplace** — Level D will add plugin store
2. **Multi-Agent** — Level C will add agent plugins
3. **Custom Capabilities** — Users can build plugins
4. **Self-Development** — MOZA will write new plugins

---

### Level B — Core Product (المنتج)

**Duration:** 45-60 days  
**Status:** NOT STARTED

#### Why This Level Exists

Without this level, MOZA is a "technically advanced system" but not a product. This level transforms the core into a real product that users can use daily.

#### Current Implementation Analysis

**What Already Exists:**
- `ChatInterface.tsx` — basic chat UI
- `BrowserVisualizer.tsx` — browser preview
- `TerminalComponent.tsx` — terminal output
- `MainLayout.tsx` — 3-panel layout
- `execution_panel` — tool execution log
- Session management (basic)

**What Will Be Reused:**
- All existing UI components
- Event Bus for real-time updates
- Session Manager for history
- Tool Registry for capability discovery

**What Will Be Refactored:**
- `ChatInterface.tsx` — add file upload, rich content
- `MainLayout.tsx` — add history sidebar, settings
- Add new routes for upload, history, export, search

**What New Components Will Be Added:**
- `FileUpload.tsx` — drag & drop file upload
- `HistorySidebar.tsx` — conversation history
- `RichContent.tsx` — code highlighting, images, PDFs
- `TaskCard.tsx` — task visualization
- `FileTree.tsx` — project structure
- `SettingsPanel.tsx` — model, temperature, theme
- `ExportMenu.tsx` — PDF, Markdown, HTML export
- `SearchBar.tsx` — global search
- Backend routes for upload, history, export, search, settings

**Why This Design Does NOT Break Existing Functionality:**
- All new UI components are additive
- Existing chat continues to work
- File upload is optional (existing text input works)
- History sidebar is collapsible (doesn't block chat)
- All existing tests continue to pass

#### What Becomes Possible Afterwards

- Users can upload files for analysis
- Users can see their previous conversations
- Responses look professional (code highlighting, images)
- Users can see progress of complex tasks
- Users can customize the system
- Users can export reports

#### What Remains Immutable

- Workspace Asset Management (File Upload)
- Conversation History System
- Rich Content Renderer
- Task Visualization System
- Settings Management
- Export/Share System
- Search Engine
- Workspace UI Framework
- Authentication (Basic)
- Session Management

#### What is Intentionally Postponed

| Postponed | Reason |
|-----------|--------|
| Memory Implementation | Intelligence level (Level C) |
| Reflection Implementation | Intelligence level (Level C) |
| Learning Implementation | Intelligence level (Level C) |
| Security Hardening | Commercial level (Level D) |
| Performance Optimization | Commercial level (Level D) |
| Mobile App | Commercial level (Level D) |

#### Definition of Done

- [ ] File Upload works (Drag & Drop + Picker)
- [ ] Conversation History UI works (Sidebar with Search)
- [ ] Rich Content Renderer works (Code, Images, PDFs)
- [ ] Task Visualization Cards work (Progress bars)
- [ ] Browser Workspace works (Live preview)
- [ ] File Tree Explorer works
- [ ] Settings Panel works (Model, Temperature, Theme)
- [ ] Export/Share works (PDF, Markdown, HTML)
- [ ] Search works (Global search)
- [ ] Workspace UI is professional (Manus-like)
- [ ] Basic Authentication works (Local auth)
- [ ] Session Management works
- [ ] Multiple Projects work
- [ ] Theme (Dark/Light) works
- [ ] Accessibility (WCAG 2.1 Basic) works
- [ ] RTL Support works
- [ ] i18n Foundation exists
- [ ] 94+ existing tests pass
- [ ] 5 frozen benchmarks pass
- [ ] Frontend build succeeds
- [ ] Confidence Score: ≥ 95%

#### Regression Criteria

- All 94 existing tests pass
- All 5 frozen benchmarks pass
- No breakage of any certified capability
- UI tests pass (Playwright)

#### Files to Create or Modify

**New Frontend Files:**
```
frontend/src/
├── components/
│   ├── upload/
│   │   ├── FileUpload.tsx
│   │   ── FilePreview.tsx
│   ├── sidebar/
│   │   ├── HistorySidebar.tsx
│   │   └── SearchBar.tsx
│   ├── chat/
│   │   ├── RichContent.tsx
│   │   ├── TaskCard.tsx
│   │   └── ExportMenu.tsx
│   ├── workspace/
│   │   ├── FileTree.tsx
│   │   └── BrowserPreview.tsx
│   └── settings/
│       ├── SettingsPanel.tsx
│       ── ThemeToggle.tsx
├── hooks/
│   ├── useFileUpload.ts
│   ├── useHistory.ts
│   └── useSettings.ts
└── utils/
    ├── i18n.ts
    └── rtl.ts
```

**New Backend Files:**
```
backend/moza/api/routes/
├── upload.py
├── history.py
├── export.py
├── search.py
└── settings.py
```

**Modified Files:**
```
frontend/src/components/chat/ChatInterface.tsx  # Add file upload, rich content
frontend/src/components/Layout/MainLayout.tsx   # Add history sidebar, settings
```

**Files That Must Never Be Touched:**
```
backend/moza/tools/filesystem_tool.py
backend/moza/tools/terminal_tool.py
backend/moza/tools/browser_tool.py
backend/moza/agents/litellm_tool_agent.py
backend/moza/orchestrator/orchestrator.py
```

#### Migration Strategy

1. Create new UI components alongside existing ones
2. Add file upload as optional feature (existing text input works)
3. Add history sidebar as collapsible panel (doesn't block chat)
4. Gradually enhance ChatInterface with rich content
5. Keep existing components working during transition

#### Rollback Strategy

1. If File Upload breaks, disable via feature flag
2. If History Sidebar causes issues, hide via CSS
3. If Rich Content breaks, fallback to plain text
4. All new features have feature flags for safe rollback

#### Required Interfaces and Contracts

**UploadInterface:**
```python
class UploadInterface(ABC):
    @abstractmethod
    async def upload(self, file: UploadFile) -> dict: pass
    
    @abstractmethod
    async def download(self, file_id: str) -> bytes: pass
    
    @abstractmethod
    async def delete(self, file_id: str) -> bool: pass
```

**HistoryInterface:**
```python
class HistoryInterface(ABC):
    @abstractmethod
    async def list_sessions(self, user_id: str) -> list[dict]: pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> dict: pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool: pass
```

#### Future Expansion Points

1. **Collaboration** — Level D will add multi-user
2. **Cloud Sync** — Level D will add synchronization
3. **Mobile** — Level D will add mobile app
4. **PWA** — Level D will add offline mode

---

### Level C — Intelligence Expansion (الذكاء)

**Duration:** 60-90 days  
**Status:** NOT STARTED

#### Why This Level Exists

This level makes the system intelligent, capable of learning from experience and adapting to the user. It transforms MOZA from a "tool" to an "intelligent assistant."

#### Current Implementation Analysis

**What Already Exists:**
- `event_recorder.py` — persists events as JSONL
- `session_manager.py` — reads recorded events
- `context_builder.py` — reads last 5 events (no retrieval, just slicing)
- `EventBus` — streams events in real-time
- `capability_base.py` — MaturityLevel, CertificationResult
- `macro_reflection.py` (stub) — generates ExperienceRecords
- `experience_layer.py` (stub) — stores experiences in SQLite

**What Will Be Reused:**
- Event Bus for real-time event streaming
- Event Recorder for persistence
- Session Manager for session data
- Context Builder (will be enhanced)
- Certification Framework for capability validation

**What Will Be Refactored:**
- `context_builder.py` — retrieve from Memory Mesh instead of simple slicing
- `event_recorder.py` — add layer tagging (conversation vs. task vs. experience)
- `orchestrator.py` — insert Micro/Macro Reflection hooks
- `macro_reflection.py` — full implementation
- `experience_layer.py` — full implementation

**What New Components Will Be Added:**
- `memory_mesh.py` — unified memory interface
- 5 memory layers (Identity, User, Experience, Conversation, Task)
- Storage backends (SQLite, JSONL, Embeddings)
- `micro_reflection.py` — per-step reflection
- `macro_reflection.py` — per-task reflection
- `consolidation.py` — experience consolidation
- `knowledge_graph.py` — SQLite + JSON knowledge graph
- `adaptive_profile.py` — user preference tracking
- `confidence_engine.py` — advanced confidence scoring
- `planner.py` — multi-step task decomposition
- `multi_agent.py` — basic agent orchestration
- New tools: Vision, Computer Use, Email, WhatsApp, ERP

**Why This Design Does NOT Break Existing Functionality:**
- Memory layers are additive (existing context slicing works as fallback)
- Reflection hooks are optional (can be disabled via feature flag)
- New tools are registered via Plugin Architecture (don't affect existing tools)
- All existing tests continue to pass

#### What Becomes Possible Afterwards

- The system remembers previous conversations (Memory Mesh)
- The system learns from mistakes (Reflection)
- The system improves with repetition (Learning)
- The system knows user preferences (Adaptive Profile)
- The system plans complex tasks (Advanced Planning)
- The system uses vision (Vision)
- The system controls the computer (Computer Use)
- The system sends emails (Email)
- The system communicates via WhatsApp
- The system integrates with ERP

#### What Remains Immutable

- Memory Mesh (5 Layers - Full Implementation)
- Reflection Engine (Micro + Macro)
- Learning Pipeline
- Knowledge Graph (SQLite + JSON)
- Adaptive Profile
- Confidence Engine (Advanced)
- Planning Engine (Advanced)
- Multi-Agent (Basic)
- Vision Capability
- Computer Use Capability
- Email Capability
- WhatsApp Capability
- ERP Capability

#### What is Intentionally Postponed

| Postponed | Reason |
|-----------|--------|
| Security Hardening | Commercial level (Level D) |
| Performance Optimization | Commercial level (Level D) |
| Marketplace | Commercial level (Level D) |
| Enterprise Features | Commercial level (Level D) |

#### Definition of Done

- [ ] Memory Mesh works (5 Layers: Identity, User, Experience, Conversation, Task)
- [ ] Reflection Engine works (Micro + Macro)
- [ ] Learning Pipeline works (Consolidation + Knowledge Graph)
- [ ] Adaptive Profile works (Personalization)
- [ ] Confidence Engine is advanced (3 sub-scores)
- [ ] Planning Engine is advanced (Multi-step decomposition)
- [ ] Multi-Agent Basic works
- [ ] Vision Capability is certified
- [ ] Computer Use Capability is certified
- [ ] Email Capability is certified
- [ ] WhatsApp Capability is certified
- [ ] ERP Capability is certified
- [ ] Knowledge Graph is queryable
- [ ] Experience Decay works
- [ ] Rule Consolidation works (3 similar → 1 rule)
- [ ] 94+ existing tests pass
- [ ] 5 frozen benchmarks pass
- [ ] Frontend build succeeds
- [ ] Confidence Score: ≥ 95%

#### Regression Criteria

- All 94 existing tests pass
- All 5 frozen benchmarks pass
- All certified capabilities (Level B) pass
- Memory tests pass
- Reflection tests pass
- Learning tests pass

#### Files to Create or Modify

**New Backend Files:**
```
backend/moza/
├── memory/
│   ├── layers/
│   │   ├── identity_layer.py
│   │   ├── user_layer.py
│   │   ├── experience_layer.py
│   │   ├── conversation_layer.py
│   │   └── task_layer.py
│   └── backends/
│       ├── sqlite_backend.py
│       ├── jsonl_backend.py
│       └── embedding_backend.py
├── reflection/
│   ├── micro_reflection.py
│   ├── macro_reflection.py
│   └── models.py
├── learning/
│   ├── consolidation.py
│   ├── knowledge_graph.py
│   ├── adaptive_profile.py
│   └── models.py
├── core/
│   ├── confidence_engine.py
│   └── planner.py
├── agents/
│   └── multi_agent.py
└── tools/
    ├── vision_tool.py
    ├── computer_use_tool.py
    ├── email_tool.py
    ├── whatsapp_tool.py
    └── erp_tool.py
```

**Modified Files:**
```
backend/moza/core/event_recorder.py  # Add layer tagging
backend/moza/orchestrator/orchestrator.py  # Add reflection hooks
backend/moza/core/context_builder.py  # Use Memory Mesh
```

**Files That Must Never Be Touched:**
```
backend/moza/tools/filesystem_tool.py
backend/moza/tools/terminal_tool.py
backend/moza/tools/browser_tool.py
frontend/src/components/chat/ChatInterface.tsx
frontend/src/components/Layout/MainLayout.tsx
```

#### Migration Strategy

1. Create Memory Mesh alongside existing context slicing
2. Keep existing context slicing as fallback during transition
3. Gradually migrate to Memory Mesh retrieval
4. Add reflection hooks as optional (can be disabled)
5. New tools register via Plugin Architecture

#### Rollback Strategy

1. If Memory Mesh causes issues, fallback to context slicing
2. If Reflection breaks, disable via feature flag
3. If new tools cause issues, unregister from Plugin Registry
4. All new features have feature flags for safe rollback

#### Required Interfaces and Contracts

**MemoryInterface:**
```python
class MemoryInterface(ABC):
    @abstractmethod
    async def store(self, layer: str, key: str, value: dict) -> bool: pass
    
    @abstractmethod
    async def retrieve(self, layer: str, query: str, top_k: int) -> list[dict]: pass
    
    @abstractmethod
    async def delete(self, layer: str, key: str) -> bool: pass
```

**ReflectionInterface:**
```python
class ReflectionInterface(ABC):
    @abstractmethod
    async def micro_reflect(self, step_result: dict) -> dict: pass
    
    @abstractmethod
    async def macro_reflect(self, task_result: dict) -> dict: pass
```

**LearningInterface:**
```python
class LearningInterface(ABC):
    @abstractmethod
    async def consolidate(self, experiences: list[dict]) -> dict: pass
    
    @abstractmethod
    async def query_knowledge(self, query: str) -> list[dict]: pass
    
    @abstractmethod
    async def update_profile(self, user_id: str, interaction: dict) -> bool: pass
```

#### Future Expansion Points

1. **Advanced Multi-Agent** — Level D will add agent orchestration
2. **Custom Learning** — Users can train the system
3. **Knowledge Sharing** — Level D will add shared knowledge
4. **Self-Development** — Level D will add evolution engine

---

### Level D — Commercial Platform (المنصة التجارية)

**Duration:** 90-120 days  
**Status:** NOT STARTED

#### Why This Level Exists

This level transforms MOZA into a professional platform that competes globally. It makes the project commercially viable and scalable.

#### Current Implementation Analysis

**What Already Exists:**
- Basic authentication (if implemented in Level B)
- Docker skeleton (if exists)
- GitHub Actions (if exists)
- Monitoring (basic logging)

**What Will Be Reused:**
- All existing capabilities (Level A, B, C)
- Plugin Architecture for marketplace
- Event Bus for analytics
- Memory Mesh for user data

**What Will Be Refactored:**
- Authentication system (enhance with OAuth, SSO)
- Deployment pipeline (add CI/CD)
- Monitoring (add Prometheus, Grafana)
- Performance (add Redis, caching)

**What New Components Will Be Added:**
- Security system (OWASP Top 10)
- Docker containerization
- CI/CD pipeline
- Monitoring (Prometheus + Grafana)
- Analytics (PostHog or Plausible)
- Marketplace system
- Plugin store
- Enterprise features (SSO, RBAC)
- Performance optimization (Redis, caching)
- Scaling (load balancing)
- Cloud sync
- Mobile app (React Native)
- Desktop polish (Electron)
- PWA (offline mode)
- Notifications
- Charts & visualizations
- Collaboration (multi-user)
- Billing & licensing
- API platform
- SDK (Python, JS)
- Developer platform
- Community extensions

**Why This Design Does NOT Break Existing Functionality:**
- Security is additive (existing auth works as fallback)
- Docker is optional (existing deployment works)
- Marketplace is opt-in (existing plugins work)
- All existing tests continue to pass

#### What Becomes Possible Afterwards

- The system is secure (Security Hardening)
- The system can be deployed (Docker, CI/CD)
- The system can be monitored (Monitoring, Analytics)
- The system can be extended (Marketplace, Plugin Store)
- The system supports teams (Enterprise Features)
- The system is performant (Caching, Scaling)
- The system is available on all platforms (Mobile, Desktop, PWA)
- The system can be sold (Billing, Licensing)

#### What Remains Immutable

- Security System (Authentication, Authorization, Encryption)
- Deployment System (Docker, CI/CD)
- Monitoring System (Prometheus, Grafana)
- Analytics System
- Marketplace System
- Plugin Store
- Enterprise Features (SSO, RBAC)
- Performance System (Redis, Caching)
- Scaling System
- Cloud Sync
- Mobile App
- Desktop Polish
- PWA
- Notifications
- Charts & Visualizations
- Collaboration (Multi-user)
- Billing & Licensing
- API Platform
- SDK
- Developer Platform
- Community Extensions

#### Definition of Done

- [ ] Security Hardening (OWASP Top 10)
- [ ] Docker containerization
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Analytics (PostHog or Plausible)
- [ ] Marketplace works
- [ ] Plugin Store works
- [ ] Enterprise Features (SSO, RBAC, Audit)
- [ ] Performance Optimization (Redis, Caching)
- [ ] Scaling (Load balancing)
- [ ] Cloud Sync
- [ ] Mobile App (React Native)
- [ ] Desktop Polish (Electron)
- [ ] PWA (Offline mode)
- [ ] Notifications
- [ ] Charts & Visualizations
- [ ] Collaboration (Multi-user)
- [ ] Billing & Licensing
- [ ] API Platform
- [ ] SDK (Python, JS)
- [ ] Developer Platform
- [ ] Community Extensions
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] Internationalization (Full i18n)
- [ ] 94+ existing tests pass
- [ ] 5 frozen benchmarks pass
- [ ] Frontend build succeeds
- [ ] Confidence Score: ≥ 95%

#### Regression Criteria

- All 94 existing tests pass
- All 5 frozen benchmarks pass
- All certified capabilities (Level B + C) pass
- Security tests pass
- Performance tests pass
- Load tests pass

#### Files to Create or Modify

**Infrastructure:**
```
docker-compose.yml
Dockerfile
.github/workflows/
├── ci.yml
├── cd.yml
└── security.yml
```

**New Backend Files:**
```
backend/moza/
├── security/
│   ├── auth.py
│   ├── encryption.py
│   └── rbac.py
├── monitoring/
│   ├── prometheus.py
│   └── grafana_dashboards/
├── analytics/
│   └── posthog.py
├── marketplace/
│   ├── store.py
│   └── plugin_registry.py
├── enterprise/
│   ├── sso.py
│   └── audit.py
├── performance/
│   ├── redis_cache.py
│   └── cdn.py
└── api/
    ── v2/
        └── ...
```

**New Frontend Files:**
```
frontend/src/
├── mobile/
│   ── ...
├── desktop/
│   └── ...
└── pwa/
    └── ...
```

**Modified Files:**
```
backend/moza/main.py  # Add security, monitoring
frontend/src/components/  # Add marketplace, settings
```

**Files That Must Never Be Touched:**
```
backend/moza/tools/filesystem_tool.py
backend/moza/tools/terminal_tool.py
backend/moza/tools/browser_tool.py
backend/moza/agents/litellm_tool_agent.py
backend/moza/orchestrator/orchestrator.py
backend/moza/memory/  # Unless extending
backend/moza/reflection/  # Unless extending
backend/moza/learning/  # Unless extending
```

#### Migration Strategy

1. Add security layer alongside existing auth
2. Keep existing auth as fallback during transition
3. Add Docker as optional deployment method
4. Add marketplace as opt-in feature
5. All new features have feature flags

#### Rollback Strategy

1. If security breaks, fallback to existing auth
2. If Docker causes issues, use existing deployment
3. If marketplace breaks, disable via feature flag
4. All new features have feature flags for safe rollback

#### Required Interfaces and Contracts

**SecurityInterface:**
```python
class SecurityInterface(ABC):
    @abstractmethod
    async def authenticate(self, credentials: dict) -> str: pass
    
    @abstractmethod
    async def authorize(self, user_id: str, resource: str) -> bool: pass
    
    @abstractmethod
    async def encrypt(self, data: str) -> str: pass
    
    @abstractmethod
    async def decrypt(self, encrypted: str) -> str: pass
```

**MarketplaceInterface:**
```python
class MarketplaceInterface(ABC):
    @abstractmethod
    async def list_plugins(self, category: str) -> list[dict]: pass
    
    @abstractmethod
    async def install_plugin(self, plugin_id: str) -> bool: pass
    
    @abstractmethod
    async def uninstall_plugin(self, plugin_id: str) -> bool: pass
```

#### Future Expansion Points

1. **AI Models** — Add new models
2. **Integrations** — Integrations with external services
3. **Custom Plugins** — Plugins from the community
4. **Self-Development** — MOZA develops itself

---

## 🔄 Execution Model

The Coding Agent will repeatedly perform this cycle:

1. **Read this Markdown file.**
2. **Locate the next unfinished task.**
3. **Implement only that task.**
4. **Run all required tests.**
5. **Run the real application.**
6. **Demonstrate the feature using the real browser while the user watches.**
7. **Verify that nothing previously working has been broken.**
8. **Update project documentation.**
9. **Commit changes.**
10. **Push to GitHub.**
11. **Write an implementation report including:**
    - Completed task
    - Modified files
    - Tests executed
    - Browser verification
    - Documentation updated
    - GitHub commit
    - GitHub links
    - Remaining tasks
12. **STOP.** Wait for explicit user approval before starting the next task.

**The Coding Agent must NEVER continue automatically.**

---

##  Execution Order

### Level A — Core Foundation (30-45 days)

**Step A.1:** Create Plugin Architecture
- Create `PluginManager`, `CapabilityInterface`, `ToolInterface`, `ProviderInterface`
- After this step, we can add any new capability without modifying the core

**Step A.2:** Implement State Machine
- Create 8-state FSM with valid transitions
- Integrate with Orchestrator

**Step A.3:** Build Golden Rules Guards
- Create `GuardEngine` with deterministic checks
- Hook into Orchestrator before LLM calls

**Step A.4:** Create Constitution Loader
- Load `constitution.yaml` at startup
- Provide identity and rules to all components

**Step A.5:** Implement Event Sourcing
- Create `EventStore` with replay capability
- Integrate with existing EventBus

**Step A.6:** Build Registry System
- Extend `ToolRegistry` with `PluginRegistry`
- Support dynamic capability registration

**Step A.7:** Create Certification Framework
- Extend `capability_base.py` with full framework
- Create `certification_runner.py` and `certification_dashboard.py`

**Step A.8:** Implement Configuration System
- Create `ConfigManager` with hot-reload
- Support runtime configuration changes

**Step A.9:** Build Secrets Management
- Create `SecretsManager` with encryption
- Secure API keys and sensitive data

**Step A.10:** Implement Audit Trail
- Create `AuditLogger` with immutable logs
- Track all system decisions

**Step A.11:** Build Backup & Recovery
- Create `BackupManager` with scheduled backups
- Protect data (SQLite, JSONL)

**Step A.12:** Implement Health Checks
- Create `HealthChecker` with endpoints (`/health`, `/ready`)
- Monitor system health

**Step A.13:** Build Graceful Degradation
- Create `CircuitBreaker` + `FallbackStrategy`
- Handle LLM failures gracefully

**Step A.14:** Implement API Versioning
- Create `APIVersioning` with `/v1/`, `/v2/`
- Support future API changes

**Step A.15:** Build Rate Limiting
- Create `RateLimiter` with quotas
- Protect from abuse

**Step A.16:** Implement Schema Migration
- Create `MigrationManager` with versioning
- Support database evolution

**Step A.17:** Build Dependency Injection Container
- Create `DIContainer` for component management
- Support dynamic component replacement

**Step A.18:** Implement Feature Flags
- Create `FeatureFlagManager` with LaunchDarkly-like interface
- Support safe feature rollout

**Step A.19:** Create Memory Interfaces
- Define `MemoryInterface` and layer interfaces
- No implementation yet, just contracts

**Step A.20:** Create Reflection Interfaces
- Define `ReflectionInterface` (Micro + Macro)
- No implementation yet, just contracts

**Step A.21:** Create Learning Interfaces
- Define `LearningInterface`
- No implementation yet, just contracts

**Step A.22:** Create Evolution Interfaces
- Define `EvolutionInterface`
- No implementation yet, just contracts

---

### Level B — Core Product (45-60 days)

**Step B.1:** Implement File Upload Component
- Create `FileUpload.tsx` with Drag & Drop
- Create backend upload API

**Step B.2:** Build Conversation History UI
- Create `HistorySidebar.tsx` with search
- Create backend history API

**Step B.3:** Implement Rich Content Renderer
- Create `RichContent.tsx` with code highlighting, images, PDFs
- Support Markdown rendering

**Step B.4:** Build Task Visualization Cards
- Create `TaskCard.tsx` with progress bars
- Show task execution status

**Step B.5:** Implement Browser Workspace
- Enhance `BrowserPreview.tsx` with live preview
- Add navigation controls

**Step B.6:** Build File Tree Explorer
- Create `FileTree.tsx` for project structure
- Integrate with Filesystem tool

**Step B.7:** Implement Settings Panel
- Create `SettingsPanel.tsx` for model, temperature, theme
- Create backend settings API

**Step B.8:** Build Export/Share System
- Create `ExportMenu.tsx` for PDF, Markdown, HTML
- Create backend export API

**Step B.9:** Implement Global Search
- Create `SearchBar.tsx` for conversations and files
- Create backend search API

**Step B.10:** Polish Workspace UI
- Make UI professional (Manus-like)
- Improve layout and styling

**Step B.11:** Implement Basic Authentication
- Create local auth system
- Protect user data

**Step B.12:** Build Session Management
- Manage multiple sessions
- Support session switching

**Step B.13:** Implement Multiple Projects
- Support project isolation
- Project-specific settings

**Step B.14:** Build Theme System
- Dark/Light theme toggle
- Theme persistence

**Step B.15:** Implement Accessibility (WCAG 2.1 Basic)
- Screen reader support
- Keyboard navigation

**Step B.16:** Build RTL Support
- Arabic language support
- Right-to-left layout

**Step B.17:** Implement i18n Foundation
- Externalize strings
- Prepare for multiple languages

---

### Level C — Intelligence Expansion (60-90 days)

**Step C.1:** Implement Memory Mesh
- Build 5 memory layers (Identity, User, Experience, Conversation, Task)
- Create storage backends (SQLite, JSONL, Embeddings)

**Step C.2:** Build Reflection Engine
- Implement Micro Reflection (after each tool step)
- Implement Macro Reflection (after task completion)

**Step C.3:** Implement Learning Pipeline
- Build Experience Consolidation
- Create Knowledge Graph (SQLite + JSON)

**Step C.4:** Build Adaptive Profile
- Track user preferences
- Personalize responses

**Step C.5:** Implement Advanced Confidence Engine
- Add 3 sub-scores (intent, capability, plan)
- Risk-based routing (L0-L4)

**Step C.6:** Build Advanced Planning Engine
- Multi-step task decomposition
- Plan optimization

**Step C.7:** Implement Basic Multi-Agent
- Agent orchestration
- Task delegation

**Step C.8:** Build Vision Capability
- Screenshot → LLM vision → reasoning
- Element detection

**Step C.9:** Implement Computer Use Capability
- OS-level mouse/keyboard control
- Sandboxed execution

**Step C.10:** Build Email Capability
- SMTP/IMAP interface
- Read inbox, send email

**Step C.11:** Implement WhatsApp Capability
- WhatsApp Business API or web automation
- Send/receive messages

**Step C.12:** Build ERP Integration
- Generic REST/SOAP connector
- Configurable endpoints (Odoo, SAP)

---

### Level D — Commercial Platform (90-120 days)

**Step D.1:** Implement Security Hardening
- OWASP Top 10 compliance
- Authentication, Authorization, Encryption

**Step D.2:** Build Docker Containerization
- Create `Dockerfile` and `docker-compose.yml`
- Support production deployment

**Step D.3:** Implement CI/CD Pipeline
- GitHub Actions workflows
- Automated testing and deployment

**Step D.4:** Build Monitoring System
- Prometheus + Grafana
- System metrics and alerts

**Step D.5:** Implement Analytics
- PostHog or Plausible
- User behavior tracking

**Step D.6:** Build Marketplace
- Plugin store
- Plugin discovery and installation

**Step D.7:** Implement Enterprise Features
- SSO, RBAC, Audit logs
- Team collaboration

**Step D.8:** Build Performance Optimization
- Redis caching
- Lazy loading, CDN

**Step D.9:** Implement Scaling
- Load balancing
- Horizontal scaling

**Step D.10:** Build Cloud Sync
- Synchronize data across devices
- Cloud storage integration

**Step D.11:** Implement Mobile App
- React Native or Expo
- iOS and Android support

**Step D.12:** Polish Desktop App
- Electron enhancements
- Native features

**Step D.13:** Build PWA
- Offline mode
- Installable web app

**Step D.14:** Implement Notifications
- Push notifications
- Email notifications

**Step D.15:** Build Charts & Visualizations
- Data visualization
- Interactive charts

**Step D.16:** Implement Collaboration
- Multi-user support
- Real-time collaboration

**Step D.17:** Build Billing & Licensing
- Subscription management
- License enforcement

**Step D.18:** Implement API Platform
- Public API
- API documentation

**Step D.19:** Build SDK
- Python SDK
- JavaScript SDK

**Step D.20:** Implement Developer Platform
- Plugin development tools
- Documentation and examples

**Step D.21:** Build Community Extensions
- Community plugin marketplace
- Contribution guidelines

**Step D.22:** Implement Full Accessibility (WCAG 2.1 AA)
- Complete accessibility compliance
- Automated testing

**Step D.23:** Build Full Internationalization
- Multiple language support
- RTL languages

---

## 🧪 Testing Strategy

### Testing Pipeline

Every phase MUST follow this pipeline:

**Implementation → Unit Tests → Integration Tests → Browser Acceptance → Regression Suite → Confidence Sign-off**

| Stage | Tools | Criteria |
|-------|-------|----------|
| Unit Tests | pytest, asyncio | ≥ 90% coverage for new code, all pass |
| Integration Tests | pytest, httpx ASGITransport | Module boundaries, event flow, state transitions |
| Browser Acceptance | Playwright, `npm run build` | Frontend builds, zero console errors, zero 404s |
| Regression Suite | pytest + live benchmarks | 94+ tests pass, 5 frozen benchmarks pass |
| Confidence Sign-off | Manual review | ≥ 95% confidence, no known blockers |

### Test Categories

1. **Unit Tests:** Test individual components in isolation
2. **Integration Tests:** Test module boundaries and interactions
3. **E2E Tests:** Test complete user workflows
4. **Live Benchmarks:** Test with real LLM and real tools
5. **Performance Tests:** Test system under load
6. **Security Tests:** Test for vulnerabilities
7. **Accessibility Tests:** Test for WCAG compliance

### Test Execution Rules

- All tests must pass before moving to the next step
- No test can be disabled or skipped without explicit approval
- New capabilities must include tests before merging
- Regression tests are permanent and cannot be modified

---

## 🛡️ Regression Strategy

### Frozen Benchmarks (5 Canonical)

These are permanent quality gates. Every phase must run all 5 before sign-off.

1. **Recovery Loop** — Agent recovers from file-not-found, writes + reads recovery file.
2. **Software Engineer** — Agent writes tests, fixes integer division bug, verifies 4/4 pass.
3. **Browser Live (Wikipedia)** — Navigate → type → click (timeout, recovered) → extract → screenshot → save.
4. **Autonomous Research (Fixtures)** — 2 fixture pages, 4 data fields per page, structured research.md.
5. **Replay API Integration** — 6 integration tests: empty, 404, CRUD lifecycle, multi-task, events, replay.

### Regression Freeze Protocol

- Frozen benchmarks are permanent. Any phase that breaks them is halted immediately.
- New capabilities must include a Canonical Benchmark before merging.
- Emergency override only with `manager-approve` in commit + 2 reviewer sign-offs.
- Test count is secondary — capability certification is primary.

### Regression Check Procedure

After every implementation:

```bash
cd backend && python -m pytest tests/ -v
# Expected: 94+ tests pass, 0 failures

python tests/live/test_recovery_loop.py
python tests/live/test_software_engineer_benchmark.py
python tests/live/test_browser_live_benchmark.py
python tests/live/test_autonomous_research_benchmark.py
python tests/integration/test_replay_api.py

cd frontend && npm run build
# Expected: ✓ Compiled successfully, zero errors
```

---

## 📚 Documentation Rules

### Documentation Updates

After every phase, update:

- `PROJECT_STATE.md` — current phase, test count, certified capabilities
- `CERTIFICATION_DASHBOARD.md` — new certifications, maturity levels
- `ARCHITECTURE.md` — new ADRs if architectural decisions changed
- `REGRESSION_FREEZE.md` — if new benchmarks are frozen
- `CHANGELOG.md` — what changed and why

### Documentation Standards

- All public APIs must have documentation
- All interfaces must have contract documentation
- All capabilities must have certification documentation
- All architectural decisions must have ADRs
- Documentation must be in English (with Arabic comments where appropriate)

### Documentation Tools

- API Documentation: Swagger UI or Redoc
- User Documentation: Docusaurus or GitBook
- Architecture Documentation: Markdown with Mermaid diagrams
- Changelog: Keep a Changelog format

---

## 🔀 Git Rules

### Branching Strategy

- `main` — Production-ready code
- `develop` — Integration branch for features
- `feature/*` — Feature branches
- `fix/*` — Bug fix branches
- `exp/*` — Experimental branches (for self-development)

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request Rules

- All PRs must include tests
- All PRs must pass CI/CD
- All PRs must be reviewed by at least 1 person
- Merge to `main` requires `manager-approve` tag

### Version Control Rules

- Never force push to `main` or `develop`
- Never commit directly to `main`
- Always create a branch for changes
- Always delete branch after merge

---

## ✅ Approval Workflow

### Approval Levels

| Level | Description | Required For |
|-------|-------------|--------------|
| L0 | Auto-approve | Read-only operations |
| L1 | Log only | Informative operations |
| L2 | Log + Notify | Safe mutations |
| L3 | Ask | Risky mutations |
| L4 | Block | Destructive operations |

### Approval Process

1. Coding Agent completes a task
2. Coding Agent writes implementation report
3. Coding Agent requests approval
4. Manager reviews report and verifies GitHub links
5. Manager tests the feature manually
6. Manager approves or requests changes
7. If approved, Coding Agent proceeds to next task
8. If rejected, Coding Agent fixes and resubmits

### Approval Criteria

- All tests pass
- No regression
- Browser verification successful
- Documentation updated
- GitHub links provided
- Confidence ≥ 95%

---

## 🎯 Definition of Done

### Task-Level DoD

- [ ] Code is written and committed to GitHub
- [ ] Tests pass (Unit + Integration + E2E)
- [ ] Manual browser test succeeds
- [ ] Documentation is updated
- [ ] Regression freeze is preserved
- [ ] Manager approval obtained

### Level-Level DoD

- [ ] All tasks in the level are complete
- [ ] All tests pass (94+ existing + new)
- [ ] All frozen benchmarks pass
- [ ] Frontend build succeeds
- [ ] Browser verification successful
- [ ] Documentation is updated
- [ ] Confidence Score ≥ 95%
- [ ] Manager approval obtained

### Project-Level DoD

- [ ] All 4 Evolution Levels are complete
- [ ] All capabilities are certified
- [ ] System is production-ready
- [ ] Self-development is possible
- [ ] Manager final approval obtained

---

##  Project Completion Criteria

The project is complete when:

1. **All 4 Evolution Levels are complete** (A, B, C, D)
2. **All capabilities are certified** (21/21)
3. **System is production-ready** (security, performance, deployment)
4. **Self-development is possible** (MOZA can suggest improvements, write code, test, and propose changes)
5. **Manager gives final approval**

---

##  Future Expansion Strategy

### Expansion Principles

1. **Everything is a plugin.** New capabilities enter through the plugin system.
2. **Everything is a capability.** New features are certified capabilities.
3. **Everything is extensible.** No hardcoded implementations.
4. **Everything is testable.** New capabilities must include tests.
5. **Everything is documented.** New capabilities must include documentation.

### Expansion Process

1. Identify the need (user request, market demand, self-development suggestion)
2. Design the capability (interface, contract, certification criteria)
3. Implement the capability (as a plugin)
4. Test the capability (unit, integration, E2E, live benchmark)
5. Certify the capability (run certification script, update dashboard)
6. Document the capability (contract, usage examples)
7. Deploy the capability (merge to main, update marketplace)

### Expansion Areas

1. **New AI Models** — Support for emerging models
2. **New Integrations** — CRM, ERP, communication tools
3. **New Platforms** — Mobile, desktop, web, PWA
4. **New Capabilities** — Vision, voice, video, AR/VR
5. **New Markets** — Enterprise, education, healthcare, finance

---

## 🤖 Self Development Roadmap

### Phase 1: Interfaces (Level A)

In Level A, we build empty interfaces for:
- `EvolutionInterface`
- `SelfModificationInterface`
- `TechnologyDiscoveryInterface`

These interfaces allow MOZA to later:
- Suggest improvements
- Search for new technologies
- Write new plugins

### Phase 2: Basic Evolution (Level C)

In Level C, we build:
- `EvolutionEngine` — monitors telemetry
- `ProposalManager` — manages proposals
- `ExperimentalRunner` — tests in sandbox
- `CandidateGate` — requires human approval

### Phase 3: Full Self-Development (Level D)

In Level D, MOZA can:
- Discover new technologies
- Analyze open source projects
- Suggest improvements
- Write development plans
- Execute them in Sandbox
- Test them
- Compare performance
- Suggest merging them

**But:** Every development passes through:
```
Idea → Design → Review → Implementation → Certification → Regression → Approval → Merge
```

MOZA does not modify itself directly. It becomes an engineer that proposes, writes, tests, and proves the change is safe, then waits for approval.

---

## 🔌 Plugin Strategy

### Plugin Architecture

Every capability is a plugin. The system consists of:

1. **PluginManager** — Manages plugin lifecycle (load, unload, activate, deactivate)
2. **PluginRegistry** — Registers available plugins
3. **PluginInterface** — Contract that all plugins must implement
4. **PluginStore** — Marketplace for discovering and installing plugins

### Plugin Types

1. **Capability Plugins** — Add new capabilities (Browser, Filesystem, Terminal, etc.)
2. **Provider Plugins** — Add new LLM providers (GPT, Claude, Gemini, Local, etc.)
3. **Tool Plugins** — Add new tools (Email, WhatsApp, ERP, etc.)
4. **UI Plugins** — Add new UI components (Charts, Maps, etc.)
5. **Integration Plugins** — Add new integrations (CRM, ERP, etc.)

### Plugin Lifecycle

1. **Discovery** — Plugin is discovered (marketplace, local, self-development)
2. **Installation** — Plugin is installed (dependencies, configuration)
3. **Activation** — Plugin is activated (loaded into memory)
4. **Execution** — Plugin is executed (when needed)
5. **Deactivation** — Plugin is deactivated (unloaded from memory)
6. **Uninstallation** — Plugin is uninstalled (removed from system)

### Plugin Security

- All plugins must be signed
- All plugins must pass security checks
- All plugins must be sandboxed
- All plugins must request permissions
- All plugins must be auditable

---

## 🎯 Capability Strategy

### Capability Definition

A capability is a real-world skill MOZA can perform, certified by a Canonical Benchmark.

### Capability Components

1. **Capability Interface** — Contract that defines the capability
2. **Capability Implementation** — Code that implements the capability
3. **Capability Contract** — Documentation of what the capability does
4. **Capability Certification** — Test that proves the capability works
5. **Capability Benchmark** — Frozen test that ensures the capability continues to work

### Capability Maturity Levels

| Level | Name | Description |
|-------|------|-------------|
| 0 | Not Implemented | Capability does not exist |
| 1 | Basic Functionality | Works in simplest cases |
| 2 | Error Handling | Handles failures gracefully |
| 3 | Realistic Scenarios | Works independently in real-world cases |
| 4 | Production Ready | Reliable, documented, tested |
| 5 | Trusted Autonomy | Can execute without direct supervision |

### Capability Certification Process

1. Define the capability (interface, contract)
2. Implement the capability (code)
3. Write certification script (test)
4. Run certification (prove it works)
5. Capture evidence (screenshots, logs)
6. Update dashboard (show maturity level)
7. Freeze benchmark (ensure it continues to work)

---

## 🧠 Memory Strategy

### Memory Architecture

MOZA has a 5-layer memory system:

1. **Identity Memory** — Who am I? (Constitution, Golden Rules)
2. **User Memory** — Who is the user? (Preferences, habits)
3. **Experience Memory** — What have I learned? (Patterns, rules)
4. **Conversation Memory** — What are we discussing? (Chat history)
5. **Task Memory** — What am I doing right now? (Current task state)

### Memory Storage

- **Identity Memory:** `constitution.yaml` (immutable)
- **User Memory:** SQLite (`memory/user.db`)
- **Experience Memory:** SQLite + JSON (`memory/experience.db`)
- **Conversation Memory:** SQLite (`memory/conversation.db`)
- **Task Memory:** In-memory + 24h archive

### Memory Retrieval

- **Identity Memory:** Loaded at startup, available to all components
- **User Memory:** Retrieved per user, injected into prompts
- **Experience Memory:** Retrieved by similarity, used for learning
- **Conversation Memory:** Retrieved by session, used for context
- **Task Memory:** Retrieved by task, used for execution

### Memory Lifecycle

| Layer | Write Trigger | Read Trigger | Retention | Archive |
|-------|---------------|--------------|-----------|---------|
| Identity | Startup | Every prompt | Permanent | Never |
| User | End of session | Every prompt | Permanent | Never |
| Experience | Macro Reflection | Planning phase | 90 days | After decay |
| Conversation | Every turn | Next turn | 20 turns | After session |
| Task | Every step | Current task | Task duration | 24 hours |

---

## 🧠 Executive Mind Strategy

### Executive Mind Architecture

The Executive Mind is the decision engine of MOZA. It consists of:

1. **Intent Classifier** — Understands what the user wants
2. **Planner** — Breaks down complex tasks into steps
3. **Confidence Engine** — Scores decisions (0.0-1.0)
4. **Approval Router** — Routes decisions based on risk (L0-L4)
5. **Prompt Composer** — Assembles the final prompt
6. **Recovery Engine** — Handles failures and retries
7. **Reflection Engine** — Learns from execution

### Executive Mind Flow

```
User Input
    ↓
Intent Classifier
    ↓
Guard Engine (Golden Rules)
    ↓
Planner (if TASK)
    ↓
Confidence Engine
    ↓
Approval Router
    ↓
Prompt Composer
    ↓
LLM (Reasoning Engine)
    ↓
Tool Execution
    ↓
Recovery Engine (if failed)
    ↓
Reflection Engine (after completion)
```

### Executive Mind Principles

1. **Deterministic first.** Use rules and heuristics before LLM.
2. **Confidence-based.** Score every decision.
3. **Risk-aware.** Route based on operation risk.
4. **Recoverable.** Handle failures gracefully.
5. **Reflective.** Learn from every execution.

---

## 🔄 Reflection Strategy

### Reflection Architecture

MOZA has two types of reflection:

1. **Micro Reflection** — After every tool execution step
2. **Macro Reflection** — After task completion

### Micro Reflection

**Trigger:** After every `TOOL_RESULT` event

**Purpose:** Analyze step result and decide next action

**Actions:**
- Retry (if recoverable error)
- Fallback (switch to alternative tool)
- Continue (if success)
- Escalate (if unrecoverable)

**Output:** `MICRO_REFLECTION` event

### Macro Reflection

**Trigger:** After `TASK_COMPLETED` or `TASK_FAILED`

**Purpose:** Extract lessons from the entire task

**Actions:**
- Analyze full event stream
- Extract what worked, what failed, what was slow
- Generate `ExperienceRecord`
- Update capability confidence scores
- Consolidate similar experiences into rules

**Output:** `MACRO_REFLECTION` event + `reflection_report.json`

### Reflection Integration

- Micro reflection is called by the Orchestrator after every `TOOL_RESULT`
- Macro reflection is called by the Orchestrator after task end
- Both feed their insights into the Memory Mesh

---

## 📚 Learning Strategy

### Learning Architecture

MOZA learns through a pipeline:

```
Execution → Reflection → Experience → Knowledge → Adaptive Behaviour
```

### Learning Components

1. **Experience Consolidation** — Groups similar experiences into rules
2. **Knowledge Graph** — Stores entities and relationships
3. **Adaptive Profile** — Tracks user preferences

### Experience Consolidation

**Trigger:** After Macro Reflection or periodically

**Process:**
1. Group similar experiences by tool, error pattern, task type
2. If 3+ similar experiences → generate `LearnedRule`
3. Store rules in Identity layer (as "soft rules")
4. Decay old experiences after 30 days unless reinforced

### Knowledge Graph

**Storage:** SQLite + JSON

**Schema:**
- `entities` (id, type, name, embedding)
- `relations` (source, target, type, weight)

**Entity Types:** Tool, File, URL, Error, Concept, UserPreference

**Relation Types:** uses, produces, fixes, causes, depends_on

**Population:** Automatically from task events, reflection reports, user feedback

**Query Interface:** `find_related(entity, relation_type, depth)`

### Adaptive Profile

**Storage:** Per-user profile (separate from immutable Identity)

**Tracks:** Preferred language, common task types, frequently used tools, typical workspace paths, preferred response style

**Updates:** After every task via Macro Reflection

**Usage:** Loaded by PromptComposer to personalize prompts

---

##  Security Strategy

### Security Layers

1. **Authentication** — Who is the user?
2. **Authorization** — What can the user do?
3. **Encryption** — Protect data at rest and in transit
4. **Audit** — Track all actions
5. **Compliance** — GDPR, OWASP, etc.

### Security Implementation

- **Authentication:** JWT tokens, OAuth 2.0, SSO
- **Authorization:** RBAC (Role-Based Access Control)
- **Encryption:** AES-256 for data at rest, TLS 1.3 for data in transit
- **Audit:** Immutable logs, tamper-proof
- **Compliance:** GDPR (data deletion), OWASP Top 10

### Security Testing

- Penetration testing
- Vulnerability scanning
- Dependency auditing
- Code review
- Security benchmarks

---

##  Performance Strategy

### Performance Goals

- **Response Time:** < 2 seconds for simple tasks
- **Throughput:** 100 concurrent users
- **Availability:** 99.9% uptime
- **Scalability:** Horizontal scaling

### Performance Optimization

1. **Caching** — Redis for frequent queries
2. **Lazy Loading** — Load components on demand
3. **CDN** — Serve static assets from CDN
4. **Database Optimization** — Indexes, query optimization
5. **Connection Pooling** — Reuse database connections
6. **Async Processing** — Non-blocking I/O
7. **Load Balancing** — Distribute traffic across instances

### Performance Monitoring

- **Metrics:** Latency, throughput, error rates
- **Tools:** Prometheus, Grafana
- **Alerts:** Threshold-based alerts
- **Dashboards:** Real-time performance dashboards

### Performance Testing

- Load testing (k6, Artillery)
- Stress testing
- Endurance testing
- Spike testing

---

## 🚀 Deployment Strategy

### Deployment Environments

1. **Development** — Local development
2. **Staging** — Pre-production testing
3. **Production** — Live environment

### Deployment Methods

1. **Docker** — Containerized deployment
2. **Kubernetes** — Orchestrated deployment
3. **Cloud** — AWS, GCP, Azure
4. **On-Premise** — Self-hosted

### Deployment Pipeline

```
Code → Build → Test → Stage → Deploy → Monitor
```

### Deployment Tools

- **CI/CD:** GitHub Actions, GitLab CI, Jenkins
- **Containerization:** Docker, Docker Compose
- **Orchestration:** Kubernetes, Docker Swarm
- **Cloud:** AWS ECS, GCP GKE, Azure AKS
- **Monitoring:** Prometheus, Grafana, ELK

### Deployment Strategy

- **Blue-Green Deployment** — Zero downtime
- **Canary Deployment** — Gradual rollout
- **Rolling Deployment** — Incremental updates
- **Feature Flags** — Safe feature rollout

---

##  Product Strategy

### Product Vision

MOZA is an AI Operating System that works alongside you every day, knows your world as well as you do, and can eventually participate in its own development under human supervision.

### Product Goals

1. **Usability** — Easy to use, intuitive interface
2. **Reliability** — Works consistently, no crashes
3. **Intelligence** — Learns and adapts to the user
4. **Extensibility** — Can be extended with plugins
5. **Security** — Protects user data
6. **Performance** — Fast and responsive

### Product Metrics

- **User Engagement:** Daily active users, session duration
- **User Satisfaction:** NPS, CSAT
- **Task Completion:** Success rate, time to complete
- **Capability Usage:** Which capabilities are used most
- **Error Rate:** Frequency of errors, recovery rate

### Product Roadmap

- **Level A:** Core Foundation (30-45 days)
- **Level B:** Core Product (45-60 days)
- **Level C:** Intelligence Expansion (60-90 days)
- **Level D:** Commercial Platform (90-120 days)

---

##  Commercial Readiness Strategy

### Commercial Requirements

1. **Security** — OWASP Top 10, GDPR compliance
2. **Performance** — 99.9% uptime, < 2s response time
3. **Scalability** — Support 100+ concurrent users
4. **Support** — Documentation, help desk, community
5. **Billing** — Subscription management, licensing
6. **Legal** — Terms of service, privacy policy

### Commercial Models

1. **SaaS** — Cloud-hosted, subscription-based
2. **On-Premise** — Self-hosted, license-based
3. **Hybrid** — Cloud + on-premise options

### Commercial Pricing

- **Free Tier** — Basic features, limited usage
- **Pro Tier** — Advanced features, higher limits
- **Enterprise Tier** — Full features, unlimited usage, support

### Commercial Launch

1. **Beta** — Limited users, feedback collection
2. **Soft Launch** — Public but limited marketing
3. **Full Launch** — Public with full marketing

---

## 🌐 Open Source Strategy

### Open Source Model

MOZA will be open source with a commercial offering.

### Open Source License

- **Core:** MIT License (permissive)
- **Enterprise Features:** Commercial License

### Open Source Community

- **Contributors:** Welcome external contributions
- **Maintainers:** Core team reviews and merges
- **Users:** Community support and feedback

### Open Source Governance

- **Code of Conduct:** Professional and respectful
- **Contribution Guidelines:** Clear process for contributions
- **Issue Tracking:** Public issue tracker
- **Roadmap:** Public roadmap

### Open Source Benefits

- **Transparency** — Users can see and verify the code
- **Community** — External contributors and users
- **Innovation** — Faster development through collaboration
- **Trust** — Users can audit the code

---

## 🛠️ Maintenance Strategy

### Maintenance Types

1. **Corrective** — Fix bugs and errors
2. **Adaptive** — Adapt to new environments
3. **Perfective** — Improve performance and usability
4. **Preventive** — Prevent future problems

### Maintenance Process

1. **Issue Reporting** — Users report issues
2. **Issue Triage** — Prioritize issues
3. **Issue Resolution** — Fix issues
4. **Issue Verification** — Verify fixes
5. **Issue Closure** — Close issues

### Maintenance Tools

- **Issue Tracking:** GitHub Issues, Jira
- **Monitoring:** Prometheus, Grafana, Sentry
- **Logging:** ELK Stack, Loki
- **Alerting:** PagerDuty, OpsGenie

### Maintenance Schedule

- **Daily:** Monitor system health
- **Weekly:** Review issues and metrics
- **Monthly:** Performance optimization
- **Quarterly:** Security audit
- **Yearly:** Architecture review

---

## 📎 Appendices

### Appendix A: File Structure After All Phases

```
Moza/
 ├── constitution.yaml              # Level A — Immutable identity
 ├── config.yaml                    # Existing — Runtime config
 ├── backend/
 │   └── moza/
 │       ├── main.py
 │       ├── config/
 │       ├── core/
 │       │   ├── models.py
 │       │   ├── context.py
 │       │   ├── context_builder.py
 │       │   ├── event_bus.py
 │       │   ├── event_recorder.py
 │       │   ├── session_manager.py
 │       │   ├── cancellation.py
 │       │   ├── resource_manager.py
 │       │   ├── state_machine.py       # Level A
 │       │   ├── guards.py              # Level A
 │       │   ├── identity.py            # Level A
 │       │   ├── planner.py             # Level C
 │       │   ├── confidence_engine.py   # Level C
 │       │   ├── prompt_composer.py     # Level C
 │       │   ── approval_router.py     # Level C
 │       ├── plugins/                   # Level A
 │       │   ├── plugin_manager.py
 │       │   ├── interfaces.py
 │       │   └── registry.py
 │       ├── agents/
 │       │   ├── interfaces.py
 │       │   ├── litellm_tool_agent.py
 │       │   ├── mock_agent.py
 │       │   └── openhands_adapter.py
 │       ├── gateway/
 │       │   ├── interfaces.py
 │       │   ├── litellm_adapter.py
 │       │   ├── gateway_manager.py     # Level A
 │       │   ├── provider_registry.py   # Level A
 │       │   ├── fallback_chain.py      # Level A
 │       │   └── health_check.py        # Level A
 │       ├── tools/
 │       │   ├── registry.py
 │       │   ├── browser_tool.py
 │       │   ├── browser_engine.py
 │       │   ├── playwright_engine.py
 │       │   ├── filesystem_tool.py
 │       │   ├── terminal_tool.py
 │       │   ├── vision_tool.py         # Level C
 │       │   ├── computer_use_tool.py   # Level C
 │       │   ├── email_tool.py          # Level C
 │       │   ├── whatsapp_tool.py       # Level C
 │       │   └── erp_tool.py            # Level C
 │       ├── memory/                    # Level C
 │       │   ├── memory_mesh.py
 │       │   ├── layers/
 │       │   │   ├── identity_layer.py
 │       │   │   ├── user_layer.py
 │       │   │   ├── experience_layer.py
 │       │   │   ├── conversation_layer.py
 │       │   │   └── task_layer.py
 │       │   └── backends/
 │       │       ├── sqlite_backend.py
 │       │       ├── jsonl_backend.py
 │       │       ── embedding_backend.py
 │       ├── reflection/                # Level C
 │       │   ├── micro_reflection.py
 │       │   ├── macro_reflection.py
 │       │   └── models.py
 │       ├── learning/                  # Level C
 │       │   ├── consolidation.py
 │       │   ├── knowledge_graph.py
 │       │   ├── adaptive_profile.py
 │       │   └── models.py
 │       ├── evolution/                 # Level C/D
 │       │   ├── engine.py
 │       │   ├── proposal_manager.py
 │       │   ├── experimental_runner.py
 │       │   ├── candidate_gate.py
 │       │   ├── models.py
 │       │   └── analyzers/
 │       │       ├── telemetry_analyzer.py
 │       │       ├── code_analyzer.py
 │       │       └── benchmark_analyzer.py
 │       ├── certification/
 │       │   ├── capability_base.py
 │       │   ├── certification_runner.py    # Level A
 │       │   ├── certification_dashboard.py # Level A
 │       │   └── capabilities/
 │       │       ├── conversation_contract.md
 │       │       ├── conversation.py
 │       │       ├── filesystem_contract.md       # Level A
 │       │       ├── terminal_contract.md         # Level A
 │       │       ├── browser_contract.md          # Level A
 │       │       ├── research_contract.md         # Level A
 │       │       ├── recovery_contract.md         # Level A
 │       │       ├── replay_contract.md           # Level A
 │       │       ├── sse_streaming_contract.md    # Level A
 │       │       ├── react_reasoning_contract.md  # Level A
 │       │       ├── executive_mind_contract.md   # Level A
 │       │       ├── vision_contract.md           # Level C
 │       │       ├── computer_use_contract.md     # Level C
 │       │       ├── email_contract.md            # Level C
 │       │       ├── whatsapp_contract.md         # Level C
 │       │       └── erp_contract.md              # Level C
 │       ├── security/                  # Level D
 │       │   ├── auth.py
 │       │   ├── encryption.py
 │       │   └── rbac.py
 │       ├── monitoring/                # Level D
 │       │   ├── prometheus.py
 │       │   └── grafana_dashboards/
 │       ├── analytics/                 # Level D
 │       │   └── posthog.py
 │       ├── marketplace/               # Level D
 │       │   ├── store.py
 │       │   └── plugin_registry.py
 │       ├── enterprise/                # Level D
 │       │   ├── sso.py
 │       │   └── audit.py
 │       ├── performance/               # Level D
 │       │   ├── redis_cache.py
 │       │   ── cdn.py
 │       ├── api/
 │       │   └── routes/
 │       │       ├── chat.py
 │       │       ├── replay.py
 │       │       ├── upload.py          # Level B
 │       │       ├── history.py         # Level B
 │       │       ├── export.py          # Level B
 │       │       ├── search.py          # Level B
 │       │       └── settings.py        # Level B
 │       └── orchestrator/
 │           ├── orchestrator.py
 │           └── service.py
 ├── frontend/                      # Level B
 ├── desktop/                       # Level D
 ├── benchmarks/                    # YAML specs for all capabilities
 ├── docs/
 │   └── ADRs/
 ├── tests/
 │   ├── unit/
 │   ├── integration/
 │   ├── e2e/
 │   └── live/
 └── sessions/                      # Runtime data (JSONL + SQLite)
```

### Appendix B: Confidence Score Formula

```python
composite_confidence = (
    intent_confidence * 0.35 +
    capability_confidence * 0.30 +
    plan_confidence * 0.35
)

# Risk-based routing
if risk_class == "L4":
    decision = "BLOCK"  # Always ask, regardless of confidence
elif composite_confidence >= 0.70:
    decision = "AUTO"
elif composite_confidence >= 0.50:
    decision = "LOG"
elif composite_confidence >= 0.30:
    decision = "ASK"
else:
    decision = "CLARIFY"  # Ask user to rephrase
```

### Appendix C: Risk-Based Approval Matrix

| Risk Class | Examples | Confidence Threshold | Action |
|------------|----------|---------------------|--------|
| L0 — Read-Only | Read file, list dir, browse page, extract text | ≥ 0.10 | Auto — Execute immediately |
| L1 — Informative | Run `git status`, `pytest --collect-only`, screenshot | ≥ 0.30 | Auto — Log only |
| L2 — Mutating (Safe) | Write new file, create directory, non-destructive terminal | ≥ 0.50 | Log + Notify — Execute but record |
| L3 — Mutating (Risky) | Overwrite existing file, `pip install`, browser form submit | ≥ 0.70 | Ask — Pause for human approval |
| L4 — Destructive | Delete file/directory, `rm -rf`, format disk, send email/WhatsApp | ≥ 0.95 | Block — Always require approval regardless of confidence |

**Rule:** Risk Class is determined by the tool's `is_destructive` and `requires_confirmation` flags, NOT by the LLM's confidence.

### Appendix D: State Machine (8 States)

```
Idle → Planning → Executing → WaitingApproval → Reflecting → Recovering → Completed
                                                              ↓
                                                            Failed
```

| State | Meaning | Entry Trigger |
|-------|---------|---------------|
| Idle | System ready, no active task | Startup / task completion |
| Planning | Analyzing intent, building plan, scoring confidence | Task received |
| Executing | Running tools, streaming events | Plan approved (auto or human) |
| WaitingApproval | Paused for human decision on L3/L4 operation | Tool with `requires_confirmation=True` |
| Reflecting | Micro-reflection after each step; Macro after task | Step complete / task complete |
| Recovering | Handling tool failure, retrying, or switching strategy | `success=False` in ToolResult |
| Completed | Task done, artifacts saved, memory updated | Final event emitted |
| Failed | Unrecoverable error or max steps reached | Fatal error or exhaustion |

### Appendix E: Glossary

- **Capability:** A real-world skill MOZA can perform, certified by a Canonical Benchmark.
- **Canonical Benchmark:** A frozen, versioned, YAML-driven E2E test that proves a capability.
- **Confidence Score:** 0.0–1.0 measure of system certainty in a decision.
- **Risk Class:** L0–L4 classification of operation danger (read-only to destructive).
- **Regression Freeze:** Permanent lock on proven benchmarks; no future change may break them.
- **Controlled Evolution:** Pipeline for self-improvement (Experimental → Candidate → Stable).
- **Memory Mesh:** Unified interface to 5 memory layers.
- **Reflection:** Micro (per-step) and Macro (per-task) analysis of execution quality.
- **Plugin:** A modular component that adds a capability to the system.
- **Evolution Level:** A stable platform that enables the next level of functionality.

---

##  Final Notes

This document is the **single source of truth** for MOZA's construction roadmap.

After this document, no architectural redesigns. Future additions (new tools, new providers, new UIs) enter as new Capabilities within this framework.

The Coding Agent must read this file before every implementation cycle and never improvise outside this document.

MOZA is built to last.

**This plan is FINAL.**