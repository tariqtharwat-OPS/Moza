"""
Golden Rules Guard Engine for MOZA AI OS.

Deterministic checks extracted from the agent's system prompt.
Runs BEFORE tool calls are executed to enforce golden rules.
"""

from dataclasses import dataclass
from typing import Any
import re


@dataclass
class GuardResult:
    """Result of a guard check."""
    passed: bool
    rule_name: str
    message: str = ""
    severity: str = "error"  # "error", "warning", "info"


@dataclass
class GoldenRulesConfig:
    """Configuration for golden rules."""
    # Greeting patterns that should NOT trigger tools
    greeting_patterns: list[str] = None
    # Phrases that indicate robotic completion (should not be used)
    completion_phrases: list[str] = None
    # Maximum file write content size
    max_write_size: int = 10_000_000  # 10MB
    # Require non-empty content for writes
    require_content: bool = True

    def __post_init__(self):
        if self.greeting_patterns is None:
            self.greeting_patterns = [
                r"^\s*(hi|hello|hey|howdy|greetings|how are you|what's up|sup)\b",
                r"^\s*(good morning|good afternoon|good evening)\b",
            ]
        if self.completion_phrases is None:
            self.completion_phrases = [
                "task started",
                "task completed",
                "task finished",
                "the task is done",
                "task complete",
                "task done",
            ]


def reset_guard_engine():
    """Reset the global guard engine (for testing)."""
    global _guard_engine
    _guard_engine = None


class GuardEngine:
    """
    Deterministic guard engine that validates LLM outputs against Golden Rules.
    
    Rules checked:
    1. No tools for greetings/casual chat
    2. Respect explicit tool requests
    3. Never drop/alter content on writes
    4. Ask clarifying questions for vague requests
    5. No robotic completion phrases
    6. Single tool call per step (enforced by agent loop)
    """

    def __init__(self, config: GoldenRulesConfig | None = None):
        self.config = config or GoldenRulesConfig()
        self._compiled_greetings = [re.compile(p, re.IGNORECASE) for p in self.config.greeting_patterns]

    def check_greeting_no_tools(self, user_message: str, tool_calls: list[dict]) -> GuardResult:
        """Rule 1: Greetings/casual chat must NOT call tools."""
        is_greeting = any(p.search(user_message) for p in self._compiled_greetings)
        
        if is_greeting and tool_calls:
            return GuardResult(
                passed=False,
                rule_name="greeting_no_tools",
                message=f"Greeting detected but {len(tool_calls)} tool call(s) present. Must respond directly without tools.",
                severity="error"
            )
        return GuardResult(
            passed=True,
            rule_name="greeting_no_tools",
            message="OK" if not is_greeting else "Greeting handled correctly (no tools)"
        )

    def check_explicit_tool_request(self, user_message: str, tool_calls: list[dict], available_tools: list[str]) -> GuardResult:
        """Rule 2: If user explicitly requests a tool, that tool MUST be used."""
        explicit_requests = []
        for tool in available_tools:
            patterns = [
                rf"\buse (?:the )?{tool}\b",
                rf"\bwith (?:the )?{tool}\b",
                rf"\bvia (?:the )?{tool}\b",
                rf"\b{tool} tool\b",
            ]
            for pattern in patterns:
                if re.search(pattern, user_message, re.IGNORECASE):
                    explicit_requests.append(tool)
                    break
        
        if explicit_requests and tool_calls:
            called_tools = [tc.get("name", "") for tc in tool_calls]
            for requested in explicit_requests:
                if requested not in called_tools:
                    return GuardResult(
                        passed=False,
                        rule_name="explicit_tool_request",
                        message=f"User explicitly requested '{requested}' but agent called {called_tools}. Must use requested tool.",
                        severity="error"
                    )
        return GuardResult(
            passed=True,
            rule_name="explicit_tool_request",
            message="OK"
        )

    def check_write_content_integrity(self, tool_calls: list[dict]) -> GuardResult:
        """Rule 3: Never drop or alter content on file writes."""
        for tc in tool_calls:
            if tc.get("name") == "filesystem" and tc.get("args", {}).get("action") == "write":
                content = tc.get("args", {}).get("content")
                if content is None:
                    return GuardResult(
                        passed=False,
                        rule_name="write_content_integrity",
                        message="filesystem write called with null content. Content must be provided (empty string OK).",
                        severity="error"
                    )
                if not self.config.require_content and content == "":
                    return GuardResult(
                        passed=True,
                        rule_name="write_content_integrity",
                        message="Empty write allowed"
                    )
                if self.config.require_content and content == "":
                    return GuardResult(
                        passed=False,
                        rule_name="write_content_integrity",
                        message="filesystem write called with empty content. Must provide actual content or use empty string explicitly.",
                        severity="warning"
                    )
                if len(content) > self.config.max_write_size:
                    return GuardResult(
                        passed=False,
                        rule_name="write_content_integrity",
                        message=f"Write content exceeds max size ({len(content)} > {self.config.max_write_size})",
                        severity="error"
                    )
        return GuardResult(
            passed=True,
            rule_name="write_content_integrity",
            message="OK"
        )

    def check_vague_request_clarification(self, user_message: str, tool_calls: list[dict]) -> GuardResult:
        """Rule 4: Vague/ambiguous requests should ask clarifying questions, not guess."""
        vague_patterns = [
            r"find me something interesting",
            r"do some research",
            r"look up.*",
            r"search for.*",
            r"tell me about.*",
            r"what.*about.*",
        ]
        
        is_vague = any(re.search(p, user_message, re.IGNORECASE) for p in vague_patterns)
        
        # Heuristic: if message is short and has no specific entity/task
        words = user_message.split()
        is_short = len(words) < 10
        has_specific = bool(re.search(r"\b(create|write|edit|delete|run|execute|search|find|get|list|show)\b", user_message, re.IGNORECASE))
        
        if is_vague and is_short and not has_specific and tool_calls:
            return GuardResult(
                passed=False,
                rule_name="vague_request_clarification",
                message=f"Vague request detected but {len(tool_calls)} tool call(s) made. Should ask clarifying questions first.",
                severity="warning"
            )
        return GuardResult(
            passed=True,
            rule_name="vague_request_clarification",
            message="OK"
        )

    def check_semantic_hallucination(self, required_tools: list[str], tool_calls: list[dict]) -> GuardResult:
        """Rule 6: If user's task semantically requires a tool, the response MUST include a tool_call."""
        if required_tools and not tool_calls:
            return GuardResult(
                passed=False,
                rule_name="semantic_hallucination",
                message=f"Task requires tool(s) {required_tools} but no tool_call was emitted. The LLM must use a tool to fulfill this request, not describe the action in text.",
                severity="error"
            )
        if required_tools and tool_calls:
            return GuardResult(
                passed=True,
                rule_name="semantic_hallucination",
                message=f"Task requires tool(s) {required_tools} and tool_call(s) are present"
            )
        return GuardResult(
            passed=True,
            rule_name="semantic_hallucination",
            message="No tools required for this task"
        )

    def check_no_robotic_completion(self, llm_response: str) -> GuardResult:
        """Rule 5: No robotic completion phrases in responses."""
        for phrase in self.config.completion_phrases:
            if phrase in llm_response.lower():
                return GuardResult(
                    passed=False,
                    rule_name="no_robotic_completion",
                    message=f"Robotic completion phrase detected: '{phrase}'. Use natural phrasing instead.",
                    severity="warning"
                )
        return GuardResult(
            passed=True,
            rule_name="no_robotic_completion",
            message="OK"
        )

    def check_all(self, user_message: str, tool_calls: list[dict], available_tools: list[str], llm_response: str = "", required_tools: list[str] | None = None) -> list[GuardResult]:
        """Run all guard checks and return results."""
        results = [
            self.check_greeting_no_tools(user_message, tool_calls),
            self.check_explicit_tool_request(user_message, tool_calls, available_tools),
            self.check_write_content_integrity(tool_calls),
            self.check_vague_request_clarification(user_message, tool_calls),
        ]
        if required_tools is not None:
            results.append(self.check_semantic_hallucination(required_tools, tool_calls))
        if llm_response:
            results.append(self.check_no_robotic_completion(llm_response))
        return results

    def any_failed(self, results: list[GuardResult]) -> bool:
        """Check if any guard check failed with error severity."""
        return any(not r.passed and r.severity == "error" for r in results)

    def get_failures(self, results: list[GuardResult]) -> list[GuardResult]:
        """Get all failed checks."""
        return [r for r in results if not r.passed]

    def validate_tool_call(self, user_message: str, tool_calls: list[dict], available_tools: list[str], assistant_content: str = "") -> list[GuardResult]:
        """Alias for check_all."""
        return self.check_all(user_message, tool_calls, available_tools, assistant_content)

    def should_block(self, results: list[GuardResult]) -> tuple[bool, str]:
        """Check if execution should be blocked and return reason."""
        if self.any_failed(results):
            failures = self.get_failures(results)
            reasons = [f"{f.rule_name}: {f.message}" for f in failures]
            return True, "; ".join(reasons)
        return False, ""


# Global singleton
_guard_engine: GuardEngine | None = None


def get_guard_engine(config: GoldenRulesConfig | None = None) -> GuardEngine:
    """Get or create the global GuardEngine instance."""
    global _guard_engine
    if _guard_engine is None:
        _guard_engine = GuardEngine(config)
    return _guard_engine