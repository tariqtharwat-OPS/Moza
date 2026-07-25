import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from moza.core.resource_manager import ResourceManager


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_TOOL = "waiting_tool"
    WAITING_USER = "waiting_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EventType(str, Enum):
    AGENT_STARTED = "agent_started"
    AGENT_THINKING = "agent_thinking"
    TOOL_SELECTED = "tool_selected"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    BROWSER_STARTED = "browser_started"
    BROWSER_ACTION = "browser_action"
    TERMINAL_OUTPUT = "terminal_output"
    LLM_TOKEN = "llm_token"
    LLM_FINISHED = "llm_finished"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    WAITING_APPROVAL = "waiting_approval"


class ArtifactType(str, Enum):
    FILE = "file"
    DIFF = "diff"
    IMAGE = "image"
    REPORT = "report"
    LOG = "log"


class ToolResultPayload(BaseModel):
    """Strict schema for TOOL_RESULT event payloads."""
    success: bool
    duration_ms: float
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    artifacts: list["Artifact"] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    @classmethod
    def error(cls, message: str, duration_ms: float = 0, exit_code: int = 1) -> "ToolResultPayload":
        return cls(success=False, duration_ms=duration_ms, exit_code=exit_code, stderr=message)

    @classmethod
    def ok(cls, stdout: str = "", duration_ms: float = 0, exit_code: int = 0, **kw: Any) -> "ToolResultPayload":
        return cls(success=True, duration_ms=duration_ms, exit_code=exit_code, stdout=stdout, **kw)


class _FilesystemState(BaseModel):
    root_path: str = ""
    git_branch: str | None = None


class _TerminalState(BaseModel):
    cwd: str = ""
    environment_vars: dict[str, str] = Field(default_factory=dict)
    shell_type: str = ""


class _BrowserState(BaseModel):
    active_tabs: list[str] = Field(default_factory=list)
    headless_mode: bool = True


class _DesktopState(BaseModel):
    active_windows: list[str] = Field(default_factory=list)
    clipboard: str = ""


class Environment(BaseModel):
    """
    Represents the full execution environment for an AI OS session.

    Subsumes the old Workspace concept and expands to cover all
    domains an AI agent can interact with: filesystem, terminal,
    browser, desktop, secrets, and memory.

    The `resource_manager` field is excluded from Pydantic serialization
    because it manages runtime state (file watchers, git connections, locks).
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    filesystem: _FilesystemState = Field(default_factory=_FilesystemState)
    terminal: _TerminalState = Field(default_factory=_TerminalState)
    browser: _BrowserState = Field(default_factory=_BrowserState)
    desktop: _DesktopState = Field(default_factory=_DesktopState)
    secrets: dict[str, str] = Field(default_factory=dict)
    memory: dict[str, Any] = Field(default_factory=dict)
    resource_manager: Any = Field(default=None, exclude=True)

    def ensure_resource_manager(self) -> ResourceManager:
        if not isinstance(self.resource_manager, ResourceManager):
            self.resource_manager = ResourceManager(
                workspace_path=self.filesystem.root_path,
                git_branch=self.filesystem.git_branch,
            )
        return self.resource_manager


class Workspace(Environment):
    """
    DEPRECATED: Use Environment instead.
    Kept for backward compatibility. Will be removed in a future release.

    Accepts top-level `root_path` and `git_branch` kwargs and maps them
    to the ``filesystem`` sub-domain for backward compat.
    """

    def __init__(self, **data):
        fs = data.get("filesystem")
        if not isinstance(fs, dict):
            fs = {}
        if "root_path" in data:
            fs.setdefault("root_path", data.pop("root_path"))
        if "git_branch" in data:
            fs.setdefault("git_branch", data.pop("git_branch"))
        data["filesystem"] = fs
        super().__init__(**data)


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    task_id: str
    type: ArtifactType
    path: str
    version: int = 1
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Task(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    session_id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    parent_task_id: str | None = None
    priority: str = "normal"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Event(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str
    task_id: str
    type: EventType
    source: str
    payload: dict = Field(default_factory=dict)


class Session(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    environment: Environment = Field(default_factory=Environment)
    tasks: list[Task] = Field(default_factory=list)
    execution_history: list[Event] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)

    @property
    def workspace(self) -> Environment:
        """Deprecated: use .environment instead."""
        return self.environment
