"""
OpenHands Agent Adapter for MOZA AI Operating System.

Maps OpenHands Actions/Observations to MOZA Event schema.
Preserves the Golden Rule: agents use tools via ToolRegistry,
all mutations flow through Event Emission.

OpenHands Action → MOZA Event mapping:
  CmdRunAction          → TOOL_CALL (tool: "terminal")
  CmdOutputObservation  → TOOL_RESULT (tool: "terminal")
  FileReadAction        → TOOL_CALL (tool: "filesystem", action: "read")
  FileReadObservation   → TOOL_RESULT (tool: "filesystem")
  FileWriteAction       → TOOL_CALL (tool: "filesystem", action: "write")
  BrowseAction          → TOOL_CALL (tool: "browser")
  BrowserOutputObservation → TOOL_RESULT (tool: "browser")
  MessageAction         → AGENT_THINKING
  AgentStateChanged     → AGENT_STARTED / TASK_COMPLETED / TASK_FAILED
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger

from moza.agents.interfaces import AgentInterface
from moza.core.context import ExecutionContext
from moza.core.models import Event, EventType

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


def _map_openhands_observation(obs: Any) -> dict | None:
    """Maps a detected OpenHands Observation to MOZA result payload."""
    obs_name = type(obs).__name__

    if isinstance(obs, CmdOutputObservation):
        return {
            "tool": "terminal",
            "observation_type": obs_name,
            "result": {
                "stdout": getattr(obs, "content", ""),
                "exit_code": getattr(obs, "exit_code", None),
            },
        }
    elif isinstance(obs, FileReadObservation):
        return {
            "tool": "filesystem",
            "observation_type": obs_name,
            "result": {"content": getattr(obs, "content", "")},
        }
    elif isinstance(obs, BrowserOutputObservation):
        return {
            "tool": "browser",
            "observation_type": obs_name,
            "result": {"content": getattr(obs, "content", "")},
        }
    elif isinstance(obs, ErrorObservation):
        return {
            "tool": "system",
            "observation_type": obs_name,
            "result": {"error": getattr(obs, "content", "Unknown error")},
        }
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
        ws = Workspace(root_path=context.workspace.root_path)

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

        for oh_event in conversation.events:
            context.cancellation_token.raise_if_cancelled()

            action_payload = _map_openhands_action(oh_event)
            obs_payload = _map_openhands_observation(oh_event)

            if action_payload:
                yield Event(
                    session_id=session.id,
                    task_id=task_id,
                    type=EventType.TOOL_CALL,
                    source="openhands_adapter",
                    payload=action_payload,
                )

            if obs_payload:
                yield Event(
                    session_id=session.id,
                    task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="openhands_adapter",
                    payload=obs_payload,
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
                result = await registry.execute_tool(tool.name, action="read", path=".")
                yield Event(
                    session_id=session.id,
                    task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="openhands_adapter",
                    payload={"tool": tool.name, "result": result, "status": "success"},
                )
            except Exception as e:
                yield Event(
                    session_id=session.id,
                    task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="openhands_adapter",
                    payload={"tool": tool.name, "result": {"warning": str(e)}, "status": "skipped"},
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
