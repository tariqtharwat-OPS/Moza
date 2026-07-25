import json
import re
from collections.abc import AsyncGenerator

from loguru import logger

from moza.agents.interfaces import AgentInterface
from moza.core.context import ExecutionContext
from moza.core.models import Event, EventType
from moza.tools.registry import ToolRegistry


_TYPE_MAP = {"string": "string", "enum": "string", "integer": "integer", "number": "number", "boolean": "boolean"}


class LiteLLMToolAgent(AgentInterface):
    def __init__(
        self,
        config,
        provider_name: str | None = None,
        max_steps: int = 15,
    ) -> None:
        self._config = config
        self._provider_name = provider_name
        self._max_steps = max_steps

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
            "Use tools to accomplish the task. Call one tool at a time.\n"
            "After receiving tool results, decide the next step.\n"
            "When the task is complete, respond with a final summary."
        )

    @property
    def _provider(self):
        return self._config.get_provider(self._provider_name)

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

        for step in range(1, self._max_steps + 1):
            context.cancellation_token.raise_if_cancelled()

            logger.info(f"[LiteLLMToolAgent] step {step}/{self._max_steps} — {len(messages)} messages")

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

            response = await litellm.acompletion(**kwargs)
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

            if not tool_calls:
                yield Event(
                    session_id=sid, task_id=task_id,
                    type=EventType.LLM_FINISHED,
                    source="litellm_tool_agent",
                    payload={"content": content},
                )
                return

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
                        "description": f"Step {step}: {fn_name}",
                        "requires_confirmation": False,
                    },
                )

                try:
                    result = await registry.execute_tool(fn_name, **fn_args)
                except KeyError as e:
                    result = {"success": False, "stderr": f"Unknown tool: {e}"}
                except Exception as e:
                    result = {"success": False, "stderr": str(e)}

                result_str = json.dumps(result) if isinstance(result, dict) else str(result)

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

        yield Event(
            session_id=sid, task_id=task_id,
            type=EventType.LLM_FINISHED,
            source="litellm_tool_agent",
            payload={"content": "Task completed (max steps reached)."},
        )
