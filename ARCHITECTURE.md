# MOZA Architecture Decision Records

> Architectural decisions are documented as ADRs (Architecture Decision Records).
> Each ADR captures a significant architectural decision, its context, alternatives, and consequences.

---

## ADR-003: Capability Contracts over Test Suites

### Status
Accepted (Phase 4.1 — 2026-07-26)

### Context
The project previously used "test count" as the primary quality metric (94 tests, 81 unit + 13 intent classifier). However, counting tests does not measure real-world capability. A capability might have many unit tests but still fail in production. Conversely, a capability might have few tests but be thoroughly proven by a single canonical benchmark.

The shift to "capability certification" required a formal model for defining what a capability is, what it must do, what it must NOT do, and how we prove it works.

### Decision
Use **Capability Contracts** instead of test suites as the primary definition of a capability.

A Capability Contract is a structured markdown document that defines:
- **Purpose** — Why the capability exists
- **User Story** — Who needs it and their goal
- **Inputs / Outputs** — What goes in and what comes out
- **Forbidden Behaviors** — What the capability must NEVER do
- **Definition of Done** — Production-ready criteria (the certification gate)
- **Evidence Requirements** — What proves it works
- **Maturity Level** — Readiness score (Level 0-5)
- **Confidence Score** — Reliability estimate (0-100%)
- **Dependencies** — What it relies on
- **Capability History** — Change log

### Capability-First Philosophy
1. **Design the contract first** — Before any code, define the capability contract based on real user needs
2. **Not framework first** — The base class (`Capability` ABC) is minimal: only 3 abstract methods. No full framework. Future capabilities extend this based on real needs, not theoretical architecture.
3. **Forbidden behaviors are first-class citizens** — What a capability must NOT do is as important as what it must do. Negative assertions are tested explicitly.
4. **Definition of Done is the gate** — A capability is "certified" only when ALL DoD criteria are met, including negative assertions.

### Consequences
- **Positive**: Clear, human-readable capability definitions. Test authors know exactly what to prove. Stakeholders can review contracts without reading code.
- **Positive**: Forbidden behaviors prevent regression (e.g., conversational inputs must NEVER trigger tool calls).
- **Positive**: Maturity Levels provide a shared vocabulary for readiness (e.g., "Level 4: Production Ready").
- **Neutral**: Requires discipline to write the contract before implementing.
- **Negative**: Contracts must be maintained as capabilities evolve.

### Comparison with Previous Approach

| Aspect | Test Suite Approach | Capability Contract Approach |
|--------|-------------------|------------------------------|
| Primary metric | Test count | Certified capabilities |
| What it defines | What the code does | What the user needs |
| Forbidden behaviors | Implicit (not tested) | Explicit (tested as negative assertions) |
| Readability | Code only | Human-readable markdown |
| Change impact | Update tests | Update contract + re-certify |
| Stakeholder review | Requires code literacy | Markdown is accessible |

### Relationship to Test Strategy
Capability Contracts do NOT replace tests. They supplement tests by providing:
- A higher-level definition of what a capability means
- The certification criteria that tests must prove
- The maturity model for tracking progress
- The forbidden behaviors that tests must verify are never violated

### Files
- Capability Contract: `backend/moza/certification/capabilities/conversation_contract.md`
- Base Class: `backend/moza/certification/capability_base.py`
- Test Strategy: `TEST_STRATEGY.md` (Section 4: Capability Certification Model)
- Project State: `PROJECT_STATE.md` (Phase 4.1)
