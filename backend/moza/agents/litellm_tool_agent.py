import json
import os
import re
from typing import Any
from collections.abc import AsyncGenerator

from loguru import logger

from moza.agents.interfaces import AgentInterface
from moza.core.context import ExecutionContext
from moza.core.context_builder import ContextBuilder
from moza.core.models import Event, EventType
from moza.tools.registry import ToolRegistry


_TYPE_MAP = {"string": "string", "enum": "string", "integer": "integer", "number": "number", "boolean": "boolean"}


class LiteLLMToolAgent(AgentInterface):
    """
    ReAct (Reason + Act) agent powered by LiteLLM.
    
    The agent knows NOTHING about specific tools (Filesystem, Terminal, Browser, etc.).
    It operates solely through:
      - ToolRegistry  — to discover available tools and execute them
      - Events        — to stream structured progress to the EventBus
      - ExecutionContext — for session, cancellation, and environment data
    
    Loop: while steps_count < max_steps:
      1. Call LLM with system prompt + task + conversation + tool schemas
      2. If LLM returns tool_calls: execute each, append results, steps_count += 1
      3. If LLM returns final text (no tool_calls): emit COMPLETED, break
      4. If steps_count >= max_steps: emit FAILED (max_steps reached), break
    """

    def __init__(
        self,
        config,
        provider_name: str | None = None,
        max_steps: int = 15,
    ) -> None:
        self._config = config
        self._provider_name = provider_name
        self._max_steps = max_steps

    # ── tool schema construction ──────────────────────────────────────────

    @staticmethod
    def _build_tool_schema(registry: ToolRegistry) -> list[dict]:
        tools = []
        for tool in registry.get_all():
            properties = {}
            required = []
            for param in tool.parameters:
                js_type = _TYPE_MAP.get(param.type, "string")
                prop: dict = {"type": js_type, "description": param.description}

                m = re.search(r"One of:\s*(.+)", param.description)
                if m:
                    raw = m.group(1)
                    values = [v.strip() for v in re.split(r"\s*\|\s*", raw)]
                    prop["enum"] = values

                properties[param.name] = prop
                if param.required:
                    required.append(param.name)

            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                        "additionalProperties": False,
                    },
                },
            })
        return tools

    @staticmethod
    def _build_system_prompt(registry: ToolRegistry, cwd: str = "") -> str:
        lines = []
        for t in registry.get_all():
            params = "; ".join(
                f"{p.name}: {p.description} ({'req' if p.required else 'opt'})"
                for p in t.parameters
            )
            lines.append(f"- {t.name}: {t.description} | {params}")
        cwd_line = f"\nCurrent working directory: {cwd}\n" if cwd else ""
        return (
            "You are MOZA, an AI operating system agent.\n\n"
            "Available tools:\n" + "\n".join(lines) + "\n\n"
            f"{cwd_line}"
            "STRICT RULE — Greetings & casual conversation: IF the user says hi, hello, hey, how are you,\n"
            "or any casual greeting / general question, you MUST respond directly with text.\n"
            "NEVER call any tool (filesystem, terminal, browser) for greetings or casual chat.\n"
            "Only use tools when the user explicitly asks for a task (e.g. 'create a file', 'search the web').\n\n"
            "STRICT RULE — Respect explicit tool requests: IF the user explicitly requests a specific tool\n"
            "(e.g. 'use terminal', 'use browser'), you MUST use that tool.\n"
            "Do not default to a different tool if the user specified which one to use.\n\n"
            "STRICT RULE — Never drop or alter content: When writing to a file, you MUST pass the exact content\n"
            "requested by the user. NEVER send empty strings or placeholder spaces to bypass validation.\n"
            "If the content is empty, write an empty file — do not substitute spaces.\n\n"
            "CLARIFICATION RULE: If the user's request is vague, ambiguous, or lacking detail\n"
            "(e.g. 'find me something interesting' or 'do some research'), DO NOT guess.\n"
            "Instead, respond with clarifying questions to narrow down what they want.\n"
            "Only proceed with tool calls once the request is specific enough.\n\n"
            "DECIDE: Is this a simple conversational task (greeting, simple question, yes/no, general knowledge)?\n"
            "  YES - Respond directly. NO tools needed.\n"
            "  NO  - Is the request specific and detailed?\n"
            "    YES - Use tools to accomplish the task. Call one tool at a time.\n"
            "    NO  - Ask clarifying questions before using any tools.\n"
            "After receiving tool results, decide the next step.\n"
            "When the task is complete, respond with a final summary.\n\n"
            "CRITICAL RULE — Natural phrasing: NEVER output 'Task started', 'Task completed',\n"
            "'Task finished', or 'The task is done' as a conversational message.\n"
            "Instead, naturally state what you have accomplished.\n"
            "For example, instead of 'Task completed', say:\n"
            "  'I have successfully translated the file and saved it as ...'\n"
            "  'Here is what I found ...'\n"
            "  'I have created the file with the requested content. Would you like me to ...'\n"
            "Always end with a natural question or offer for follow-up assistance."
        )

    @staticmethod
    def _sanitize_tool_result(result: dict | Any) -> dict:
        """Remove binary/image fields that would trigger vision errors in non-vision LLMs."""
        if not isinstance(result, dict):
            return result

        cleaned = {}
        for k, v in result.items():
            if k in ("screenshot_base64", "image_data", "image", "base64"):
                continue
            if isinstance(v, str) and len(v) > 1000:
                # Check if the string looks like base64 image data
                if re.match(r'^[A-Za-z0-9+/=]{100,}$', v[:200]):
                    v = f"<{k}: {len(v)} bytes of binary data, omitted>"
            if isinstance(v, dict):
                v = LiteLLMToolAgent._sanitize_tool_result(v)
            elif isinstance(v, list):
                v = [LiteLLMToolAgent._sanitize_tool_result(i) if isinstance(i, dict) else i for i in v]
            cleaned[k] = v

        # Truncate oversized stdout/stderr to prevent token overflow
        for key in ("stdout", "stderr"):
            if key in cleaned and isinstance(cleaned[key], str) and len(cleaned[key]) > 10000:
                cleaned[key] = cleaned[key][:10000] + "\n... [output truncated]"
        return cleaned

    # ── message normalization ─────────────────────────────────────────────

    @staticmethod
    def _normalize_message(msg: dict) -> dict:
        """Ensure every message dict contains all fields expected by LiteLLM's serializer."""
        base = {
            "role": msg.get("role", "user"),
            "content": msg.get("content"),
            "name": msg.get("name"),
            "tool_calls": msg.get("tool_calls"),
            "tool_call_id": msg.get("tool_call_id"),
        }
        return {k: v for k, v in base.items() if v is not None}

    # ── provider resolution ───────────────────────────────────────────────

    @property
    def _provider(self):
        return self._config.get_provider(self._provider_name)

    # ── ReAct loop ────────────────────────────────────────────────────────

    async def execute(self, context: ExecutionContext) -> AsyncGenerator[Event, None]:
        import litellm

        task = context.session.tasks[-1] if context.session.tasks else None
        task_id = task.id if task else "unknown"
        sid = context.session.id
        registry = context.tool_registry
        provider = self._provider

        cwd = os.getcwd()

        # ── Reconstruct conversation history from previous tasks ─────
        prev_messages: list[dict] = []
        for event in context.session.execution_history:
            if task and event.task_id == task.id:
                continue  # skip current task's events
            if event.type == EventType.AGENT_STARTED:
                desc = event.payload.get("description", "")
                if desc:
                    prev_messages.append({"role": "user", "content": desc})
            elif event.type == EventType.LLM_FINISHED:
                content = event.payload.get("content", "")
                if content:
                    prev_messages.append({"role": "assistant", "content": content})

        messages: list[dict] = [
            {"role": "system", "content": self._build_system_prompt(registry, cwd=cwd)},
            *prev_messages,
            {"role": "user", "content": task.description if task else "No task"},
        ]

        tools = self._build_tool_schema(registry)

        yield Event(
            session_id=sid, task_id=task_id,
            type=EventType.AGENT_THINKING,
            source="litellm_tool_agent",
            payload={"content": "Processing your request..."},
        )

        steps_count = 0

        while steps_count < self._max_steps:
            context.cancellation_token.raise_if_cancelled()

            logger.info(f"[LiteLLMToolAgent] step {steps_count + 1}/{self._max_steps} — {len(messages)} messages")

            # ── Inject dynamic environment context before every LLM call ──
            env_context = await ContextBuilder.build_context(context)
            messages[0] = {
                "role": "system",
                "content": f"{self._build_system_prompt(registry, cwd=cwd)}\n\n{env_context}",
            }

            normalized_msgs = [self._normalize_message(m) for m in messages]
            kwargs: dict = {
                "model": provider.model,
                "messages": normalized_msgs,
                "tools": tools,
                "tool_choice": "auto",
                "parallel_tool_calls": False,
            }
            if provider.api_key:
                kwargs["api_key"] = provider.api_key
            if provider.base_url:
                kwargs["api_base"] = provider.base_url

            try:
                response = await litellm.acompletion(**kwargs)
            except Exception as e:
                err_msg = f"LLM API error: {e}"
                logger.warning(err_msg)
                messages.append({"role": "system", "content": err_msg + " Please retry."})
                steps_count += 1
                yield Event(
                    session_id=sid, task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="litellm_tool_agent",
                    payload={"tool": "_llm", "success": False, "stderr": err_msg},
                )
                continue
            choice = response.choices[0]
            msg = choice.message

            content = msg.content or ""

            if content:
                yield Event(
                    session_id=sid, task_id=task_id,
                    type=EventType.LLM_TOKEN,
                    source="litellm_tool_agent",
                    payload={"content": content},
                )

            tool_calls = getattr(msg, "tool_calls", None) or []

            # ── No tool calls → task is complete ──────────────────────────
            if not tool_calls:
                yield Event(
                    session_id=sid, task_id=task_id,
                    type=EventType.LLM_FINISHED,
                    source="litellm_tool_agent",
                    payload={"content": content},
                )
                yield Event(
                    session_id=sid, task_id=task_id,
                    type=EventType.TASK_COMPLETED,
                    source="litellm_tool_agent",
                    payload={"task_id": task_id},
                )
                return

            # ── Tool calls present → execute them ─────────────────────────
            assistant_msg: dict = {"role": "assistant", "content": msg.content}
            tc_list = []
            for tc in tool_calls:
                tc_list.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                })
            assistant_msg["tool_calls"] = tc_list
            messages.append(assistant_msg)

            for tc in tool_calls:
                context.cancellation_token.raise_if_cancelled()

                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON args for {fn_name}: {tc.function.arguments}")
                    fn_args = {}

                logger.info(f"[LiteLLMToolAgent] tool_call: {fn_name}({fn_args})")

                yield Event(
                    session_id=sid, task_id=task_id,
                    type=EventType.TOOL_CALL,
                    source="litellm_tool_agent",
                    payload={
                        "tool": fn_name,
                        "args": fn_args,
                        "description": f"Step {steps_count + 1}: {fn_name}",
                        "requires_confirmation": False,
                    },
                )

                try:
                    result = await registry.execute_tool(fn_name, **fn_args)
                except KeyError as e:
                    result = {"success": False, "stderr": f"Unknown tool: {e}"}
                except Exception as e:
                    result = {"success": False, "stderr": str(e)}

                # Strip large/binary blobs before feeding to LLM context
                _llm_result = self._sanitize_tool_result(result)
                result_str = json.dumps(_llm_result) if isinstance(_llm_result, dict) else str(_llm_result)
                if len(result_str) > 50000:
                    result_str = result_str[:50000] + "\n... [truncated]"
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_str})

                payload: dict = {"tool": fn_name}
                if isinstance(result, dict):
                    payload.update(result)
                else:
                    payload["stdout"] = str(result)

                logger.info(f"[LiteLLMToolAgent] tool_result: {fn_name} success={payload.get('success', '?')}")

                yield Event(
                    session_id=sid, task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="litellm_tool_agent",
                    payload=payload,
                )

            steps_count += 1

        # ── Max steps reached without task completion ─────────────────────
        logger.warning(f"[LiteLLMToolAgent] max_steps ({self._max_steps}) reached — terminating")
        yield Event(
            session_id=sid, task_id=task_id,
            type=EventType.LLM_FINISHED,
            source="litellm_tool_agent",
            payload={"content": "Task exceeded maximum steps."},
        )
        yield Event(
            session_id=sid, task_id=task_id,
            type=EventType.TASK_FAILED,
            source="litellm_tool_agent",
            payload={"error": "max_steps reached", "task_id": task_id},
        )
