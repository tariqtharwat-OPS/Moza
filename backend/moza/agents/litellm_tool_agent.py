import json
import re
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
    def _build_system_prompt(registry: ToolRegistry) -> str:
        lines = []
        for t in registry.get_all():
            params = "; ".join(
                f"{p.name}: {p.description} ({'req' if p.required else 'opt'})"
                for p in t.parameters
            )
            lines.append(f"- {t.name}: {t.description} | {params}")
        return (
            "You are MOZA, an AI operating system agent.\n\n"
            "Available tools:\n" + "\n".join(lines) + "\n\n"
            "STRICT RULE — Greetings & casual conversation: IF the user says hi, hello, hey, how are you,\n"
            "or any casual greeting / general question, you MUST respond directly with text.\n"
            "NEVER call any tool (filesystem, terminal, browser) for greetings or casual chat.\n"
            "Only use tools when the user explicitly asks for a task (e.g. 'create a file', 'search the web').\n\n"
            "DECIDE: Is this a simple conversational task (greeting, simple question, yes/no, general knowledge)?\n"
            "  YES - Respond directly. NO tools needed.\n"
            "  NO  - Use tools to accomplish the task. Call one tool at a time.\n"
            "After receiving tool results, decide the next step.\n"
            "When the task is complete, respond with a final summary."
        )

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

        messages: list[dict] = [
            {"role": "system", "content": self._build_system_prompt(registry)},
            {"role": "user", "content": task.description if task else "No task"},
        ]

        tools = self._build_tool_schema(registry)

        yield Event(
            session_id=sid, task_id=task_id,
            type=EventType.AGENT_THINKING,
            source="litellm_tool_agent",
            payload={"content": f"Task received. {len(tools)} tools available."},
        )

        steps_count = 0

        while steps_count < self._max_steps:
            context.cancellation_token.raise_if_cancelled()

            logger.info(f"[LiteLLMToolAgent] step {steps_count + 1}/{self._max_steps} — {len(messages)} messages")

            # ── Inject dynamic environment context before every LLM call ──
            env_context = await ContextBuilder.build_context(context)
            messages[0] = {
                "role": "system",
                "content": f"{self._build_system_prompt(registry)}\n\n{env_context}",
            }

            kwargs: dict = {
                "model": provider.model,
                "messages": messages,
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

                # Strip large binary blobs before feeding to LLM context
                _llm_result = result
                if isinstance(result, dict):
                    _meta = result.get("metadata", {})
                    if _meta.get("screenshot_base64"):
                        _meta = dict(_meta)
                        _meta.pop("screenshot_base64", None)
                        _llm_result = dict(result)
                        _llm_result["metadata"] = _meta
                        _llm_result["_screenshot_taken"] = True
                result_str = json.dumps(_llm_result) if isinstance(_llm_result, dict) else str(_llm_result)
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
