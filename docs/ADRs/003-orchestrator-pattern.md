# ADR 003: Orchestrator Pattern for Task Lifecycle Management

**Status:** Accepted  
**Date:** 2026-01  
**Author:** Principal Engineer Team

## Context

Initial Phase 1 implementation had API routes directly calling Agent execution. This caused:
- Tight coupling between HTTP layer and agent logic
- No centralized task lifecycle management
- Difficult to implement cancellation, pause/resume
- No single source of truth for running tasks
- Event routing scattered across codebase

## Decision

Introduce **Orchestrator Layer** between API and Agents.

```
API Route → TaskService → Orchestrator → Agent → EventBus
```

### Architecture

**TaskService** (thin facade):
- Entry point for API routes
- Validates requests, returns responses
- Delegates to Orchestrator

**Orchestrator** (central coordinator):
- Owns Session lifecycle
- Dispatches Tasks to Agents
- Routes Events from Agent to EventBus
- Manages task state (submit/cancel/resume)
- Tracks running tasks in `_running_tasks: dict[task_id, asyncio.Task]`

**Golden Rule (enforced in code):**
> Agents MUST NEVER write to the Workspace directly. All mutations MUST flow through:  
> **Agent → ToolRegistry → Tool Execution → Event Emission → Workspace Update**

## Consequences

### Positive
- **Decoupling**: API doesn't know about Agent internals
- **Centralized control**: Single place to manage task lifecycle
- **Cancellation support**: Can cancel running tasks via asyncio.Task
- **Event routing**: All events flow through one path
- **Testability**: Can mock Orchestrator for integration tests
- **Future extensibility**: Can add pause/resume, retry logic, distributed execution

### Negative
- **Additional layer**: More indirection, but justified by complexity management
- **Learning curve**: Engineers need to understand the data flow
- **Performance overhead**: Minimal (in-memory routing)

## Implementation

```python
# API Route
async def execute_task(request: TaskRequest):
    task_service = get_task_service()
    session = await task_service.submit_task(...)
    return EventSourceResponse(event_stream(session.id))

# TaskService
async def submit_task(self, session_id, task, workspace):
    await orchestrator.submit_task(session_id, task, workspace)

# Orchestrator
async def submit_task(self, session_id, task, workspace):
    agent = self.get_agent_for_task(task)
    await agent.execute(session, task, tool_registry, event_bus)
```

## Alternatives Considered

1. **Direct API → Agent** (rejected): Tight coupling, no lifecycle management
2. **Message Queue (Celery)** (rejected): Overkill for in-process orchestration
3. **Workflow Engine (Temporal)** (rejected): External dependency, complexity overhead

## Future Enhancements
- Distributed Orchestrator (Redis/Distributed Task Queue)
- Long-running task persistence (for session resumption across restarts)
- Priority queuing for concurrent tasks

## References
- [Orchestrator Pattern (Microsoft)](https://docs.microsoft.com/en-us/azure/architecture/patterns/orchestrator)
- [Saga Pattern for Distributed Transactions](https://microservices.io/patterns/data/saga.html)
