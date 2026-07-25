from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
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


class Workspace(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    root_path: str = ""
    git_branch: str | None = None


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    task_id: str
    type: ArtifactType
    path: str
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
