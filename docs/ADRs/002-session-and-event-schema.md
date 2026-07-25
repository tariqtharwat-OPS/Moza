# ADR 002: Session-Centric Domain Model with Strict Event Schema

**Status:** Accepted  
**Date:** 2026-01  
**Author:** Principal Engineer Team

## Context

Initial Phase 1 "Chat" model was too simplistic for production-grade AI OS requirements. We need:
- Multi-turn task execution, not just chat
- Full audit trail of agent decisions and tool usage
- Ability to replay/resume sessions
- Structured event streaming (not raw LLM tokens)
- Workspace state tracking across execution steps

## Decision

Model MOZA around **Sessions** as the root domain entity, with strict **Event** schema for all agent activities.

### Domain Model Structure

```
Session (root aggregate)
├── Workspace (project files, git state)
├── ExecutionHistory (ordered list of Events)
├── Artifacts (outputs: logs, diffs, reports)
└── Metadata (session-level context)
```

### Event Schema

```python
class Event(BaseModel):
    id: str
    timestamp: datetime
    session_id: str
    task_id: str | None
    type: EventType  # 12 strict enum values
    source: str      # "agent", "tool", "orchestrator", "user"
    payload: dict    # Event-specific data
```

**12 Event Types:**
1. `agent_started` - Agent begins execution
2. `agent_thinking` - Agent reasoning (chain-of-thought)
3. `tool_selected` - Agent chooses a tool
4. `tool_call` - Tool invoked with parameters
5. `tool_result` - Tool returns output
6. `browser_started` - Browser session initiated
7. `browser_action` - Browser action (click, navigate, etc.)
8. `terminal_output` - Terminal command output
9. `llm_token` - Streaming LLM token
10. `llm_finished` - LLM response complete
11. `task_completed` - Task finished successfully
12. `task_failed` - Task execution failed

## Consequences

### Positive
- **Full traceability**: Every agent decision recorded
- **Replayability**: Can reconstruct session from event stream
- **Structured streaming**: Frontend renders rich UI (thinking, tool calls, terminal output)
- **Golden Rule enforcement**: Mutations flow through ToolRegistry → Event emission
- **Event sourcing pattern**: Standard enterprise approach, well-understood by engineers

### Negative
- **Storage overhead**: Every interaction generates 3-10 events
- **Complexity**: More sophisticated than simple request/response
- **Migration path**: Existing Phase 1 code needs refactoring

## Implementation

- `backend/moza/core/models.py` - Domain models
- `backend/moza/core/event_bus.py` - In-memory Pub/Sub
- `backend/moza/orchestrator/` - Event routing and lifecycle

## References
- [Event Sourcing Pattern (Microsoft)](https://docs.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)
- [CQRS with Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
