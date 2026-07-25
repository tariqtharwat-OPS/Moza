import pytest

from moza.core.context import ExecutionContext
from moza.core.context_builder import ContextBuilder
from moza.core.models import Event, EventType, Session, Task
from moza.tools.filesystem_tool import FilesystemTool
from moza.tools.registry import ToolRegistry
from moza.tools.terminal_tool import TerminalTool


def _make_context(session: Session, registry: ToolRegistry | None = None) -> ExecutionContext:
    if registry is None:
        registry = ToolRegistry()
    return ExecutionContext.build(
        session=session,
        environment=session.environment,
        tool_registry=registry,
    )


@pytest.mark.asyncio
async def test_context_builder_returns_string():
    session = Session()
    task = Task(session_id=session.id, description="Write a poem")
    session.tasks.append(task)
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    await registry.load(TerminalTool())
    context = _make_context(session, registry)
    result = await ContextBuilder.build_context(context)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_context_contains_all_seven_sections():
    session = Session()
    task = Task(session_id=session.id, description="Deploy the app")
    session.tasks.append(task)
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    await registry.load(TerminalTool())
    context = _make_context(session, registry)
    result = await ContextBuilder.build_context(context)
    assert "[Workspace Tree]" in result
    assert "[Current Directory]" in result
    assert "[Git Status]" in result
    assert "[Recent Events]" in result
    assert "[Current Task]" in result
    assert "[Available Tools]" in result
    assert "[Current Artifacts]" in result


@pytest.mark.asyncio
async def test_context_contains_task_description():
    session = Session()
    desc = "Create a file named 'hello.txt' with content 'world'."
    task = Task(session_id=session.id, description=desc)
    session.tasks.append(task)
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    context = _make_context(session, registry)
    result = await ContextBuilder.build_context(context)
    assert desc in result


@pytest.mark.asyncio
async def test_context_contains_tool_names():
    session = Session()
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    await registry.load(TerminalTool())
    context = _make_context(session, registry)
    result = await ContextBuilder.build_context(context)
    assert "filesystem" in result
    assert "terminal" in result
    assert "read_file" in result
    assert "write_file" in result
    assert "run_command" in result


@pytest.mark.asyncio
async def test_context_recent_events():
    session = Session()
    task = Task(session_id=session.id, description="Test events")
    session.tasks.append(task)
    session.execution_history.append(
        Event(session_id=session.id, task_id=task.id, type=EventType.AGENT_THINKING, source="test", payload={"content": "Thinking..."})
    )
    session.execution_history.append(
        Event(session_id=session.id, task_id=task.id, type=EventType.TOOL_CALL, source="test", payload={"tool": "filesystem", "args": {"action": "write", "path": "test.txt"}})
    )
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    context = _make_context(session, registry)
    result = await ContextBuilder.build_context(context)
    assert "agent_thinking" in result
    assert "tool_call" in result


@pytest.mark.asyncio
async def test_context_no_events_returns_placeholder():
    session = Session()
    task = Task(session_id=session.id, description="Empty history test")
    session.tasks.append(task)
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    context = _make_context(session, registry)
    result = await ContextBuilder.build_context(context)
    assert "no events yet" in result.lower() or "(no events yet)" in result


@pytest.mark.asyncio
async def test_context_workspace_tree_section():
    session = Session()
    task = Task(session_id=session.id, description="List dirs")
    session.tasks.append(task)
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    context = _make_context(session, registry)
    result = await ContextBuilder.build_context(context)
    assert "[Workspace Tree]" in result
    assert "not set" in result.lower() or "no workspace root" in result.lower()


@pytest.mark.asyncio
async def test_context_git_status_section():
    session = Session()
    task = Task(session_id=session.id, description="Git test")
    session.tasks.append(task)
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    context = _make_context(session, registry)
    result = await ContextBuilder.build_context(context)
    assert "[Git Status]" in result


@pytest.mark.asyncio
async def test_context_artifacts_section():
    session = Session()
    task = Task(session_id=session.id, description="Artifact test")
    session.tasks.append(task)
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    context = _make_context(session, registry)
    result = await ContextBuilder.build_context(context)
    assert "[Current Artifacts]" in result
    assert "no artifacts" in result.lower() or "(no artifacts)" in result
