"""
Plugin Interfaces for MOZA

These ABCs define the contracts that all plugins must implement.
They enable the plugin system to work with any capability, tool, or provider
without knowing the concrete implementation.

Design Principles:
- Every plugin type has a clear, minimal interface
- Interfaces are stable - once defined, they don't change
- Interfaces support both sync and async operations
- All plugins are discoverable and self-describing
"""

from abc import ABC, abstractmethod
from typing import Any
from collections.abc import AsyncGenerator


class CapabilityInterface(ABC):
    """
    Interface for all MOZA capabilities.
    
    A capability is a real-world skill MOZA can perform (e.g., Conversation,
    Filesystem operations, Browser navigation, Research, etc.).
    
    Every capability must implement this interface to be registered in the
    PluginRegistry and discovered by the system.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this capability (e.g., 'conversation', 'filesystem')."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version of this capability (e.g., '1.0.0')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this capability does."""
        pass

    @property
    @abstractmethod
    def author(self) -> str:
        """Author/owner of this capability."""
        pass

    @property
    def metadata(self) -> dict[str, Any]:
        """
        Optional metadata about the capability.
        
        Returns:
            dict with keys like 'maturity_level', 'confidence_score', 
            'dependencies', 'tags', etc.
        """
        return {}

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the capability with the given context.
        
        Args:
            context: Dictionary containing all information needed for execution
                   (e.g., session_id, task_id, user_input, environment, etc.)
        
        Returns:
            dict with execution results, including:
            - 'success': bool indicating if execution succeeded
            - 'output': the main result/output
            - 'events': list of Event objects to emit
            - Any other capability-specific data
        """
        pass

    @abstractmethod
    async def validate(self, context: dict[str, Any]) -> tuple[bool, str]:
        """
        Validate that the capability can execute with the given context.
        
        Args:
            context: Dictionary containing proposed execution context
        
        Returns:
            tuple of (is_valid: bool, error_message: str)
            - If valid: (True, "")
            - If invalid: (False, "reason for invalidity")
        """
        pass

    async def on_load(self) -> None:
        """Called when the capability is loaded into the registry."""
        pass

    async def on_unload(self) -> None:
        """Called when the capability is unloaded from the registry."""
        pass


class ToolInterface(ABC):
    """
    Interface for all MOZA tools.
    
    A tool is a specific action MOZA can perform (e.g., read_file, write_file,
    execute_command, navigate_to_url, click_element, etc.).
    
    Tools are the lowest-level executable units. They perform concrete actions
    and return structured results.
    
    Note: This interface is designed to be compatible with the existing BaseTool
    class in tools/registry.py. Existing tools can implement either BaseTool or
    from abc import ABC
from abc import abstractmethod
class ToolInterface(ABC):
    @abstractmethod
    def __init__(self):
        pass (or both via multiple inheritance).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this tool (e.g., 'filesystem', 'terminal')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this tool does."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version of this tool."""
        pass

    @property
    @abstractmethod
    def actions(self) -> list[str]:
        """
        List of actions this tool can perform.
        
        For simple tools with one action, this is typically [tool_name].
        For multi-action tools, this lists all available actions.
        
        Example: ['read', 'write', 'list', 'delete'] for filesystem tool
        """
        pass

    @property
    @abstractmethod
    def is_destructive(self) -> bool:
        """
        Whether this tool can cause data loss or system damage.
        
        Destructive tools (is_destructive=True) will require explicit
        user approval (L3/L4 risk class) before execution.
        """
        pass

    @abstractmethod
    async def execute(self, action: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a specific action with the given arguments.
        
        Args:
            action: The action to execute (must be in self.actions)
            args: Dictionary of arguments for the action
        
        Returns:
            dict with execution results, including:
            - 'success': bool indicating if execution succeeded
            - 'stdout': string output (if applicable)
            - 'stderr': string error output (if applicable)
            - 'exit_code': int exit code (if applicable)
            - 'artifacts': list of created/modified files
            - Any other action-specific data
        
        Raises:
            ValueError: If action is not in self.actions
            RuntimeError: If execution fails at the system level
        """
        pass

    @abstractmethod
    async def validate_action(
        self, action: str, args: dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Validate that an action can be executed with the given arguments.
        
        Args:
            action: The action to validate
            args: Dictionary of arguments to validate
        
        Returns:
            tuple of (is_valid: bool, error_message: str)
        """
        pass

    @property
    def requires_confirmation(self) -> bool:
        """
        Whether this tool requires explicit user confirmation before execution.
        
        Defaults to True for destructive tools, False otherwise.
        Can be overridden per-tool or per-action.
        """
        return self.is_destructive

    @property
    def capabilities(self) -> list[str]:
        """
        List of capability tags this tool provides.
        
        Used for capability-based discovery and gating.
        Example: ['filesystem:read', 'filesystem:write', 'filesystem:list']
        """
        return []

    async def on_load(self) -> None:
        """Called when the tool is loaded into the registry."""
        pass

    async def on_unload(self) -> None:
        """Called when the tool is unloaded from the registry."""
        pass

    async def cleanup(self) -> None:
        """
        Release resources held by this tool.
        
        Called by the Orchestrator when a task is cancelled or fails.
        Should clean up subprocesses, temp files, network connections, etc.
        """
        pass


class ProviderInterface(ABC):
    """
    Interface for all LLM providers.
    
    A provider is a service that can execute LLM inference (e.g., Groq, OpenRouter,
    Anthropic, OpenAI, Local/vLLM, LM Studio, etc.).
    
    Providers are responsible for:
    - Managing API keys and authentication
    - Executing chat completions
    - Executing embeddings (optional)
    - Reporting health status
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this provider (e.g., 'groq', 'openrouter')."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Default model name for this provider."""
        pass

    @property
    @abstractmethod
    def api_key(self) -> str | None:
        """API key for this provider, if required."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str | None:
        """Base URL for API calls, if not using default."""
        pass

    @property
    def supports_embeddings(self) -> bool:
        """Whether this provider supports embedding generation."""
        return False

    @property
    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming responses."""
        return True

    @abstractmethod
    async def chat(
        self, 
        messages: list[dict[str, Any]], 
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        Execute a chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional provider-specific arguments (tools, temperature, etc.)
        
        Returns:
            dict with completion results, including:
            - 'choices': list of completion choices
            - Each choice has 'message' with 'content' and optionally 'tool_calls'
            - 'usage': token usage information
            - Any other provider-specific data
        """
        pass

    async def achat(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Execute a streaming chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional provider-specific arguments
        
        Yields:
            dict with partial completion results (streaming chunks)
        
        Note: Default implementation falls back to non-streaming chat.
        Providers should override this for native streaming support.
        """
        # Default: execute non-streaming and yield the full result
        result = await self.chat(messages, **kwargs)
        yield result

    async def embed(self, text: str) -> list[float]:
        """
        Generate embeddings for the given text.
        
        Args:
            text: Text to embed
        
        Returns:
            list of float values representing the embedding vector
        
        Raises:
            NotImplementedError: If the provider doesn't support embeddings
        """
        if not self.supports_embeddings:
            raise NotImplementedError(f"Provider '{self.name}' does not support embeddings")
        raise NotImplementedError("Embedding not implemented")

    async def health_check(self) -> dict[str, Any]:
        """
        Check the health/status of this provider.
        
        Returns:
            dict with health information, including:
            - 'status': 'healthy' or 'unhealthy'
            - 'latency_ms': response time for health check
            - 'error': error message if unhealthy
            - Any other provider-specific health data
        """
        return {"status": "healthy", "latency_ms": 0}
