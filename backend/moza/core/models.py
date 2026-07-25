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


class Workspace(BaseModel):
    """
    Represents a project workspace with root path and resource management.

    The `resource_manager` field is excluded from Pydantic serialization
    because it manages runtime state (file watchers, git connections, locks).
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    root_path: str = ""
    git_branch: str | None = None
    resource_manager: Any = Field(default=None, exclude=True)

    def ensure_resource_manager(self) -> ResourceManager:
        if not isinstance(self.resource_manager, ResourceManager):
            self.resource_manager = ResourceManager(
                workspace_path=self.root_path,
                git_branch=self.git_branch,
            )
        return self.resource_manager


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
    workspace: Workspace
    tasks: list[Task] = Field(default_factory=list)
    execution_history: list[Event] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
