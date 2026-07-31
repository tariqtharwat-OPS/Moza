# ADR-000: Ratification of MOZA_MASTER_PLAN v1.0

## Status
**Accepted**

## Date
2026-07-28

## Context
MOZA has evolved from a component-based AI assistant into a capability-first AI Operating System. The project previously operated under MOZA_EXECUTION_PLAN.md v4.0 as its primary guidance document. However, the Execution Plan conflated architectural governance with implementation tasks, creating risk of scope drift, undocumented architectural decisions, and inconsistent execution standards.

A dedicated architectural constitution was required to:
- Separate governance (WHY/WHAT) from execution (HOW/WHEN)
- Establish immutable architectural principles
- Define capability certification standards
- Govern self-development and evolution safely
- Preserve backward compatibility as a first-class requirement

## Decision
Ratify `docs/MOZA_MASTER_PLAN.md` (v1.0-RATIFIED) as the **Single Source of Truth (SSOT)** for MOZA architectural governance.

Specifically:
1. The Master Plan governs all architectural principles, capability contracts, quality gates, and evolution governance.
2. The Execution Plan (MOZA_EXECUTION_PLAN.md) is subordinate to the Master Plan and governs implementation tasks only.
3. All conflicts between the two documents are resolved in favor of the Master Plan for architectural matters.
4. The Master Plan introduces a 3-tier capability hierarchy (Domains → Major Capabilities → Atomic Functions).
5. Level D is split into D1 (Platform Maturity) and D2 (Ecosystem & Commercialization).
6. Mobile App and PWA are deferred to Level E (Future Expansion).
7. Level A Security Baseline is mandatory before proceeding to Level B.
8. The Human Authority Principle is binding: MOZA may propose but never autonomously approve high-impact changes.
9. The Capability Preservation Matrix is a first-class quality gate.

## Consequences

### Positive
- Clear separation of concerns between governance and execution
- Immutable principles prevent architectural drift
- Capability certification ensures quality over speed
- Human Authority Principle prevents unsafe autonomous modifications
- Additive evolution policy protects existing investments

### Negative
- Additional documentation overhead (ADR process for architectural changes)
- Stricter approval gates may slow initial development velocity
- Capability Preservation Matrix requires more thorough impact analysis

### Neutral
- Execution Plan v4.0 content remains valid but is now subordinate
- All existing certified capabilities (11/22) remain frozen and protected
- 5 frozen regression benchmarks remain canonical

## Compliance
- [x] Backward compatibility addressed (additive evolution principle)
- [x] Migration plan included (Execution Plan archived with Governance Notice)
- [x] Interfaces documented (Master Plan Section 6)
- [x] Tests preserved (all frozen benchmarks remain)
- [x] Documentation updated (Master Plan + Execution Plan + this ADR)
- [x] Manager approval obtained

## Related Documents
- `docs/MOZA_MASTER_PLAN.md` — Architectural Constitution (SSOT)
- `docs/archive/MOZA_EXECUTION_PLAN_v4.md` — Archived implementation roadmap
- `MOZA_EXECUTION_PLAN.md` — Updated subordinate execution roadmap
- `PROJECT_STATE.md` — Current project state tracking
