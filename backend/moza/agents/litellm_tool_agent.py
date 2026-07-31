import json
import os
import re
from typing import Any
from collections.abc import AsyncGenerator

from loguru import logger

from moza.agents.interfaces import AgentInterface
from moza.core.context import ExecutionContext
from moza.core.context_builder import ContextBuilder
from moza.core.guards import get_guard_engine
from moza.core.models import Event, EventType
from moza.gateway.router import LLMRouter, NormalizedResponse, normalize_litellm_tool_call
from moza.tools.registry import ToolRegistry


_TYPE_MAP = {"string": "string", "enum": "string", "integer": "integer", "number": "number", "boolean": "boolean"}


class LiteLLMToolAgent(AgentInterface):
    """
    ReAct (Reason + Act) agent powered by LiteLLM.
    """

    def __init__(
        self,
        config,
        provider_name: str | None = None,
        max_steps: int = 30,
        browser_mode: bool = False,
    ) -> None:
        self._config = config
        self._provider_name = provider_name
        self._max_steps = max_steps
        self._browser_mode = browser_mode
        self._router = LLMRouter(config) if config else None
        self._force_tool_choice: str | None = None
        self._hallucination_count: int = 0

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
            "Always end with a natural question or offer for follow-up assistance.\n\n"
            "CRITICAL RULE — NEVER simulate tool execution in text: You MUST NEVER describe\n"
            "tool usage in your conversational text response. Do not write phrases like\n"
            "'Using browser tool:', 'Using filesystem tool:', 'I have saved the file',\n"
            "'I am searching the web', 'Let me navigate to', or 'I will create a file'.\n"
            "If an action requires a tool, you MUST emit a valid tool_call payload.\n"
            "If you do not emit a tool_call, the tool action DID NOT happen.\n"
            "The ONLY way to execute a tool is through a structured function call.\n\n"
            "When you need to use a tool, your response MUST contain ONLY a single\n"
            "<function_call> tag wrapping a Python dict literal with single-quoted keys.\n"
            "Example: <function_call>{'name': 'filesystem', 'arguments': {'action': 'write', 'path': 'D:\\\\path\\\\to\\\\file.txt', 'content': 'Hello World'}}</function_call>\n"
            "The 'name' field must match an available tool name exactly.\n"
            "The 'arguments' field must be a dict with the required parameters for that tool.\n"
            "Do NOT wrap in markdown code blocks. Do NOT include any other text before or after the tag.\n"
            "After the tool executes and returns a result, you may respond conversationally.\n\n"
            "CRITICAL RULE — Never fabricate data: If you need to look up information on\n"
            "the web, use the browser tool. Do not make up company names, URLs, or data.\n"
            "If the browser tool returns no results, report that honestly.\n"
            "If you need to save a file, use the filesystem tool — do not claim a file\n"
            "was saved without actually calling the tool.\n\n"
            "CRITICAL RULE — Modern UI Design: When generating HTML/CSS for UI components, reports,\n"
            "or any visual output, you MUST use a modern 'Glassmorphism' or 'Neon Dark Mode' design\n"
            "by default. Include a <style> block with: background: linear-gradient(135deg, #0f172a, #1e1b4b);\n"
            "backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.1);\n"
            "and border-radius: 24px;."
        )

    @staticmethod
    def _sanitize_tool_result(result: dict | Any) -> dict:
        if not isinstance(result, dict):
            return result
        cleaned = {}
        for k, v in result.items():
            if k in ("screenshot_base64", "screenshot_path", "image_data", "image", "base64", "png"):
                continue
            if "screenshot" in k.lower() or "image" in k.lower() or "png" in k.lower() or "base64" in k.lower():
                continue
            if isinstance(v, str) and len(v) > 1000:
                if re.match(r'^[A-Za-z0-9+/=]{100,}$', v[:200]):
                    v = f"<{k}: {len(v)} bytes of binary data, omitted>"
            if isinstance(v, dict):
                v = LiteLLMToolAgent._sanitize_tool_result(v)
            elif isinstance(v, list):
                v = [LiteLLMToolAgent._sanitize_tool_result(i) if isinstance(i, dict) else i for i in v]
            cleaned[k] = v
        for key in ("stdout", "stderr"):
            if key in cleaned and isinstance(cleaned[key], str) and len(cleaned[key]) > 10000:
                cleaned[key] = cleaned[key][:10000] + "\n... [output truncated]"
        return cleaned

    # ── message normalization ─────────────────────────────────────────────

    @staticmethod
    def _normalize_message(msg: dict) -> dict:
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
    
    @staticmethod
    def _parse_text_tool_calls(content: str, available_tools: list) -> list[dict]:
        """Extract tool call descriptions from LLM text response."""
        import uuid
        import ast

        lowered = content.lower()

        # Strategy 1: <function_call>...</function_call> XML tag
        m = re.search(r'<function_call>(.*?)</function_call>', content, re.DOTALL)
        if m:
            inner = m.group(1).strip()
            data = None
            try:
                data = ast.literal_eval(inner)
            except (ValueError, SyntaxError, MemoryError):
                pass
            if not data:
                try:
                    data = json.loads(inner.replace("'", '"'))
                except json.JSONDecodeError:
                    pass
            if isinstance(data, dict):
                fn_name = data.get("name", "")
                fn_args = data.get("arguments", {})
                if isinstance(fn_args, str):
                    try:
                        fn_args = json.loads(fn_args)
                    except (json.JSONDecodeError, ValueError):
                        try:
                            fn_args = ast.literal_eval(fn_args)
                        except (ValueError, SyntaxError, MemoryError):
                            fn_args = {}
                if not isinstance(fn_args, dict):
                    fn_args = {}
                if fn_name:
                    for t in available_tools:
                        if t.name == fn_name:
                            missing = [p.name for p in t.parameters if p.required and p.name not in fn_args]
                            if missing:
                                logger.warning(f"Strategy 1 — missing required params for '{fn_name}': {missing}")
                                return []
                            return [{
                                "id": f"call_{uuid.uuid4().hex[:12]}",
                                "type": "function",
                                "function": {
                                    "name": fn_name,
                                    "arguments": json.dumps(fn_args),
                                },
                            }]

        # Strategy 2: JSON code blocks ```json ... ```
        for m in re.finditer(r'```(?:json)?\s*\n?(.*?)```', content, re.DOTALL):
            inner = m.group(1).strip()
            data = None
            try:
                data = json.loads(inner)
            except json.JSONDecodeError:
                try:
                    data = ast.literal_eval(inner.replace("'", '"'))
                except (ValueError, SyntaxError, MemoryError):
                    continue
            if not isinstance(data, dict):
                continue
            fn_name = data.get("name", "") or data.get("tool", "")
            fn_args = data.get("arguments", {}) or {k: v for k, v in data.items() if k != "tool" and k != "name"}
            if not fn_name:
                fn_data = data.get("function", {})
                fn_name = fn_data.get("name", "")
                fn_args = fn_data.get("arguments", {})
            if not fn_name:
                tc_list = data.get("tool_calls", [])
                if tc_list:
                    tc = tc_list[0]
                    fn_name = tc.get("recipient_name", "") or tc.get("name", "")
                    fn_args = tc.get("parameters", {}) or tc.get("arguments", {})
            if isinstance(fn_args, str):
                try:
                    fn_args = json.loads(fn_args)
                except json.JSONDecodeError:
                    try:
                        fn_args = ast.literal_eval(fn_args)
                    except (ValueError, SyntaxError, MemoryError):
                        fn_args = {}
            if not isinstance(fn_args, dict):
                fn_args = {}
            if fn_name:
                for t in available_tools:
                    if t.name == fn_name:
                        missing = [p.name for p in t.parameters if p.required and p.name not in fn_args]
                        if missing:
                            logger.warning(f"Strategy 2 — missing required params for '{fn_name}': {missing}")
                            return []
                        return [{
                            "id": f"call_{uuid.uuid4().hex[:12]}",
                            "type": "function",
                            "function": {
                                "name": fn_name,
                                "arguments": json.dumps(fn_args),
                            },
                        }]

        # Strategy 3: Inline JSON with tool-related keys
        for m in re.finditer(r'\{', content):
            depth = 0
            in_str = False
            escape = False
            start = m.start()
            for i in range(start, len(content)):
                ch = content[i]
                if escape:
                    escape = False; continue
                if ch == '\\' and in_str:
                    escape = True; continue
                if ch == '"' or ch == "'":
                    in_str = not in_str; continue
                if in_str: continue
                if ch == '{': depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = content[start:i+1]
                        if len(candidate) < 20:
                            break
                        # Check for tool-related keys
                        low = candidate.lower()
                        if any(k in low for k in ['"name"', "'name'", '"tool"', "'tool'", '"function"', '"arguments"']):
                            data = None
                            try:
                                data = json.loads(candidate)
                            except json.JSONDecodeError:
                                try:
                                    data = json.loads(candidate.replace("'", '"'))
                                except json.JSONDecodeError:
                                    try:
                                        data = ast.literal_eval(candidate)
                                    except (ValueError, SyntaxError, MemoryError):
                                        continue
                            if isinstance(data, dict):
                                fn_name = data.get("name", "") or data.get("tool", "")
                                if not fn_name:
                                    fn_data = data.get("function", {})
                                    fn_name = fn_data.get("name", "")
                                    fn_args = fn_data.get("arguments", {})
                                    if fn_name:
                                        if isinstance(fn_args, str):
                                            try:
                                                fn_args = json.loads(fn_args)
                                            except (json.JSONDecodeError, ValueError):
                                                try:
                                                    fn_args = ast.literal_eval(fn_args)
                                                except (ValueError, SyntaxError, MemoryError):
                                                    fn_args = {}
                                        if not isinstance(fn_args, dict):
                                            fn_args = {}
                                        for t in available_tools:
                                            if t.name == fn_name:
                                                missing = [p.name for p in t.parameters if p.required and p.name not in fn_args]
                                                if missing:
                                                    logger.warning(f"Strategy 3 — missing required params for '{fn_name}': {missing}")
                                                    return []
                                                return [{"id": f"call_{uuid.uuid4().hex[:12]}", "type": "function", "function": {"name": fn_name, "arguments": json.dumps(fn_args)}}]
                        break

        # Strategy 4: Tool-specific keyword extraction
        tool_keywords = {
            "filesystem": ["write file", "create file", "save file", "write to"],
            "browser": ["navigate to", "search for", "go to", "browser"],
            "terminal": ["run ", "execute ", "terminal command"],
        }
        for tool_name, triggers in tool_keywords.items():
            for trigger in triggers:
                if trigger in lowered:
                    matching = [t for t in available_tools if t.name == tool_name]
                    if matching:
                        args = {}
                        if tool_name == "filesystem":
                            args["action"] = "write"
                            pm = re.search(r'(?:to|in|at|:)\s*([A-Za-z]:\\[^\s"\']+)', content)
                            if pm:
                                args["path"] = pm.group(1).strip()
                            else:
                                args["path"] = ""
                            args["content"] = content
                        elif tool_name == "browser":
                            url_m = re.search(r'https?://[^\s"\']+', content)
                            if url_m:
                                args["url"] = url_m.group(0)
                                args["action"] = "navigate"
                            else:
                                args["action"] = "extract_text"
                        elif tool_name == "terminal":
                            cmd_m = re.search(r'`([^`]+)`', content)
                            if cmd_m:
                                args["command"] = cmd_m.group(1)
                            else:
                                args["command"] = ""
                        # Validate required params
                        tool_obj = matching[0]
                        missing = [p.name for p in tool_obj.parameters if p.required and p.name not in args]
                        if missing:
                            logger.warning(f"Strategy 4 — missing required params for '{tool_name}': {missing}")
                            continue
                        return [{"id": f"call_{uuid.uuid4().hex[:12]}", "type": "function", "function": {"name": tool_name, "arguments": json.dumps(args)}}]

        return []

    @staticmethod
    def _semantic_requires_tool(
        task_description: str,
        available_tools: list,
    ) -> list[str]:
        lowered = task_description.lower()
        required = []
        action_map: dict[str, list[str]] = {
            "browser": [
                "search", "browse", "navigate", "website", "web", "url",
                "http", "look up", "find", "research", "google", "internet",
                "scrape", "extract", "page", "site", "online",
            ],
            "filesystem": [
                "write", "save", "create", "file", "folder", "directory",
                "document", "html", "xlsx", "pdf", "txt", "csv", "json",
                "read", "open", "load", "path",
            ],
            "terminal": [
                "run", "execute", "command", "terminal", "shell", "script",
                "install", "pip", "npm", "git", "compile", "build",
            ],
        }
        for tool_name, keywords in action_map.items():
            if any(kw in lowered for kw in keywords):
                for t in available_tools:
                    if t.name == tool_name:
                        required.append(tool_name)
                        break
        return required

    def _get_provider_rank(self, provider_name: str, model_name: str) -> int:
        try:
            from moza_orchestrator import RANKING_CONFIG
            for entry in RANKING_CONFIG["ranking"]:
                if entry["provider"] == provider_name and entry["model"] == model_name:
                    return entry["rank"]
            return 999
        except ImportError:
            return 1

    # ── ReAct loop ────────────────────────────────────────────────────────

    async def execute(self, context: ExecutionContext) -> AsyncGenerator[Event, None]:
        self._hallucination_count = 0
        task = context.session.tasks[-1] if context.session.tasks else None
        task_id = task.id if task else "unknown"
        sid = context.session.id
        registry = context.tool_registry

        cwd = os.getcwd()

        prev_messages: list[dict] = []
        for event in context.session.execution_history:
            if task and event.task_id == task.id:
                continue
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
        if tools:
            self._force_tool_choice = "required"

        yield Event(
            session_id=sid, task_id=task_id,
            type=EventType.AGENT_THINKING,
            source="litellm_tool_agent",
            payload={"content": "Processing your request..."},
        )

        steps_count = 0

        while steps_count < self._max_steps:
            response = None
            context.cancellation_token.raise_if_cancelled()

            logger.info(f"[LiteLLMToolAgent] step {steps_count + 1}/{self._max_steps} — {len(messages)} messages")

            env_context = await ContextBuilder.build_context(context)
            messages[0] = {
                "role": "system",
                "content": f"{self._build_system_prompt(registry, cwd=cwd)}\n\n{env_context}",
            }

            normalized_msgs = [self._normalize_message(m) for m in messages]
            try:
                if self._router:
                    result: NormalizedResponse = await self._router.route(
                        messages=normalized_msgs,
                        tools=tools,
                        browser_mode=self._browser_mode,
                        tool_choice=self._force_tool_choice,
                    )
                    self._force_tool_choice = None
                    provider_name = result.provider
                    model_name = result.model
                    logger.info(f"[LiteLLMToolAgent] using provider: {provider_name}/{model_name}")
                    
                    yield Event(
                        session_id=sid, task_id=task_id,
                        type=EventType.AGENT_THINKING,
                        source="litellm_tool_agent",
                        payload={
                            "content": "Processing your request...",
                            "provider": provider_name,
                            "model": model_name,
                            "rank": self._get_provider_rank(provider_name, model_name)
                        },
                    )
                else:
                    import litellm
                    kwargs: dict = {
                        "model": self._provider.model,
                        "messages": normalized_msgs,
                        "tools": tools,
                        "tool_choice": self._force_tool_choice or "auto",
                        "parallel_tool_calls": False,
                    }
                    self._force_tool_choice = None
                    if self._provider.api_key:
                        kwargs["api_key"] = self._provider.api_key
                    if self._provider.base_url:
                        kwargs["api_base"] = self._provider.base_url
                    if self._provider.base_url and "groq" in self._provider.base_url:
                        kwargs["custom_llm_provider"] = "groq"
                    _saved_openai_key = os.environ.pop("OPENAI_API_KEY", None)
                    try:
                        raw = await litellm.acompletion(**kwargs)
                    finally:
                        if _saved_openai_key is not None:
                            os.environ["OPENAI_API_KEY"] = _saved_openai_key
                    choice = raw.choices[0]
                    msg = choice.message
                    result = NormalizedResponse(
                        content=msg.content or "",
                        tool_calls=[normalize_litellm_tool_call(tc) for tc in (msg.tool_calls or [])],
                        provider=self._provider.model or "unknown",
                        model=self._provider.model,
                        usage={"total_tokens": choice.usage.total_tokens if hasattr(choice, "usage") and choice.usage else 0},
                    )
                    provider_name = result.provider
                    model_name = result.model
            except Exception as e:
                err_msg = f"LLM API error: {e}"
                logger.warning(err_msg)
                # If all providers are exhausted, fail immediately
                if "All providers exhausted" in str(e):
                    logger.error(f"[LiteLLMToolAgent] All providers exhausted — terminating")
                    yield Event(
                        session_id=sid, task_id=task_id,
                        type=EventType.TASK_FAILED,
                        source="litellm_tool_agent",
                        payload={"error": "All providers exhausted", "task_id": task_id},
                    )
                    return
                messages.append({"role": "system", "content": err_msg + " Please retry."})
                steps_count += 1
                yield Event(
                    session_id=sid, task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="litellm_tool_agent",
                    payload={"tool": "_llm", "success": False, "stderr": err_msg},
                )
                continue

            content = result.content
            tool_calls = result.tool_calls

            # ── Text-to-Tool Parser ─────────────────────────────────────────
            if not tool_calls and content:
                try:
                    available_tools_list = registry.get_all()
                    parsed_calls = LiteLLMToolAgent._parse_text_tool_calls(
                        content, available_tools_list
                    )
                    if parsed_calls:
                        logger.info(
                            f"[LiteLLMToolAgent] text-to-tool: parsed {len(parsed_calls)} "
                            f"tool calls from text response"
                        )
                        tool_calls = parsed_calls
                except Exception as parse_err:
                    logger.warning(f"[LiteLLMToolAgent] text-to-tool parse error: {parse_err}")

            # ── Semantic Hallucination Guard ──────────────────────────────
            if not tool_calls and content:
                available_tools_list = registry.get_all()
                required_tools = LiteLLMToolAgent._semantic_requires_tool(
                    task.description if task else "", available_tools_list
                )
                if required_tools:
                    self._hallucination_count += 1
                    logger.warning(
                        f"[LiteLLMToolAgent] Semantic hallucination #{self._hallucination_count}: "
                        f"task requires {required_tools} but no tool_call emitted"
                    )
                    yield Event(
                        session_id=sid, task_id=task_id,
                        type=EventType.LLM_TOKEN,
                        source="litellm_tool_agent",
                        payload={"content": content},
                    )
                    if self._hallucination_count >= 3:
                        logger.warning(
                            f"[LiteLLMToolAgent] Max hallucination retries reached "
                            f"({self._hallucination_count}). Treating as conversational."
                        )
                        self._hallucination_count = 0
                        yield Event(
                            session_id=sid, task_id=task_id,
                            type=EventType.TOOL_RESULT,
                            source="guard_engine",
                            payload={
                                "tool": "semantic_hallucination",
                                "success": True,
                                "stdout": f"Proceeding with LLM response after {self._hallucination_count} hallucination retries.",
                            },
                        )
                    else:
                        yield Event(
                            session_id=sid, task_id=task_id,
                            type=EventType.TOOL_RESULT,
                            source="guard_engine",
                            payload={
                                "tool": "semantic_hallucination",
                                "success": False,
                                "stderr": (
                                    f"Semantic hallucination: task requires {required_tools} "
                                    f"but LLM responded without a tool_call. "
                                    f"Retry {self._hallucination_count}/3 with forced tool selection."
                                ),
                            },
                        )
                        hallucination_msg = (
                            f"You described the action in text but did not emit a tool_call. "
                            f"This task requires one of these tools: {', '.join(required_tools)}. "
                            f"You MUST select and use the appropriate tool. Do NOT describe or simulate the action."
                        )
                        messages.append({"role": "system", "content": hallucination_msg})
                        self._force_tool_choice = "required"
                        steps_count += 1
                        continue

            if content:
                yield Event(
                    session_id=sid, task_id=task_id,
                    type=EventType.LLM_TOKEN,
                    source="litellm_tool_agent",
                    payload={"content": content},
                )

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
            self._hallucination_count = 0
            assistant_msg: dict = {"role": "assistant", "content": content}
            tc_list = []
            for tc in tool_calls:
                tc_list.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["function"]["name"], "arguments": tc["function"]["arguments"]},
                })
            assistant_msg["tool_calls"] = tc_list
            messages.append(assistant_msg)

            # ── Golden Rules Guard Check ───────────────────────────────────
            guard_engine = get_guard_engine()
            tool_call_dicts = []
            for tc in tool_calls:
                try:
                    args = json.loads(tc["function"]["arguments"])
                except (json.JSONDecodeError, TypeError):
                    args = {}
                tool_call_dicts.append({
                    "name": tc["function"]["name"],
                    "arguments": args,
                })
            
            available_tools = [t.name for t in registry.get_all()]
            user_message = task.description if task else ""
            
            guard_results = guard_engine.check_all(
                user_message=user_message,
                tool_calls=tool_call_dicts,
                available_tools=available_tools,
                llm_response=content,
            )

            blocked = guard_engine.any_failed(guard_results)
            block_reason = "; ".join(
                f"{r.rule_name}: {r.message}"
                for r in guard_engine.get_failures(guard_results)
            )
            if blocked:
                logger.warning(f"[GuardEngine] Blocked tool execution: {block_reason}")
                yield Event(
                    session_id=sid, task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="guard_engine",
                    payload={
                        "tool": "guard_engine",
                        "success": False,
                        "stderr": f"Guard check failed: {block_reason}",
                        "exit_code": 1,
                    },
                )
                messages.append({"role": "tool", "tool_call_id": tool_calls[0]["id"], "content": f"Guard error: {block_reason}"})
                steps_count += 1
                continue

            for tc in tool_calls:
                context.cancellation_token.raise_if_cancelled()

                fn_name = tc["function"]["name"]
                try:
                    fn_args = json.loads(tc["function"]["arguments"])
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Invalid JSON args for {fn_name}: {tc['function']['arguments']}")
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

                _llm_result = self._sanitize_tool_result(result)
                result_str = json.dumps(_llm_result) if isinstance(_llm_result, dict) else str(_llm_result)
                if len(result_str) > 50000:
                    result_str = result_str[:50000] + "\n... [truncated]"
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result_str})

                # Early exit: primary goal achieved (file write success or browser search success)
                if fn_name == "filesystem" and isinstance(result, dict) and result.get("success") and fn_args.get("action") == "write":
                    logger.info(f"[LiteLLMToolAgent] early exit: file write succeeded for {fn_args.get('path')}")
                    yield Event(
                        session_id=sid, task_id=task_id,
                        type=EventType.TASK_COMPLETED,
                        source="litellm_tool_agent",
                        payload={"task_id": task_id, "reason": "primary_goal_achieved"},
                    )
                    return
                if fn_name == "browser" and isinstance(result, dict) and result.get("success") and fn_args.get("action") in ("search", "navigate"):
                    logger.info(f"[LiteLLMToolAgent] early exit: browser search completed")
                    yield Event(
                        session_id=sid, task_id=task_id,
                        type=EventType.TASK_COMPLETED,
                        source="litellm_tool_agent",
                        payload={"task_id": task_id, "reason": "primary_goal_achieved"},
                    )
                    return

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
