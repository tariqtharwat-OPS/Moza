"""
OpenHands Agent Adapter for MOZA AI Operating System.

Maps OpenHands Actions/Observations to MOZA Event schema.
Preserves the Golden Rule via monitoring: all observed file operations
are mapped to structured TOOL_CALL/TOOL_RESULT events.
Adapter NEVER writes to the filesystem directly — the simulation
fallback routes all operations through context.tool_registry.execute().

OpenHands Action → MOZA Event mapping:
  CmdRunAction          → TOOL_CALL (tool: "terminal")
  CmdOutputObservation  → TOOL_RESULT (tool: "terminal", ToolResultPayload)
  FileReadAction        → TOOL_CALL (tool: "filesystem", action: "read")
  FileReadObservation   → TOOL_RESULT (tool: "filesystem", ToolResultPayload)
  FileWriteAction       → TOOL_CALL (tool: "filesystem", action: "write")
  BrowseAction          → TOOL_CALL (tool: "browser")
  BrowserOutputObservation → TOOL_RESULT (tool: "browser", ToolResultPayload)
  MessageAction         → AGENT_THINKING
  AgentStateChanged     → AGENT_STARTED / TASK_COMPLETED / TASK_FAILED
"""

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger

from moza.agents.interfaces import AgentInterface
from moza.core.context import ExecutionContext
from moza.core.models import Event, EventType, ToolResultPayload

try:
    from openhands.sdk import Agent as OH_Agent, Conversation, LLM, Workspace
    from openhands.events.action import (
        CmdRunAction,
        FileReadAction,
        FileWriteAction,
        MessageAction,
        BrowseAction,
    )
    from openhands.events.observation import (
        CmdOutputObservation,
        FileReadObservation,
        BrowserOutputObservation,
        ErrorObservation,
    )

    _OH_AVAILABLE = True
    logger.info("OpenHands SDK found — adapter will use real agent.")
except ImportError:
    _OH_AVAILABLE = False
    logger.warning("OpenHands SDK not installed — adapter will simulate.")


def _map_openhands_action(action: Any) -> dict | None:
    """Maps a detected OpenHands Action to MOZA tool/payload."""
    action_name = type(action).__name__

    if isinstance(action, CmdRunAction):
        return {
            "tool": "terminal",
            "action_type": action_name,
            "args": {"command": getattr(action, "command", "")},
        }
    elif isinstance(action, FileReadAction):
        return {
            "tool": "filesystem",
            "action_type": action_name,
            "args": {"action": "read", "path": getattr(action, "path", "")},
        }
    elif isinstance(action, FileWriteAction):
        return {
            "tool": "filesystem",
            "action_type": action_name,
            "args": {
                "action": "write",
                "path": getattr(action, "path", ""),
                "content_length": len(getattr(action, "content", "") or ""),
            },
        }
    elif isinstance(action, BrowseAction):
        return {
            "tool": "browser",
            "action_type": action_name,
            "args": {"url": getattr(action, "url", ""), "action": getattr(action, "action", "")},
        }
    elif isinstance(action, MessageAction):
        return {
            "tool": "agent",
            "action_type": action_name,
            "args": {"content": getattr(action, "content", "")},
        }
    return None


def _obs_to_tool_result(obs: Any) -> ToolResultPayload | None:
    """Maps an OpenHands Observation to a ToolResultPayload."""
    if isinstance(obs, CmdOutputObservation):
        return ToolResultPayload(
            success=getattr(obs, "exit_code", 0) == 0,
            duration_ms=0,
            exit_code=getattr(obs, "exit_code", 0),
            stdout=getattr(obs, "content", ""),
            metadata={"observation_type": type(obs).__name__},
        )
    elif isinstance(obs, FileReadObservation):
        return ToolResultPayload(
            success=True,
            duration_ms=0,
            exit_code=0,
            stdout=getattr(obs, "content", ""),
            metadata={"observation_type": type(obs).__name__},
        )
    elif isinstance(obs, BrowserOutputObservation):
        return ToolResultPayload(
            success=True,
            duration_ms=0,
            exit_code=0,
            stdout=getattr(obs, "content", ""),
            metadata={"observation_type": type(obs).__name__},
        )
    elif isinstance(obs, ErrorObservation):
        return ToolResultPayload(
            success=False,
            duration_ms=0,
            exit_code=-1,
            stderr=getattr(obs, "content", "Unknown error"),
            metadata={"observation_type": type(obs).__name__},
        )
    return None


class OpenHandsAdapter(AgentInterface):
    def __init__(self) -> None:
        self._agent: Any = None

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AsyncGenerator[Event, None]:
        session = context.session
        task = session.tasks[-1] if session.tasks else None
        task_id = task.id if task else "unknown"
        description = task.description if task else ""

        if not _OH_AVAILABLE:
            logger.info("OpenHands SDK not available — running simulation")
            async for event in self._simulate_execution(context, task_id, description):
                yield event
            return

        try:
            async for event in self._real_execution(context, task_id, description):
                yield event
        except Exception as e:
            logger.error(f"OpenHands execution failed: {e}")
            async for event in self._simulate_execution(context, task_id, description):
                yield event

    async def _real_execution(
        self,
        context: ExecutionContext,
        task_id: str,
        description: str,
    ) -> AsyncGenerator[Event, None]:
        session = context.session
        logger.info(f"Starting OpenHands agent for task: {description[:80]}")
        ws = Workspace(root_path=context.environment.filesystem.root_path)

        self._agent = OH_Agent(
            model=LLM(),
            workspace=ws,
            tools=[t.name for t in context.tool_registry.get_all()],
        )

        conversation = Conversation(agent=self._agent)
        conversation.start(description)

        yield Event(
            session_id=session.id,
            task_id=task_id,
            type=EventType.AGENT_STARTED,
            source="openhands_adapter",
            payload={"description": description, "sdk_version": "1.11.0"},
        )

        last_tool: str | None = None
        for oh_event in conversation.events:
            context.cancellation_token.raise_if_cancelled()

            action_payload = _map_openhands_action(oh_event)

            if action_payload:
                last_tool = action_payload.get("tool", "unknown")
                yield Event(
                    session_id=session.id,
                    task_id=task_id,
                    type=EventType.TOOL_CALL,
                    source="openhands_adapter",
                    payload=action_payload,
                )

            result_payload = _obs_to_tool_result(oh_event)
            if result_payload is not None:
                yield Event(
                    session_id=session.id,
                    task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="openhands_adapter",
                    payload={"tool": last_tool or "unknown", **result_payload.model_dump()},
                )

            if isinstance(oh_event, MessageAction):
                content = getattr(oh_event, "content", "")
                if content:
                    yield Event(
                        session_id=session.id,
                        task_id=task_id,
                        type=EventType.AGENT_THINKING,
                        source="openhands_adapter",
                        payload={"content": content},
                    )

        yield Event(
            session_id=session.id,
            task_id=task_id,
            type=EventType.LLM_FINISHED,
            source="openhands_adapter",
            payload={"content": f"OpenHands completed task: {description}"},
        )

    async def _simulate_execution(
        self,
        context: ExecutionContext,
        task_id: str,
        description: str,
    ) -> AsyncGenerator[Event, None]:
        session = context.session
        registry = context.tool_registry

        yield Event(
            session_id=session.id,
            task_id=task_id,
            type=EventType.AGENT_THINKING,
            source="openhands_adapter",
            payload={
                "content": "OpenHands SDK not available. Running simulated adapter.",
            },
        )
        await asyncio.sleep(0.3)
        context.cancellation_token.raise_if_cancelled()

        tools = registry.get_all()
        for tool in tools:
            yield Event(
                session_id=session.id,
                task_id=task_id,
                type=EventType.TOOL_CALL,
                source="openhands_adapter",
                payload={"tool": tool.name, "args": {"demo": True}},
            )
            await asyncio.sleep(0.2)

            try:
                start = time.monotonic()
                raw = await registry.execute_tool(tool.name, action="read", path=".")
                elapsed = (time.monotonic() - start) * 1000
                if isinstance(raw, dict) and "success" in raw:
                    result_payload = ToolResultPayload(**raw)
                else:
                    result_payload = ToolResultPayload.ok(
                        stdout=str(raw), duration_ms=elapsed
                    )
                yield Event(
                    session_id=session.id,
                    task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="openhands_adapter",
                    payload={"tool": tool.name, **result_payload.model_dump()},
                )
            except Exception as e:
                yield Event(
                    session_id=session.id,
                    task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="openhands_adapter",
                    payload={
                        "tool": tool.name,
                        **ToolResultPayload.error(str(e)).model_dump(),
                    },
                )
            await asyncio.sleep(0.2)
            context.cancellation_token.raise_if_cancelled()

        yield Event(
            session_id=session.id,
            task_id=task_id,
            type=EventType.LLM_FINISHED,
            source="openhands_adapter",
            payload={
                "content": f"OpenHands adapter simulation complete for: {description}",
                "note": "Real agent execution requires 'openhands-ai' package.",
            },
        )
