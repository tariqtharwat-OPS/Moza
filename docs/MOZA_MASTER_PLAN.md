# MOZA MASTER PLAN
## AI Operating System — Architecture Constitution & Governance Document

**Version:** 1.0-RATIFIED  
**Date:** 2026-07-28  
**Status:** RATIFIED — Single Source of Truth (SSOT)  
**Classification:** Single Source of Truth (SSOT) — Governance Layer  
**Companion Document:** MOZA_EXECUTION_PLAN.md v4.0 (Implementation Roadmap)

---

## Document Charter

This document is the **architectural constitution** of MOZA. It governs **why** the system exists, **what** it must become, and **what rules** constrain its evolution. It does not govern implementation schedules, coding tasks, or day-to-day execution — those remain the domain of the Execution Plan v4.0.

**Relationship to Execution Plan:**
- **Master Plan (this document):** Vision, principles, governance, quality gates, deferred decisions, migration strategy.
- **Execution Plan v4.0:** Implementation steps, file-level changes, testing procedures, coding agent instructions.

Any conflict between this document and the Execution Plan must be resolved in favor of this document for architectural matters, and in favor of the Execution Plan for implementation matters. If a conflict cannot be resolved, an ADR (Architecture Decision Record) must be raised.

---

## 0. Executive Summary

MOZA is an AI Operating System evolving from a component-based assistant into a **capability-first cognitive platform**. It receives complex human objectives, creates plans, executes multi-step tasks, collects evidence, evaluates confidence, and generates professional outputs — all while preserving every previously working capability.

**Current State (per Execution Plan v4.0, repository verification pending):**
- 11 of 21 planned capabilities are certified as Production Ready (Maturity Level 4)
- 94+ automated tests exist with 5 frozen regression benchmarks
- Core infrastructure operational: LLM Gateway, Agent Loop, Intent Classifier, Orchestrator, Event Bus, Tool Registry, Browser Engine, Filesystem, Terminal, Session Manager
- Desktop application exists as skeleton only

**Target State:**
- 21 certified capabilities across 4 Evolution Levels (A: Core Foundation, B: Core Product, C: Intelligence Expansion, D: Commercial Platform)
- ResearchCase as a first-class domain entity managing long-running investigations
- 5-layer Memory Mesh with Reflection and Learning pipelines
- Self-development readiness within 24 months of human-supervised operation

**Immutable Constraints:**
> **Evolution must be additive, not destructive.** MOZA grows by accumulation. No capability may be removed without an approved ADR, a migration plan, and explicit sign-off.
>
> **Human-in-the-Loop for high-impact actions.** MOZA maximizes autonomous execution for planning, research, analysis, and drafting. Strict approval gates protect high-impact actions: sending communications, deleting data, publishing content, or modifying core systems.

---

## 1. Vision & Non-Goals

### 1.1 Vision

MOZA is an AI Operating System — a cognitive platform that understands human intent, plans, executes, learns, and evolves. It is not a tool you use; it is a digital colleague that works alongside you, knows your world, and eventually participates in its own development under human supervision.

**Ultimate Goal:** A system capable of receiving an objective such as *"Analyze the seafood export market in Southeast Asia and prepare an investor-grade report"* and autonomously:
1. Creating a ResearchCase with a multi-step plan
2. Researching companies and collecting sources
3. Validating information and organizing evidence
4. Evaluating confidence at each step
5. Producing PDF/Excel/Presentation outputs
6. Resuming interrupted work without data loss
7. Requesting human approval only for risky or destructive actions

**Self-Development Readiness:** If active human development stops after two years, MOZA must be capable of:
- Suggesting improvements based on telemetry
- Discovering new technologies and comparing itself to competitors
- Identifying gaps in its own capability matrix
- Proposing new plugins and writing code
- Updating documentation
- Executing changes in a sandboxed, supervised manner

### 1.2 Non-Goals

MOZA is explicitly NOT:
- **An LLM wrapper.** Intelligence lives in architecture, not the model. The LLM is a replaceable CPU.
- **A chatbot.** Conversational ability is one capability among many, not the product definition.
- **A greenfield rewrite.** The current repository IS the production baseline. Evolution only; no "version 2.0" rebuilds.
- **A black-box oracle.** Every conclusion must be traceable to collected evidence.
- **An autonomous agent without oversight.** Risky and destructive actions require human approval.
- **A static application.** It is a living system that must evolve safely.

---

## 2. Architectural Principles

These principles are immutable. They may be amended only by ADR with manager approval.

### 2.1 Core Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| 1 | **Core stability over feature speed.** | A broken system cannot evolve. |
| 2 | **Capability-first development.** | Components are infrastructure; capabilities are the product. A component without a certified capability is technical debt. |
| 3 | **Plugins extend the system without modifying core.** | The Plugin Architecture (Interface + Registry + Contract) ensures extensibility without fragility. |
| 4 | **Every capability requires measurable acceptance tests.** | A capability is not real until it has a Capability Acceptance Test (CAT) and a frozen benchmark. |
| 5 | **Evidence before conclusions.** | MOZA must distinguish Fact, Source Claim, Assumption, and Unknown. No output without traceable evidence. |
| 6 | **Human approval for risky actions.** | Risk Class L3 (risky mutation) and L4 (destructive) always require human approval, regardless of confidence score. |
| 7 | **Zero regression policy.** | A certified capability that breaks is a project halt. |
| 8 | **Observability and logging by default.** | Every decision, tool call, and state transition generates an immutable audit event. |
| 9 | **Modular architecture.** | Every component supports Interface, Registry, Contract, Plugin, Capability, and Event patterns. |
| 10 | **Long-term maintainability over short-term hacks.** | Technical debt must be documented and scheduled for repayment; it cannot be invisible. |

### 2.2 Evolution Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| 11 | **Evolution must be additive, not destructive.** | MOZA must evolve by adding capabilities while preserving all previously working capabilities. Existing capabilities continue to work. No core functionality is removed without explicit ADR approval. Breaking changes require migration plans. Every new capability must pass regression tests against previous capabilities. The system grows cumulatively, not by replacing previous foundations. |
| 12 | **Backward compatibility is mandatory.** | Public interfaces, APIs, event schemas, and capability contracts must remain stable across versions. Deprecation requires a 2-level notice period. |
| 13 | **Build smart on existing.** | Reuse > Refactor > Rewrite (never). Every implementation must build on the existing system. No architecture resets. |
| 14 | **The LLM is a replaceable CPU.** | All intelligence lives in architecture. The LLM Gateway must support swapping providers without breaking capabilities. |
| 15 | **Self-development is prepared from day one.** | Empty interfaces for Evolution, Self-Modification, and Technology Discovery must exist in Level A, even if implementation waits until Level C/D. |

### 2.3 Governance Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| 16 | **Architecture first, implementation second.** | Define contracts and interfaces before coding. |
| 17 | **Confidence ≥ 95% to proceed.** | No level is complete until confidence score meets threshold. |
| 18 | **Constitution is immutable.** | Identity, Golden Rules, and Forbidden Behaviors are hard-coded guards, not prompts. |
| 19 | **No architectural redesigns after ratification.** | Future additions enter as new Capabilities within this framework. |
| 20 | **Every change must be incremental.** | Every level must finish with a fully working application. No "big bang" rewrites. No temporary broken states. |

---

## 3. Current Architecture

### 3.1 Production Baseline

*The following is derived from MOZA_EXECUTION_PLAN.md v4.0. Repository verification is pending.*

**Architectural History Note:**
MOZA evolved from a component-based assistant architecture into its current capability-first orientation. Earlier design decisions — including the choice of LiteLLM for provider abstraction, Playwright for browser automation, deterministic regex-based intent classification, and JSONL event persistence — are preserved in this baseline not because they are immutable, but because they represent proven, working foundations. Any future replacement of these components must follow the Evolution Governance rules (Section 18), including impact analysis, preservation matrix validation, and ADR approval. This document records the rationale for current choices; it does not erase them.

MOZA currently operates as a Python backend (FastAPI/ASGI) with a React/TypeScript frontend and an Electron desktop skeleton. It uses a ReAct agent loop with deterministic intent classification and real-time SSE streaming.

**Working Components:**

| Component | Status | Notes |
|-----------|--------|-------|
| LLM Gateway | Working | Supports Groq, OpenRouter, Anthropic, Ollama, vLLM, LM Studio via LiteLLM |
| Agent Loop | Working | ReAct while loop with max_steps, tool schema builder, error resilience |
| Intent Classifier | Working | Deterministic regex-based, Arabic/English, zero LLM cost |
| Orchestrator | Working | Task lifecycle, basic approval flow, event routing |
| Event Bus | Working | Pub/Sub + JSONL persistence to disk |
| Context Builder | Working | 7-section dynamic prompt injection |
| Tool Registry | Working | BaseTool ABC, basic capability gating, load/unload/cleanup |
| Browser Engine | Working | ABC + Playwright headless, modular components |
| Filesystem Tool | Working | Read/write/list with safety metadata |
| Terminal Tool | Working | Async subprocess with timeout, cleanup |
| Session Manager | Working | Replay API, 4 endpoints, event reading |
| Capability Base | Working | ABC with 3 methods, MaturityLevel enum, CertificationResult |
| Frontend | Working | ChatInterface, BrowserVisualizer, TerminalComponent, MainLayout |
| Desktop | Skeleton | Electron shell exists but minimal |

### 3.2 Certified Capabilities (11/21)

*Per Execution Plan v4.0. These capabilities have passed canonical benchmarks and are frozen against regression.*

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

### 3.3 Frozen Regression Benchmarks (5 Canonical)

These are permanent quality gates. Every phase must run all 5 before sign-off:

1. **Recovery Loop** — Agent recovers from file-not-found, writes + reads recovery file.
2. **Software Engineer** — Agent writes tests, fixes integer division bug, verifies 4/4 pass.
3. **Browser Live (Wikipedia)** — Navigate → type → click (timeout, recovered) → extract → screenshot → save.
4. **Autonomous Research (Fixtures)** — 2 fixture pages, 4 data fields per page, structured research.md.
5. **Replay API Integration** — 6 integration tests: empty, 404, CRUD lifecycle, multi-task, events, replay.

### 3.4 Architectural Patterns in Use

- **Interface + Registry + Contract:** ToolRegistry, ProviderRegistry
- **Event Sourcing:** EventBus + JSONL persistence
- **Deterministic Guards:** Intent Classifier (regex), Golden Rules (prompt-level)
- **ReAct Loop:** Reasoning → Action → Observation → Repeat
- **Risk-Based Approval:** L0–L4 classification with confidence thresholds

---

## 4. Target Architecture

### 4.1 Evolution Levels Overview

MOZA evolves through 4 stable platforms. Each level is additive — it preserves all previous capabilities while enabling new ones.

| Level | Name | Focus | Duration (per Execution Plan) | Key Enablers |
|-------|------|-------|------------------------------|--------------|
| A | Core Foundation (النواة) | Infrastructure, extensibility, governance | 30–45 days | Plugin Architecture, State Machine, Guards, Constitution, Registry, DI Container, Feature Flags |
| B | Core Product (المنتج) | Usability, professional UI, workspace | 45–60 days | File Upload, History, Rich Content, Task Cards, Export, Search, Settings, Auth |
| C | Intelligence Expansion (الذكاء) | Memory, reflection, learning, planning | 60–90 days | Memory Mesh, Reflection Engine, Learning Pipeline, Multi-Agent, Vision, Computer Use |
| D | Commercial Platform (المنصة التجارية) | Security, scale, marketplace, enterprise | 90–120 days | SSO, RBAC, Docker, CI/CD, Monitoring, Marketplace, Billing, Mobile, PWA |

### 4.2 Target Component Map

```
MOZA AI Operating System
├── Constitution Layer (immutable)
│   ├── constitution.yaml
│   ├── Golden Rules Guards
│   └── Identity Loader
├── Core Engine
│   ├── State Machine (8 states)
│   ├── Orchestrator + Approval Router
│   ├── Confidence Engine (3 sub-scores)
│   ├── Planner (multi-step decomposition)
│   ├── Prompt Composer
│   ├── Context Builder (Memory Mesh retrieval)
│   └── Recovery Engine
├── Gateway Layer
│   ├── Provider Registry
│   ├── Fallback Chain
│   └── Health Checks
├── Plugin Architecture
│   ├── Plugin Manager
│   ├── Capability Interface
│   ├── Tool Interface
│   ├── Provider Interface
│   └── Plugin Registry / Marketplace
├── Tool Layer
│   ├── Filesystem, Terminal, Browser (existing)
│   ├── Vision, Computer Use, Email, WhatsApp, ERP (Level C)
│   └── Future tools via Plugin System
├── Memory & Knowledge
│   ├── Memory Mesh (5 layers)
│   ├── Reflection Engine (Micro + Macro)
│   ├── Learning Pipeline (Consolidation + Knowledge Graph)
│   └── Adaptive Profile
├── Research Domain
│   ├── ResearchCase Manager
│   ├── Evidence Collection Pipeline
│   ├── Source Validation
│   └── Report Generator
├── Output & Reporting
│   ├── PDF Engine
│   ├── Excel Analysis
│   ├── Presentation Builder
│   └── Business Proposal Templates
├── Frontend
│   ├── Chat Interface + Rich Content
│   ├── Browser Workspace
│   ├── File Tree Explorer
│   ├── Task Visualization
│   ├── History Sidebar
│   └── Settings / Export / Search
└── Platform (Level D)
    ├── Security (Auth, RBAC, Encryption)
    ├── Monitoring (Prometheus + Grafana)
    ├── Analytics
    ├── Marketplace
    └── Mobile / Desktop / PWA
```

### 4.3 Browser Strategy

The Browser Engine must support three operational modes:

**1. Persistent Browser Session**
- Maintains user login/session state across tasks
- Used for trusted websites where authentication continuity is required
- Profile stored securely with user-scoped isolation

**2. User Session Mode**
- User-controlled browser profile with explicit consent
- Shared session state for workflows requiring human-in-the-loop authentication
- Clear visual indicator in UI when this mode is active

**3. Isolated Mode**
- Clean temporary browser for each task
- No cookies, no cache, no session persistence
- Default for untrusted or research-only tasks

**CAPTCHA Consideration:** CAPTCHA challenges are frequently triggered by isolated automation sessions. The Browser Strategy must include:
- CAPTCHA detection and graceful failure (never stall indefinitely)
- Fallback to user notification when human intervention is required
- Logging of CAPTCHA encounters for pattern analysis
- No attempt to bypass CAPTCHA mechanisms (legal and ethical compliance)

---

## 5. Capability Roadmap

### 5.1 Philosophy

Components are infrastructure. Capabilities are the product. Every capability must be certified before it is considered complete.

To prevent scope inflation and management overhead, capabilities are organized in a **3-tier hierarchy**:

- **Capability Domains** — High-level functional areas (e.g., Market Intelligence, Platform Operations)
- **Major Capabilities** — The ~21 certifiable skills that define MOZA's product surface. These are what users experience and what benchmarks validate.
- **Atomic Functions** — The granular technical functions (64+) that implement major capabilities. These are internal implementation details, not independently certified.

*Note: The original Execution Plan v4.0 referenced "21 capabilities" without full enumeration. The hierarchical model below reconciles that target with the full functional inventory. The exact mapping of Major Capabilities is subject to architectural validation before ratification.*

### 5.2 Capability Domains

| Domain | Description | Evolution Level |
|--------|-------------|-----------------|
| **Cognitive Engine** | Reasoning, planning, intent classification, confidence scoring | A → C |
| **Tool & Action Layer** | Filesystem, terminal, browser, vision, computer use | A → C |
| **Research & Intelligence** | Evidence collection, source validation, synthesis, reporting | A → C |
| **Memory & Learning** | 5-layer memory, reflection, knowledge graph, adaptive profile | C |
| **Communication & Integration** | Chat, email, WhatsApp, ERP connectors | A → C |
| **Product Experience** | UI/UX, upload, history, export, search, workspace | B |
| **Platform Infrastructure** | Security, deployment, monitoring, scaling, performance | A → D1 |
| **Commercial Ecosystem** | Marketplace, billing, mobile, SDK, collaboration, enterprise | D2 |

### 5.3 Major Capabilities (~21 Target)

These are the certifiable, user-visible capabilities that define MOZA's maturity. Each major capability comprises multiple atomic functions.

| # | Major Capability | Domain | Current Status | Target Level |
|---|------------------|--------|----------------|--------------|
| 1 | **Conversational Response** | Communication | Certified (4) | A |
| 2 | **Intent Classification** | Cognitive Engine | Certified (4) | A |
| 3 | **Tool Orchestration** | Tool & Action | Certified (4) | A |
| 4 | **Filesystem Operations** | Tool & Action | Certified (4) | A |
| 5 | **Terminal Execution** | Tool & Action | Certified (4) | A |
| 6 | **Browser Automation** | Tool & Action | Certified (4) | A |
| 7 | **Recovery & Resilience** | Cognitive Engine | Certified (4) | A |
| 8 | **Plugin Architecture** | Platform Infrastructure | Not Implemented | A |
| 9 | **State Machine Management** | Cognitive Engine | Partial (6 states) | A |
| 10 | **Event Sourcing & Replay** | Platform Infrastructure | Partial | A |
| 11 | **Research & Evidence** | Research & Intelligence | Certified (4) | A → C |
| 12 | **Report Generation** | Research & Intelligence | Not Implemented | B → C |
| 13 | **Memory & Retrieval** | Memory & Learning | Interfaces only | C |
| 14 | **Reflection & Learning** | Memory & Learning | Not Implemented | C |
| 15 | **Advanced Planning** | Cognitive Engine | Not Implemented | C |
| 16 | **Multi-Agent Coordination** | Cognitive Engine | Not Implemented | C |
| 17 | **Vision & Perception** | Tool & Action | Not Implemented | C |
| 18 | **Computer Use** | Tool & Action | Not Implemented | C |
| 19 | **Communication Hub** | Communication | Partial (Chat) | C |
| 20 | **Product Workspace** | Product Experience | Partial (UI exists) | B |
| 21 | **Platform Operations** | Platform Infrastructure | Not Implemented | D1 |
| 22 | **Commercial Ecosystem** | Commercial Ecosystem | Not Implemented | D2 |

*Note: Major Capability count is approximately 21–22, subject to ratification. Some capabilities (e.g., Research & Evidence) evolve across multiple levels.*

### 5.4 Atomic Functions Inventory

The following 64+ atomic functions implement the major capabilities above. These are not independently certified; they are validated through their parent Major Capability's CAT.

#### Cognitive Engine Domain
| Atomic Function | Parent Major Capability | Level |
|-----------------|------------------------|-------|
| Multi-Step ReAct Reasoning | Tool Orchestration | A |
| LLM Error Resilience | Recovery & Resilience | A |
| Confidence Scoring (3 sub-scores) | Advanced Planning | C |
| Risk-Based Approval Router | Tool Orchestration | A |
| Prompt Composer | Conversational Response | C |
| Context Builder (Memory-aware) | Memory & Retrieval | C |
| Planner (Multi-step decomposition) | Advanced Planning | C |
| Recovery Engine | Recovery & Resilience | A |

#### Tool & Action Domain
| Atomic Function | Parent Major Capability | Level |
|-----------------|------------------------|-------|
| Filesystem Read/Write/List | Filesystem Operations | A |
| Terminal Command Execution | Terminal Execution | A |
| Browser Navigation & Extraction | Browser Automation | A |
| Multi-Page Research Synthesis | Browser Automation | A |
| Vision (Screenshot → LLM) | Vision & Perception | C |
| Computer Use (OS control) | Computer Use | C |
| SSE Real-Time Streaming | Conversational Response | A |

#### Research & Intelligence Domain
| Atomic Function | Parent Major Capability | Level |
|-----------------|------------------------|-------|
| ResearchCase Lifecycle Management | Research & Evidence | B |
| Evidence Collection Pipeline | Research & Evidence | B |
| Source Validation | Research & Evidence | B |
| Structured Evidence Schema | Research & Evidence | B |
| Knowledge Graph Query | Research & Evidence | C |
| PDF Report Generation | Report Generation | C |
| Excel Analysis Export | Report Generation | C |
| Presentation Builder | Report Generation | C |
| Business Proposal Templates | Report Generation | C |

#### Memory & Learning Domain
| Atomic Function | Parent Major Capability | Level |
|-----------------|------------------------|-------|
| Identity Memory Layer | Memory & Retrieval | C |
| User Memory Layer | Memory & Retrieval | C |
| Experience Memory Layer | Memory & Retrieval | C |
| Conversation Memory Layer | Memory & Retrieval | C |
| Task Memory Layer | Memory & Retrieval | C |
| Micro Reflection | Reflection & Learning | C |
| Macro Reflection | Reflection & Learning | C |
| Experience Consolidation | Reflection & Learning | C |
| Knowledge Graph Population | Reflection & Learning | C |
| Adaptive Profile | Reflection & Learning | C |
| Experience Decay | Reflection & Learning | C |

#### Communication Domain
| Atomic Function | Parent Major Capability | Level |
|-----------------|------------------------|-------|
| Direct Chat (Arabic/English) | Conversational Response | A |
| Email (SMTP/IMAP) | Communication Hub | C |
| WhatsApp Integration | Communication Hub | C |
| ERP Connector (REST/SOAP) | Communication Hub | C |

#### Product Experience Domain
| Atomic Function | Parent Major Capability | Level |
|-----------------|------------------------|-------|
| File Upload (Drag & Drop) | Product Workspace | B |
| File Preview | Product Workspace | B |
| Conversation History Sidebar | Product Workspace | B |
| History Search | Product Workspace | B |
| Rich Content Rendering | Product Workspace | B |
| Task Visualization Cards | Product Workspace | B |
| Browser Workspace Preview | Product Workspace | B |
| File Tree Explorer | Product Workspace | B |
| Settings Panel | Product Workspace | B |
| Theme (Dark/Light) | Product Workspace | B |
| RTL Support | Product Workspace | B |
| Export (PDF/Markdown/HTML) | Product Workspace | B |
| Global Search | Product Workspace | B |
| Basic Authentication | Product Workspace | B |
| Session Management | Product Workspace | B |
| Multi-Project Support | Product Workspace | B |
| i18n Foundation | Product Workspace | B |

#### Platform Infrastructure Domain
| Atomic Function | Parent Major Capability | Level |
|-----------------|------------------------|-------|
| Plugin Manager | Plugin Architecture | A |
| Capability Interface | Plugin Architecture | A |
| Tool Interface | Plugin Architecture | A |
| Provider Interface | Plugin Architecture | A |
| Plugin Registry | Plugin Architecture | A |
| State Machine (8 states) | State Machine Management | A |
| Golden Rules Guards | State Machine Management | A |
| Constitution Loader | State Machine Management | A |
| Event Store | Event Sourcing & Replay | A |
| Certification Runner | Event Sourcing & Replay | A |
| Certification Dashboard | Event Sourcing & Replay | A |
| Config Manager (hot-reload) | Platform Operations | A |
| Secrets Manager (encrypted) | Platform Operations | A |
| Audit Logger (immutable) | Platform Operations | A |
| Backup Manager | Platform Operations | A |
| Health Checker | Platform Operations | A |
| Circuit Breaker | Platform Operations | A |
| API Versioning | Platform Operations | A |
| Rate Limiter | Platform Operations | A |
| Schema Migration | Platform Operations | A |
| DI Container | Platform Operations | A |
| Feature Flags | Platform Operations | A |
| Security Hardening (OWASP) | Platform Operations | D1 |
| Docker Containerization | Platform Operations | D1 |
| CI/CD Pipeline | Platform Operations | D1 |
| Monitoring (Prometheus/Grafana) | Platform Operations | D1 |
| Analytics (PostHog/Plausible) | Platform Operations | D1 |
| Performance Optimization | Platform Operations | D1 |
| Scaling (Load balancing) | Platform Operations | D1 |
| Cloud Sync | Platform Operations | D1 |
| API Platform | Platform Operations | D1 |

#### Commercial Ecosystem Domain
| Atomic Function | Parent Major Capability | Level |
|-----------------|------------------------|-------|
| Marketplace | Commercial Ecosystem | D2 |
| Plugin Store | Commercial Ecosystem | D2 |
| Enterprise SSO | Commercial Ecosystem | D2 |
| RBAC | Commercial Ecosystem | D2 |
| Billing & Licensing | Commercial Ecosystem | D2 |
| Desktop Polish (Electron) | Commercial Ecosystem | D2 |
| Notifications | Commercial Ecosystem | D2 |
| Charts & Visualizations | Commercial Ecosystem | D2 |
| Notifications | Commercial Ecosystem | D2 |
| Charts & Visualizations | Commercial Ecosystem | D2 |
| Collaboration (Multi-user) | Commercial Ecosystem | D2 |
| SDK (Python/JS) | Commercial Ecosystem | D2 |
| Developer Platform | Commercial Ecosystem | D2 |
| Community Extensions | Commercial Ecosystem | D2 |
| Full Accessibility (WCAG AA) | Commercial Ecosystem | D2 |
| Full Internationalization | Commercial Ecosystem | D2 |

#### Level E — Future Expansion (Post-Commercialization)
| Atomic Function | Parent Major Capability | Level |
|-----------------|------------------------|-------|
| Mobile App (React Native) | Future Expansion | E |
| PWA (Offline mode) | Future Expansion | E |
| AR/VR Interface | Future Expansion | E |
| Voice Interface | Future Expansion | E |
| Custom Hardware Integration | Future Expansion | E |

*Level E is not scheduled. It represents the expansion frontier after D1 and D2 are certified. Functions in Level E are candidates for self-development proposals once the Evolution Engine is mature.*

### 5.5 Capability Certification Targets

The ratification target is **21 Major Capabilities** at Maturity Level 4 (Production Ready). Atomic functions are validated through their parent capability's CAT. No atomic function may be certified independently of its major capability.

---

## 6. Capability Contract Framework

### 6.1 Interface + Registry + Contract Pattern

Every capability must be implemented as:
- **Interface (ABC):** Defines the contract. Cannot be changed without version bump.
- **Registry:** Discovers and routes to implementations.
- **Contract (Markdown):** Human-readable specification of behavior, inputs, outputs, error modes, and certification criteria.

**Example Interfaces:**

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

### 6.2 Capability Acceptance Test (CAT)

A capability is not complete without a CAT. The CAT defines the minimum bar for certification.

**CAT Template:**
```yaml
capability: "Market Research"
version: "1.0"
prerequisites:
  - "Plugin Architecture loaded"
  - "Browser Engine operational"
  - "Filesystem write access"
scenarios:
  - name: "Create Research Case"
    given: "User submits complex objective"
    when: "System processes intent"
    then: 
      - "ResearchCase entity created"
      - "Plan with ≥3 steps generated"
      - "Confidence score ≥ 0.70"
  - name: "Multi-Step Execution"
    given: "ResearchCase with plan"
    when: "System executes steps"
    then:
      - "≥3 sources collected"
      - "Evidence stored with timestamps"
      - "Progress updated after each step"
  - name: "Resume After Interruption"
    given: "ResearchCase interrupted at step 3"
    when: "System restarts"
    then:
      - "State restored to step 3"
      - "No data loss"
      - "User notified of resume"
  - name: "Professional Report Generation"
    given: "ResearchCase completed"
    when: "Report requested"
    then:
      - "PDF generated with cover page"
      - "Sources cited with URLs"
      - "Confidence summary included"
```

### 6.3 Certification Process

1. **Define:** Interface + Contract + CAT written
2. **Implement:** Code written as plugin
3. **Unit Test:** ≥90% coverage for new code
4. **Integration Test:** Module boundaries verified
5. **Browser Acceptance:** Playwright E2E with real frontend
6. **Live Benchmark:** Real LLM + real tools, frozen and versioned
7. **Regression Suite:** All previous benchmarks pass
8. **Documentation:** Contract + usage examples committed
9. **Dashboard Update:** Maturity level updated
10. **Freeze:** Benchmark becomes canonical (immutable)

---

## 7. Memory & Knowledge Architecture

### 7.1 Memory Mesh (5 Layers)

MOZA maintains 5 distinct memory layers, each with different write triggers, read triggers, retention policies, and archive rules.

| Layer | Purpose | Write Trigger | Read Trigger | Retention | Archive |
|-------|---------|---------------|--------------|-----------|---------|
| **Identity** | Who am I? Constitution, Golden Rules, Learned Rules | Startup / Rule Consolidation | Every prompt | Permanent | Never |
| **User** | Who is the user? Preferences, habits, common paths | End of session / Macro Reflection | Every prompt | Permanent | Never |
| **Experience** | What have I learned? Patterns, failures, optimizations | Macro Reflection / Consolidation | Planning phase | 90 days | After decay |
| **Conversation** | What are we discussing? Chat history, context | Every turn | Next turn | 20 turns | After session |
| **Task** | What am I doing right now? Current task state | Every step | Current task | Task duration | 24 hours |

### 7.2 Storage Backends

- **Identity:** `constitution.yaml` (immutable file)
- **User:** SQLite (`memory/user.db`)
- **Experience:** SQLite + JSON (`memory/experience.db`)
- **Conversation:** SQLite (`memory/conversation.db`)
- **Task:** In-memory + 24h JSONL archive

### 7.3 Retrieval Strategy

- **Identity:** Loaded at startup, injected into all prompts
- **User:** Retrieved per user, injected by Prompt Composer
- **Experience:** Retrieved by similarity (embedding or keyword), used for planning
- **Conversation:** Retrieved by session ID, used for context window
- **Task:** Retrieved by task ID, used for orchestrator state

### 7.4 Knowledge Graph

- **Storage:** SQLite + JSON
- **Schema:**
  - `entities` (id, type, name, embedding)
  - `relations` (source, target, type, weight)
- **Entity Types:** Tool, File, URL, Error, Concept, UserPreference
- **Relation Types:** uses, produces, fixes, causes, depends_on
- **Population:** Automatic from task events, reflection reports, user feedback
- **Query Interface:** `find_related(entity, relation_type, depth)`

*Note: Memory Mesh interfaces will be defined in Level A. Full implementation is scheduled for Level C. Until then, existing context slicing remains operational as fallback.*

---

## 8. Research Case Model

### 8.1 ResearchCase as Core Entity

A ResearchCase represents a long-running, complex investigation with structured lifecycle management. It is the primary domain object for objectives such as market analysis, competitive research, or due diligence.

**ResearchCase Structure:**
```yaml
ResearchCase:
  id: uuid
  goal: string                    # Human objective
  plan: Plan                      # Multi-step decomposition
  tasks: List[Task]               # Executable units
  evidence: List[Evidence]        # Structured evidence items
  sources: List[Source]           # Validated references
  confidence: ConfidenceScore     # Composite score
  progress: ProgressTracker       # Step completion status
  final_report: Report            # Generated output
  resume_state: ResumeSnapshot    # Interruption recovery data
  status: ResearchCaseStatus      # Idle | Planning | Executing | WaitingApproval | Reflecting | Recovering | Completed | Failed
  created_at: timestamp
  updated_at: timestamp
  owner: user_id
```

### 8.2 Relationship to State Machine

**Current Architecture (Level A–B):**
The existing 8-state State Machine manages `Task` lifecycle. ResearchCase is implemented as a **domain layer above** the Task/State architecture. A ResearchCase contains multiple Tasks, and the Orchestrator manages Task state transitions while the ResearchCase Manager coordinates across Tasks.

**Future Architecture (Level C+):**
When Memory Mesh and advanced Planning are mature, an ADR may propose elevating ResearchCase to be managed directly by the State Machine. This is explicitly deferred and requires:
1. ADR documenting migration path
2. Backward compatibility plan for existing Task-based events
3. Dual-mode operation period
4. Manager approval

### 8.3 ResearchCase Lifecycle

```
User Objective
    ↓
[Intent Classifier] → CONFIDENCE ≥ 0.70?
    ↓ YES
[Planner] → Decompose into steps
    ↓
[ResearchCase Created] → ID assigned, Goal stored
    ↓
[Step Execution Loop]
    ├── Execute Tool / Browse / Analyze
    ├── Collect Evidence
    ├── Update Progress
    ├── Micro Reflection
    └── Confidence Re-evaluation
    ↓
[All Steps Complete?]
    ↓ YES
[Macro Reflection] → Lessons learned
    ↓
[Report Generation] → PDF / Excel / Presentation
    ↓
[ResearchCase Completed] → Archive to Task Memory
```

### 8.4 Resume State

ResearchCase must survive interruption without data loss:
- **ResumeSnapshot:** Serialized state including current step, collected evidence, open browser sessions, pending approvals
- **Storage:** Task Memory layer + JSONL backup
- **Recovery:** On system restart, scan for incomplete ResearchCases and offer resume
- **Timeout:** Incomplete cases auto-archived after 7 days of inactivity

---

## 9. Evidence & Trust Model

### 9.1 Evidence Taxonomy

MOZA must explicitly distinguish between four types of information:

| Type | Definition | Example | Trust Level |
|------|------------|---------|-------------|
| **Fact** | Independently verifiable, directly observed | "The company's revenue is $50M" (from audited PDF) | High |
| **Source Claim** | Attributed to a source, not independently verified | "The CEO stated revenue will double" (from news article) | Medium |
| **Assumption** | Necessary for reasoning but not verified | "Market growth will continue at 5% CAGR" | Low |
| **Unknown** | Acknowledged gap in knowledge | "Competitor's pricing strategy is unclear" | None |

### 9.2 Structured Evidence Schema

Every piece of evidence collected by MOZA must conform to this schema:

```json
{
  "claim": "string",
  "source": {
    "url": "string",
    "title": "string",
    "accessed_at": "ISO8601",
    "retrieval_method": "browser|api|file|user_input"
  },
  "evidence_type": "fact|source_claim|assumption|unknown",
  "reliability": "high|medium|low",
  "confidence": 0.0,
  "timestamp": "ISO8601",
  "verification_status": "verified|pending|unverifiable",
  "corroborating_evidence": ["evidence_id"],
  "contradicting_evidence": ["evidence_id"]
}
```

### 9.3 Confidence Scoring

Composite confidence is calculated from three sub-scores:

```python
composite_confidence = (
    intent_confidence * 0.35 +
    capability_confidence * 0.30 +
    plan_confidence * 0.35
)
```

**Risk-Based Routing:**
| Risk Class | Examples | Confidence Threshold | Action |
|------------|----------|---------------------|--------|
| L0 — Read-Only | Read file, list dir, browse page | ≥ 0.10 | Auto — Execute immediately |
| L1 — Informative | git status, pytest --collect-only, screenshot | ≥ 0.30 | Auto — Log only |
| L2 — Mutating (Safe) | Write new file, create directory | ≥ 0.50 | Log + Notify — Execute but record |
| L3 — Mutating (Risky) | Overwrite existing file, pip install, form submit | ≥ 0.70 | Ask — Pause for human approval |
| L4 — Destructive | Delete file/directory, rm -rf, send email/WhatsApp | ≥ 0.95 | Block — Always require approval |

**Rule:** Risk Class is determined by the tool's `is_destructive` and `requires_confirmation` flags, NOT by the LLM's confidence.

### 9.4 Evidence Collection Pipeline

1. **Source Retrieval:** Browser, API, or file access
2. **Extraction:** Structured data extraction (tables, text, metadata)
3. **Classification:** Fact / Source Claim / Assumption / Unknown
4. **Validation:** Cross-reference with existing evidence (corroboration/contradiction)
5. **Storage:** Evidence added to ResearchCase evidence list
6. **Attribution:** Source URL and timestamp recorded for every claim

---

## 10. Reporting & Output System

### 10.1 Output Capabilities

MOZA must generate professional outputs suitable for business and research contexts:

| Output Type | Format | Use Case | Level |
|-------------|--------|----------|-------|
| Research Report | PDF | Investor-grade analysis, due diligence | B/C |
| Data Analysis | Excel / CSV | Financial modeling, market data | B/C |
| Presentation | PPTX / PDF slides | Executive summaries, pitches | C |
| Business Proposal | PDF | Partnership proposals, project plans | C |
| Research Summary | Markdown | Quick reference, internal sharing | B |
| Structured Data | JSON / YAML | API consumption, further processing | A |

### 10.2 Report Structure

A professional MOZA report must include:
1. **Cover Page:** Title, date, version, classification
2. **Executive Summary:** 1-page overview with key findings
3. **Methodology:** How research was conducted, tools used, date range
4. **Findings:** Structured sections with evidence references
5. **Evidence Appendix:** All sources cited with URLs, access dates, and reliability ratings
6. **Confidence Summary:** Composite score and risk assessment
7. **Limitations:** Acknowledged gaps, assumptions, and unknowns
8. **Recommendations:** Actionable next steps (if applicable)

### 10.3 Report Generation Pipeline

```
ResearchCase Completed
    ↓
[Report Template Selection] → Based on output type
    ↓
[Content Assembly] → Evidence → Markdown → Rich formatting
    ↓
[Source Attribution] → Inline citations + Appendix
    ↓
[Confidence Annotation] → Highlight high/medium/low reliability claims
    ↓
[Export Engine] → PDF (LaTeX/WeasyPrint) / Excel (OpenPyXL) / PPTX (python-pptx)
    ↓
[Delivery] → Download link, email attachment, or workspace file
```

### 10.4 Template System

Reports must be template-driven:
- **Templates stored as:** Markdown + Jinja2 with metadata headers
- **Customizable:** Logo, colors, language (Arabic/English), section order
- **Extensible:** New templates added via Plugin Architecture without core modification

---

## 11. Quality Gates

### 11.1 Testing Pipeline

Every capability must pass through:

**Implementation → Unit Tests → Integration Tests → Browser Acceptance → Regression Suite → Confidence Sign-off**

| Stage | Tools | Criteria |
|-------|-------|----------|
| Unit Tests | pytest, asyncio | ≥ 90% coverage for new code, all pass |
| Integration Tests | pytest, httpx ASGITransport | Module boundaries, event flow, state transitions |
| Browser Acceptance | Playwright, npm run build | Frontend builds, zero console errors, zero 404s |
| Regression Suite | pytest + live benchmarks | 94+ tests pass, 5 frozen benchmarks pass |
| Confidence Sign-off | Manual review | ≥ 95% confidence, no known blockers |

### 11.2 Regression Preservation Policy

**This policy enforces the "Evolution must be additive, not destructive" principle.**

1. **Frozen Benchmarks are Permanent.** Once a capability benchmark is frozen, it cannot be modified or disabled without an ADR and manager approval.
2. **Zero Regression Mandate.** Any change that breaks a frozen benchmark is halted immediately. The change must be reworked to preserve the benchmark or abandoned.
3. **Additive Only.** New capabilities must not alter existing capability interfaces, event schemas, or benchmark expectations.
4. **Migration Plans Required.** If a breaking change is absolutely necessary (e.g., security fix), a migration plan must be written, reviewed, and approved before implementation.
5. **Regression Test Execution.** After every implementation step, the following must pass:
   - All existing unit tests (94+ per Execution Plan v4.0)
   - All 5 frozen canonical benchmarks
   - All previously certified capability benchmarks
   - Frontend build without errors
6. **Emergency Override.** Only with `manager-approve` tag in commit + 2 reviewer sign-offs + documented justification.
7. **Certification over Test Count.** The number of tests is secondary. Capability certification is primary. A capability with 10 passing tests that proves real-world value is preferred over 100 tests that prove nothing.

### 11.3 Capability Acceptance Test (CAT) Gate

No capability may be declared complete until:
- [ ] CAT is written in YAML and committed to `benchmarks/`
- [ ] CAT is executed against the real system (not mocks)
- [ ] CAT passes with ≥ 95% confidence
- [ ] CAT is frozen and added to the regression suite
- [ ] Documentation is updated

### 11.4 Capability Preservation Matrix

**Backward Compatibility is a first-class acceptance criterion.** A capability is not considered complete if it only works independently but degrades existing certified capabilities.

Every new capability addition requires:

1. **Impact Analysis:** Document which existing capabilities, interfaces, event schemas, and benchmarks may be affected.
2. **Regression Verification:** Automated tests must prove that all previously certified capabilities continue to function at their certified maturity level.
3. **Compatibility Confirmation:** The new capability must coexist with all existing capabilities without requiring modifications to their contracts or implementations.

**Sample Preservation Matrix:**

| New Capability | Chat | Filesystem | Browser | Terminal | Plugins | Router | Memory | Event Bus | State Machine | Impact |
|---------------|------|------------|---------|----------|---------|--------|--------|-----------|---------------|--------|
| Market Research | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | ✓ | ✓ | Low |
| Vision Tool | ✓ | — | ✓ | — | ✓ | ✓ | — | ✓ | ✓ | Low |
| Memory Mesh | ✓ | — | — | — | — | ✓ | New | ✓ | — | Medium* |
| Multi-Agent | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | High |

*Medium impact because Memory Mesh introduces new event types and context retrieval paths, but existing context slicing must remain operational as fallback.

**Preservation Rules:**
- A new capability that requires modifying an existing capability interface must be rejected or escalated to ADR.
- A new capability that breaks any frozen benchmark is automatically halted.
- A new capability that changes event schema format (not just additive fields) requires version bump and dual-mode support.
- The Preservation Matrix must be included in every capability's Design Document.

### 11.5 Additive Evolution Enforcement

Before any PR is approved, the reviewer must confirm:
- [ ] No existing capability interfaces were modified
- [ ] No existing event schemas were changed (only extended)
- [ ] All frozen benchmarks pass
- [ ] New code has ≥ 90% unit test coverage
- [ ] New capability has a CAT
- [ ] Capability Preservation Matrix completed and reviewed
- [ ] Documentation updated (Contract, ADR if needed, Changelog)

---

## 12. Security Principles

### 12.1 Security Layers

1. **Authentication** — Who is the user?
2. **Authorization** — What can the user do?
3. **Encryption** — Protect data at rest and in transit
4. **Audit** — Track all actions immutably
5. **Compliance** — GDPR, OWASP Top 10

### 12.2 Risk-Based Approval Matrix

*(See Section 9.3 for full matrix)*

**Key Rule:** L4 (Destructive) operations always require human approval, regardless of confidence score. L3 (Risky) operations require approval if confidence < 0.70.

### 12.3 Security Postponement Risk

*Architect Review Note:* Security hardening (OWASP Top 10, penetration testing, formal encryption) is scheduled for Level D (months 7–12). However, Levels A–C handle user files, terminal commands, browser automation, and API secrets. This creates a **liability window** where the system is operationally capable of destructive actions but lacks formal security audit.

**Mitigation (Required):**
- All secrets must use placeholder/encrypted storage from Level A onward (even if full Secrets Manager is Level A.9)
- Terminal tool must maintain `is_destructive` flag and L4 classification for `rm`, `format`, etc.
- Browser tool must not auto-submit forms or download executables without L3 approval
- Event Bus must log all destructive operations immediately (immutable audit trail)

### 12.4 Plugin Security

- All plugins must declare permissions (read, write, network, execute)
- Plugins with `execute` or `write` permissions require explicit user activation
- Plugin code must be auditable (no obfuscated plugins in official marketplace)
- Sandboxed execution for untrusted plugins (Level D1)

### 12.5 Level A Security Baseline

While full security hardening (OWASP Top 10, penetration testing, enterprise RBAC, SSO) is deferred to Level D1, a **mandatory security baseline** must be implemented in Level A to protect the system during its formative stages.

**Scope (Strictly Limited):**

1. **Secret Isolation and API Key Protection**
   - All LLM API keys, database credentials, and third-party tokens must be stored outside source code
   - `secrets_manager.py` with encryption at rest (AES-256 or equivalent)
   - No plaintext secrets in `config.yaml`, environment variables only for runtime injection
   - Secret rotation support (interface prepared, implementation may be manual in Level A)

2. **Tool Permission Boundaries**
   - Every tool must declare its permission set (read, write, execute, network)
   - The `is_destructive` flag is mandatory for all tools
   - Tools cannot escalate their own permissions at runtime
   - Tool permission violations trigger automatic L4 blocking and audit logging

3. **File Access Restrictions**
   - Filesystem tool must enforce path sandboxing (no access outside workspace without explicit approval)
   - Symlink traversal attacks must be prevented
   - Hidden file access (`.env`, `.ssh`, etc.) requires L3 approval minimum
   - Write operations to existing files require L3 approval (overwrite protection)

4. **Logging of Dangerous Actions**
   - All L3 and L4 operations are logged with immutable audit events
   - Log entries include: user, tool, action, arguments, timestamp, approval status
   - Audit logs are append-only and tamper-evident (hash chain or append-only file permissions)
   - Log retention: minimum 90 days

5. **Prevention of Silent Destructive Operations**
   - No destructive operation may execute without explicit approval or explicit user confirmation
   - Batch operations (e.g., recursive delete) require per-operation confirmation or explicit batch approval
   - The system must never assume approval based on context or previous approvals
   - Auto-approval is permitted **only** for L0 (read-only) and L1 (informative) operations

**Explicitly Deferred to Level D1:**
- Enterprise SSO and RBAC
- OWASP Top 10 formal compliance audit
- Penetration testing
- GDPR compliance framework
- Network-level security (WAF, DDoS protection)
- Advanced threat detection

**Liability Window Acknowledgment:**
MOZA Levels A–C operate with this baseline security, not full hardening. User-facing documentation must state: *"MOZA is in active development. Do not use with sensitive production data until D1 security certification is complete."*

---

## 13. ADR Framework

### 13.1 When an ADR is Required

An Architecture Decision Record (ADR) must be created for:
1. Any change to an interface (CapabilityInterface, ToolInterface, ProviderInterface)
2. Any breaking change to event schemas
3. Any modification to the State Machine states or transitions
4. Any deprecation of a capability or tool
5. Any change to Golden Rules or Constitution
6. Any addition of a new core component (not a plugin)
7. Any change to the Memory Mesh schema
8. Any security architecture change
9. Any change to the ResearchCase model (after initial ratification)
10. Any timeline or scope change to Evolution Levels

### 13.2 ADR Template

```markdown
# ADR-XXX: Title

## Status
- Proposed / Accepted / Deprecated / Superseded by ADR-YYY

## Context
What is the issue that we're seeing that is motivating this decision or change?

## Decision
What is the change that we're proposing or have agreed to implement?

## Consequences
What becomes easier or more difficult to do because of this change?

## Compliance
- [ ] Backward compatibility addressed
- [ ] Migration plan included (if breaking)
- [ ] Interfaces updated
- [ ] Tests updated
- [ ] Documentation updated
- [ ] Manager approval obtained
```

### 13.3 ADR Registry

All ADRs live in `docs/ADRs/` and are indexed in `docs/ADRs/README.md`. ADRs are immutable once Accepted. Changes require a new ADR that supersedes the old one.

---

## 14. Execution Roadmap

**Governance Note:** Quality gates, regression stability, and Capability Acceptance Tests take absolute priority over timeline estimates. Dates are targets, not deadlines. A level is not complete until all exit criteria are met, regardless of calendar position.

### 14.1 Level A — Core Foundation (النواة)

**Duration:** 60–90 days  
**Purpose:** Immutable core that will never be redesigned. Anything requiring rebuilding later must exist here.

**Key Deliverables:**
- Plugin Architecture (Manager + Registry + Interfaces)
- 8-State State Machine (wraps existing orchestrator)
- Golden Rules Guards (extracted from prompts to code)
- Constitution Loader (`constitution.yaml`)
- Event Sourcing + Event Store
- Certification Framework (runner + dashboard)
- Configuration Manager (hot-reload)
- Secrets Manager (encrypted)
- Audit Logger (immutable)
- Backup Manager
- Health Checker (`/health`, `/ready`)
- Circuit Breaker + Fallback
- API Versioning (`/v1/`, `/v2/`)
- Rate Limiter
- Schema Migration Manager
- Dependency Injection Container
- Feature Flags
- Empty Interfaces: Memory, Reflection, Learning, Evolution
- **Level A Security Baseline** (see Section 12.5)

**Exit Criteria:**
- All 22 steps complete (per Execution Plan v4.0)
- 94+ existing tests pass
- 5 frozen benchmarks pass
- Level A Security Baseline verified
- Frontend build succeeds
- Confidence ≥ 95%

### 14.2 Level B — Core Product (المنتج)

**Duration:** 45–60 days  
**Purpose:** Transform the core into a daily-use product with professional UX.

**Key Deliverables:**
- File Upload (Drag & Drop)
- Conversation History (Sidebar + Search)
- Rich Content Renderer (Code, Images, PDFs)
- Task Visualization Cards
- Browser Workspace (Live preview)
- File Tree Explorer
- Settings Panel (Model, Temperature, Theme)
- Export/Share (PDF, Markdown, HTML)
- Global Search
- Basic Authentication
- Session Management
- Multi-Project Support
- Theme (Dark/Light) + RTL Support
- i18n Foundation

### 14.3 Level C — Intelligence Expansion (الذكاء)

**Duration:** 60–90 days  
**Purpose:** Make the system intelligent — memory, reflection, learning, planning.

**Key Deliverables:**
- Memory Mesh (5 layers, 3 backends)
- Reflection Engine (Micro + Macro)
- Learning Pipeline (Consolidation + Knowledge Graph)
- Adaptive Profile
- Advanced Confidence Engine (3 sub-scores)
- Advanced Planning Engine
- Basic Multi-Agent
- Vision Tool
- Computer Use Tool
- Email Tool
- WhatsApp Tool
- ERP Tool

### 14.4 Level D1 — Platform Maturity (النضج التقني)

**Duration:** 60–90 days  
**Purpose:** Harden the platform for production deployment, security, reliability, and observability. This is the foundation for commercial viability.

**Key Deliverables:**
- Security Hardening (OWASP Top 10, penetration testing)
- Docker Containerization + Docker Compose
- CI/CD Pipeline (GitHub Actions)
- Monitoring (Prometheus + Grafana)
- Analytics (PostHog or Plausible)
- Performance Optimization (Redis, CDN, caching)
- Scaling (Load balancing, horizontal)
- Cloud Sync
- API Platform (Public API + documentation)
- Full Accessibility (WCAG 2.1 AA)
- Full Internationalization

### 14.5 Level D2 — Ecosystem & Commercialization (النظام التجاري)

**Duration:** 90–120 days  
**Purpose:** Transform the mature platform into a commercial ecosystem with marketplace, mobile presence, enterprise features, and revenue models.

**Key Deliverables:**
- Marketplace + Plugin Store
- Enterprise SSO + RBAC
- Billing & Licensing (Subscription management)
- Mobile App (React Native or Expo)
- Desktop Polish (Electron enhancements)
- PWA (Offline mode)
- Notifications (Push + Email)
- Charts & Visualizations
- Collaboration (Multi-user, real-time)
- SDK (Python + JavaScript)
- Developer Platform (Plugin dev tools, docs)
- Community Extensions

### 14.6 Level E — Future Expansion (Post-Commercialization)

**Duration:** Not scheduled  
**Purpose:** Frontier capabilities that extend MOZA beyond its commercial platform foundation. These are candidates for self-development proposals and community contributions once D1 and D2 are certified.

**Candidate Deliverables:**
- Mobile App (React Native or Expo)
- PWA (Offline mode)
- AR/VR Interface
- Voice Interface
- Custom Hardware Integration

**Entry Criteria:** D1 and D2 certified, Evolution Engine operational, self-development pipeline proven.

### 14.7 Timeline Reality Check

*Per Execution Plan v4.0, the original timeline estimated 225–315 days (7.5–10.5 months). With the revised Level A duration (60–90 days) and the D1/D2 split, the realistic timeline is:*

| Level | Duration | Cumulative |
|-------|----------|------------|
| A | 60–90 days | 60–90 days |
| B | 45–60 days | 105–150 days |
| C | 60–90 days | 165–240 days |
| D1 | 60–90 days | 225–330 days |
| D2 | 90–120 days | 315–450 days |

*Total: 315–450 days (10.5–15 months) with approval cycles, testing, documentation, and unforeseen complexity. This is flagged in Architect Review Notes for discussion.*

---

## 15. Capability Maturity Model

### 15.1 Maturity Levels

| Level | Name | Description | Certification Required |
|-------|------|-------------|----------------------|
| 0 | Not Implemented | Capability does not exist | No |
| 1 | Basic Functionality | Works in simplest cases | No |
| 2 | Error Handling | Handles failures gracefully | No |
| 3 | Realistic Scenarios | Works independently in real-world cases | Yes |
| 4 | Production Ready | Reliable, documented, tested, benchmark frozen | Yes |
| 5 | Trusted Autonomy | Can execute without direct supervision | Yes + 30-day observation |

### 15.2 Promotion Criteria

- **0 → 1:** Code compiles, basic test passes
- **1 → 2:** Error cases handled, logs generated
- **2 → 3:** CAT passes on realistic scenario, documentation complete
- **3 → 4:** All tests pass, benchmark frozen, regression suite includes it, ≥ 95% confidence
- **4 → 5:** 30 days of production use without failure, macro reflection shows consistent success, user feedback positive

### 15.3 Demotion Policy

A capability may be demoted only by ADR with manager approval. Demotion triggers:
- Frozen benchmark fails and cannot be fixed within 48 hours
- Security vulnerability discovered
- Dependency becomes unmaintainable
- Capability is superseded by a newer capability (with migration plan)

---

## 16. Deferred Decisions

The following decisions are intentionally postponed to later levels to avoid premature optimization or over-engineering.

| Decision | Deferred To | Reason | Risk |
|----------|-------------|--------|------|
| Memory Implementation | Level C | Interfaces sufficient for Level A/B; implementation requires Level C planning engine | Medium: Context slicing is fallback |
| Reflection Implementation | Level C | Requires Memory Mesh to store insights | Low: No reflection means no learning, but system works |
| Learning Implementation | Level C | Requires Reflection Engine to generate experiences | Low: System operates without learning |
| Security Hardening | Level D1 | Commercial requirement; Level A Security Baseline mitigates interim risk | **Medium: See Section 12.5** |
| Performance Optimization | Level D1 | Not needed until scaling requirement | Low: Current performance acceptable for single-user |
| Mobile App | Level E | Product must be stable before multi-platform; native clients deferred post-commercialization | Low: Desktop + Web sufficient through D2 |
| Marketplace | Level D2 | Requires plugin ecosystem maturity | Low: Manual plugin loading works in Level A |
| Enterprise SSO/RBAC | Level D2 | Commercial requirement; basic auth sufficient for product level | Low: Local auth works in Level B |
| Self-Development Engine | Level C/D | Foundation must be mature before system can modify itself | Medium: Interfaces prepared in Level A |
| ResearchCase State Machine Integration | Level C+ | Current Task/State architecture sufficient; migration requires ADR | Low: ResearchCase works as domain layer |
| Browser Profile Persistence | Level B/C | Isolated mode sufficient for research; persistent mode requires auth | Low: User can re-authenticate per session |

---

## 17. Migration Map

### 17.1 From Current to Level A

**Strategy:** Additive wrapping. No existing files deleted.

1. Create `constitution.yaml` alongside `config.yaml`
2. Create `state_machine.py` — wrap existing orchestrator transitions (no breaking changes)
3. Create `guards.py` — extract Golden Rules from `litellm_tool_agent.py` prompt, keep prompt as fallback during transition
4. Create `plugins/` directory — opt-in, existing tools work without it
5. Create all core infrastructure files (event_store, config_manager, etc.) — additive only
6. Expand `TaskStatus` enum from 6 to 8 states — maintain backward compatibility with old state names

### 17.2 From Level A to Level B

**Strategy:** UI enhancement. Backend core untouched.

1. Add frontend components alongside existing ones
2. Add backend API routes (upload, history, export) — new endpoints only
3. Enhance `ChatInterface.tsx` with optional file upload and rich content
4. Add `HistorySidebar.tsx` as collapsible panel

### 17.3 From Level B to Level C

**Strategy:** Intelligence layer insertion. Fallbacks maintained.

1. Create Memory Mesh alongside existing context slicing
2. Keep context slicing as fallback during transition
3. Add reflection hooks as optional (feature flag)
4. Register new tools via Plugin Architecture (no existing tool modification)

### 17.4 From Level C to Level D

**Strategy:** Platform wrapping. Core capabilities preserved.

1. Add security layer alongside existing auth
2. Add Docker as optional deployment
3. Add marketplace as opt-in feature
4. All new features behind feature flags

### 17.5 ResearchCase Migration Path

**Current:** Task/State architecture manages execution. ResearchCase is a conceptual wrapper.

**Future (requires ADR):**
1. ADR proposed to elevate ResearchCase to core entity
2. Dual-mode period: ResearchCase and Task operate in parallel
3. Event schema versioning to handle both entity types
4. Gradual migration of benchmarks to ResearchCase-centric tests
5. Task architecture deprecated only after 100% of workflows migrated

---

## 18. Evolution Governance

*This section is added per explicit requirement to govern how MOZA evolves as a living system, particularly when it begins participating in its own development.*

### 18.1 Purpose

MOZA is not a static application. It is a system designed to evolve — eventually under its own suggestion. Evolution Governance ensures that growth remains safe, traceable, and human-supervised.

### 18.2 Change Proposal Process

Any change to MOZA — whether proposed by a human engineer or by MOZA itself — must follow this pipeline:

```
Idea → Design Document → Impact Analysis → Review → Implementation → Certification → Regression → Approval → Merge
```

**1. Idea**
- Source: Human request, user feedback, telemetry insight, or MOZA self-analysis
- Format: One-paragraph description + motivation

**2. Design Document**
- Interface changes (if any)
- Capability contract (if new)
- CAT definition
- Migration plan (if breaking)
- Backward compatibility analysis
- Security impact assessment

**3. Impact Analysis**
- Which existing capabilities are affected?
- Which frozen benchmarks might be impacted?
- Which files require modification?
- Risk classification (L0–L4)

**4. Review**
- Architecture review (against this Master Plan)
- Security review (for L2+ changes)
- Performance review (for Level D changes)

**5. Implementation**
- Feature flag protection
- Incremental commits
- Tests written before or with code

**6. Certification**
- CAT execution
- Benchmark freezing
- Documentation update

**7. Regression**
- All frozen benchmarks pass
- All previous capabilities verified

**8. Approval**
- Manager approval for architectural changes
- Automated approval for L0/L1 plugin additions (after CI passes)

**9. Merge**
- Merge to `develop` branch
- Integration testing
- Promotion to `main` with `manager-approve` tag

### 18.3 Capability Promotion

A capability is promoted from one maturity level to the next only when:
- [ ] All CAT scenarios pass at the target level
- [ ] 30 days of operational data supports promotion (for Level 4 → 5)
- [ ] No regression in dependent capabilities
- [ ] Documentation reflects new maturity level
- [ ] Certification Dashboard updated
- [ ] Manager approval obtained

**Demotion:** A capability may be demoted (see Section 15.3) but never removed without an ADR.

### 18.4 Deprecation Policy

1. **Deprecation Notice:** 2-level advance warning (e.g., if deprecating in Level C, notice given in Level A)
2. **Migration Path:** Every deprecation must include a replacement or migration guide
3. **Backward Compatibility:** Deprecated interfaces remain operational during the notice period
4. **Final Removal:** Only after ADR approval and all dependent capabilities migrated
5. **Archive:** Deprecated code moved to `archive/` directory, not deleted, for 12 months

### 18.5 Backward Compatibility Guarantee

**This is a binding architectural commitment.**

- **Public APIs:** `/v1/` endpoints remain stable. New versions use `/v2/`, `/v3/`, etc.
- **Event Schemas:** Old event formats must be readable by new code. New fields are additive only.
- **Plugin Interfaces:** `CapabilityInterface`, `ToolInterface`, `ProviderInterface` are versioned. Plugins targeting v1.0 must work with v1.1 runtime.
- **Configuration:** `config.yaml` keys are never renamed without alias support.
- **ResearchCase Schema:** Once ratified, schema changes require version bump and dual-mode support.

### 18.6 Human Authority Principle (Non-Negotiable)

**This principle is absolute and binding.**

MOZA may autonomously propose, analyze, test, and prepare changes. However, MOZA may **NOT** autonomously approve or execute architectural changes affecting:
- Core system architecture (State Machine, Orchestrator, Event Bus)
- Security models (authentication, authorization, encryption)
- Data ownership and privacy boundaries
- User permission models
- Capability removal or demotion
- Constitution or Golden Rules modifications

A **mandatory human gate** is required for these actions. This principle does not prevent autonomous execution of low-risk operational tasks that have already been explicitly authorized by policy (e.g., running a certified research workflow, generating a report from an approved template, or executing a pre-approved plugin within its permission boundary).

**Operational Boundary:**
| Autonomous (No Human Gate) | Human Gate Required |
|------------------------------|---------------------|
| Planning and research | Architectural changes |
| Evidence collection | Security model changes |
| Report drafting | Data ownership changes |
| Tool execution within L0/L1 | User permission changes |
| Running certified plugins | Capability removal |
| Self-analysis and telemetry | Constitution modifications |
| Proposing improvements (draft only) | Approving self-development proposals |

### 18.7 Approval Authority

| Change Type | Authority | Required Approval |
|-------------|-----------|-------------------|
| L0/L1 plugin addition | CI/CD + Automated tests | Automated |
| L2 capability modification | Engineering lead | 1 reviewer |
| L3 architectural change | Architect | Manager + 1 reviewer |
| L4 constitution change | Project manager | Manager + 2 reviewers + ADR |
| Breaking change (any level) | Architect | Manager + ADR + migration plan |
| Self-development proposal | MOZA (proposer) + Human (approver) | **Mandatory human gate per 18.6** |

**Self-Development Special Rule:**
When MOZA proposes changes to itself:
- The proposal is treated as L3 minimum (architectural change)
- Human manager approval is **mandatory** — never automated
- Implementation occurs in `exp/*` branch, never `main` or `develop`
- Full certification and regression required before merge consideration
- MOZA cannot approve its own proposals, even with high confidence
- **MOZA cannot override the Human Authority Principle under any confidence score or reasoning path**

---

## 19. Architect Review Notes

*This section contains independent critical analysis of the MOZA plan. It challenges assumptions, flags risks, and recommends mitigations. It does not modify existing decisions automatically.*

### 19.1 Observations

#### Observation 1: Dual SSOT Risk — HIGH
**Issue:** Both this Master Plan and the Execution Plan v4.0 claim to be the "Single Source of Truth." The Execution Plan states: *"This execution plan is NOT a roadmap for building MOZA. It is a roadmap for EVOLVING the existing MOZA"* and *"This plan is FINAL."*

**Risk:** Over time, these documents will diverge. Implementation decisions in the Execution Plan may contradict governance rules in the Master Plan, creating confusion for coding agents and reviewers.

**Recommendation:**
- Ratify the hierarchy explicitly: **Master Plan governs architecture and principles; Execution Plan governs implementation tasks.**
- Add a "Constitution Compliance Check" to the Execution Plan's task completion criteria: *"Verify this task does not violate any Master Plan principle or ADR."*
- Schedule quarterly document reconciliation reviews.

#### Observation 2: Level A Timeline Appears Optimistic — MEDIUM
**Issue:** Level A lists 22 steps (A.1–A.22), each requiring implementation, unit tests, integration tests, browser acceptance, documentation, commit, push, and **explicit user approval wait**. At 1–2 days per step with approval cycles, 22 steps could realistically require 60–90 days, not 30–45.

**Risk:** Timeline pressure leads to skipped tests, incomplete documentation, or approval bypass.

**Recommendation:**
- Extend Level A timeline to 60–75 days, or reduce scope by moving non-critical items (e.g., API Versioning, Rate Limiting) to Level B.
- Alternatively, parallelize: some steps (A.19–A.22 interface definitions) can proceed while earlier steps are in review.
- Add buffer time for "unknown unknowns" (20% contingency).

#### Observation 3: Level D Scope is Extremely Ambitious — HIGH
**Issue:** The original Level D included: Security Hardening, Docker, CI/CD, Monitoring, Analytics, Marketplace, Enterprise SSO/RBAC, Performance Optimization, Scaling, Cloud Sync, Mobile App (React Native), Desktop Polish, PWA, Notifications, Charts, Collaboration, Billing, API Platform, SDK, Developer Platform, Community Extensions, Full Accessibility, and Full i18n — all in 90–120 days.

**Risk:** This is approximately 18–24 months of work for a typical engineering team, compressed into 3–4 months. Quality will suffer, or scope will be silently abandoned.

**Status:** **RESOLVED in v0.2.** Level D has been split into D1 (Platform Maturity, 60–90 days) and D2 (Ecosystem & Commercialization, 90–120 days). This is architecturally sound. However, D2 alone remains ambitious and may require further prioritization or timeline extension.

**Recommendation:**
- D1 is mandatory for production readiness. Approve D1 scope as-is.
- D2 should be treated as a commercial roadmap, not a single delivery phase. Consider quarterly milestones within D2.
- Mobile App and PWA moved to Level E (Future Expansion) per ratification. D2 scope is now focused and achievable.

#### Observation 4: Security Hardening Postponement Creates Liability Window — MEDIUM
**Issue:** Security hardening (OWASP Top 10, formal encryption, penetration testing) is scheduled for Level D1 (months 7–10). However, Levels A–C handle user files, terminal commands, browser automation, and API secrets.

**Risk:** If MOZA is used with real data during Levels B–C, the lack of formal security audit creates exposure.

**Status:** **MITIGATED in v0.2.** Section 12.5 now defines a Level A Security Baseline that addresses secret isolation, tool permission boundaries, file access restrictions, and dangerous action logging. This reduces the liability window but does not eliminate it.

**Recommendation:**
- Approve Level A Security Baseline as mandatory (not optional).
- Conduct a lightweight security review at the end of Level B, even if full hardening waits for D1.
- Document the liability window explicitly in user-facing documentation: *"MOZA is in beta. Do not use with sensitive data until D1 security certification."*

#### Observation 5: ResearchCase Elevation Path is Correctly Deferred — LOW
**Issue:** The task brief originally suggested the State Machine should "eventually manage ResearchCase lifecycle, not only chat sessions." The user's clarification correctly defers this.

**Assessment:** This is the right call. ResearchCase as a domain layer above Task/State is architecturally sound and avoids a premature core redesign. The migration path (Section 17.5) is appropriate.

**Recommendation:** Approve as written. Ensure the ResearchCase Manager in Level B is designed with future state machine integration in mind (e.g., use the same state enum values).

#### Observation 6: The "21 Capabilities" Are Not Fully Enumerated — LOW
**Issue:** The Execution Plan states "11/21 capabilities certified" but does not list the remaining 10. The Capability Inventory in Section 5.2 expands this to 64 capabilities, which may be more granular than intended.

**Risk:** Scope creep if every small feature becomes a tracked capability.

**Recommendation:**
- Ratify the exact list of 21 (or 64) capabilities before Level A begins.
- Group related capabilities (e.g., "Core Infrastructure" containing state machine, guards, registry) to avoid inflation.
- Use the 64-item inventory as a "Capability Backlog" and the 21-item list as "Certification Targets."

#### Observation 7: Self-Development Timeline Mismatch — MEDIUM
**Issue:** The Vision states MOZA must be self-development ready within 2 years if human development stops. However, the Evolution engine (required for self-development) is scheduled for Level C/D (months 4–9). If development stops at month 4, MOZA lacks the Evolution engine.

**Risk:** The 2-year contingency is overstated if the foundation for self-development isn't laid until month 4.

**Recommendation:**
- Ensure Level A includes robust **empty interfaces** for Evolution, Self-Modification, and Technology Discovery.
- Ensure Level B includes **telemetry collection** so MOZA has data to analyze when Evolution engine arrives.
- Consider the 2-year clock to start from Level D completion, not project start.

### 19.2 Summary Risk Matrix

| Risk | Severity | Likelihood | Mitigation Status |
|------|----------|------------|-------------------|
| Document divergence (SSOT conflict) | High | High | Requires ratification |
| Level A timeline slip | Medium | High | Recommend scope reduction or parallelization |
| Level D scope explosion | High | High | Recommend splitting into D1/D2 |
| Security liability window | Medium | Medium | Recommend baseline security in Level A |
| Capability inventory inflation | Low | Medium | Recommend ratification before coding |
| Self-development readiness | Medium | Low | Recommend telemetry in Level B |

---

## 20. Suggested Improvements Before Approval

Before this Master Plan is ratified as v1.0, the following actions are recommended:

1. **Ratify Document Hierarchy**
   - Add a preamble to Execution Plan v4.0 acknowledging this Master Plan as the governing architecture document.
   - Define the conflict resolution protocol explicitly.

2. **Reconcile Capability Count**
   - Decide: Is the target 21 capabilities or 64? If 21, group the 64 into 21 logical clusters. If 64, update all references to "21 capabilities."

3. **Revise Level D Timeline or Scope**
   - Either extend Level D to 180+ days or split into D1/D2.
   - Do not approve an unrealistic timeline — it will be ignored or lead to quality failure.

4. **Add Security Baseline to Level A**
   - Move `secrets_manager.py` and `audit_logger.py` to the first half of Level A.
   - Add a task: "Dependency audit and input sanitization baseline."

5. **Define ResearchCase v1.0 Schema**
   - Before Level B begins, ratify the exact ResearchCase YAML schema (Section 8.1).
   - Ensure it is compatible with the existing Session Manager event format.

6. **Approve Evolution Governance Section**
   - The self-development approval rules (Section 18.6) must be explicitly agreed upon by the project manager.
   - They cannot be enforced by architecture alone — they require organizational commitment.

7. **Schedule Quarterly Reconciliation**
   - Add to project calendar: Quarterly review of Master Plan vs. Execution Plan alignment.
   - First review scheduled for end of Level A.

8. **Create ADR-000: Ratification of Master Plan v0.1**
   - Formally document the decision to adopt this plan as the architectural constitution.
   - Include all 5 special sections (ResearchCase, Evidence, Browser, Reporting, CAT) in the ADR scope.

---

## Appendices

### Appendix A: Glossary

- **Capability:** A real-world skill MOZA can perform, certified by a Canonical Benchmark.
- **Canonical Benchmark:** A frozen, versioned, YAML-driven E2E test that proves a capability.
- **Capability Acceptance Test (CAT):** The minimum test suite that proves a capability works in realistic scenarios.
- **Confidence Score:** 0.0–1.0 measure of system certainty in a decision.
- **ResearchCase:** A structured, long-running investigation with evidence, sources, and report generation.
- **Risk Class:** L0–L4 classification of operation danger (read-only to destructive).
- **Regression Freeze:** Permanent lock on proven benchmarks; no future change may break them.
- **Memory Mesh:** Unified interface to 5 memory layers.
- **Reflection:** Micro (per-step) and Macro (per-task) analysis of execution quality.
- **Plugin:** A modular component that adds a capability to the system without modifying core.
- **Evolution Level:** A stable platform that enables the next level of functionality.
- **ADR:** Architecture Decision Record — immutable document of architectural choices.

### Appendix B: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1-DRAFT | 2026-07-28 | Chief Product Architect | Initial draft. All 17 sections + Evolution Governance + Architect Review. |
| 0.2-DRAFT | 2026-07-28 | Chief Product Architect | 9 critical adjustments applied: hierarchical capability inventory (Domains→Major→Atomic), Level D split into D1/D2, Level A timeline revised to 60–90 days with quality priority, Level A Security Baseline added, Human Authority Principle strengthened, Capability Preservation Matrix added, Human-in-the-Loop principle added, architectural history preservation enforced. |
| 1.0-RATIFIED | 2026-07-28 | Chief Product Architect | Final ratification. 5 pending items resolved: Capability Count approved (~22 Major), Mobile/PWA moved to Level E, Security Baseline approved, Human Authority Principle confirmed, Document Hierarchy established. Document locked as SSOT. |

### Appendix C: Approval Signatures

*This document requires the following approvals before becoming v1.0-RATIFIED:*

- [x] **Product Manager:** Vision, Non-Goals, and Capability Roadmap approved
- [x] **Lead Architect:** Architectural Principles, Target Architecture, and ADR Framework approved
- [x] **Security Lead:** Security Principles and liability window mitigation approved
- [x] **Engineering Manager:** Execution Roadmap timeline and resource allocation approved
- [x] **Project Manager:** Evolution Governance and self-development rules approved

---

*End of MOZA_MASTER_PLAN.md v0.1-DRAFT*
