"""Direct agent test - no API server needed."""
import asyncio
import json
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"

from moza.config.models import MOZAConfig
from moza.agents.litellm_tool_agent import LiteLLMToolAgent
from moza.core.context import ExecutionContext
from moza.core.models import Environment, Session, Task
from moza.core.event_bus import EventBus
from moza.core.cancellation import CancellationToken
from moza.tools.registry import get_tool_registry

async def main():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml")
    config = MOZAConfig.from_yaml(config_path)
    
    registry = get_tool_registry()
    if not registry.get_all():
        from moza.tools.filesystem_tool import FilesystemTool
        from moza.tools.browser_tool import BrowserTool
        from moza.tools.terminal_tool import TerminalTool
        registry.register(FilesystemTool())
        registry.register(BrowserTool())
        registry.register(TerminalTool())
    session = Session(id="test_session")
    task = Task(session_id="test_session", description="Create a file named hello.txt in D:\\Moza with content 'Hello World'")
    session.tasks.append(task)
    
    context = ExecutionContext(
        session=session,
        environment=Environment(),
        tool_registry=registry,
        event_bus=EventBus(),
        cancellation_token=CancellationToken(),
    )
    
    agent = LiteLLMToolAgent(config)
    
    t0 = asyncio.get_event_loop().time()
    async for event in agent.execute(context):
        elapsed = asyncio.get_event_loop().time() - t0
        etype = event.type.value if hasattr(event.type, 'value') else str(event.type)
        
        if etype == "tool_call":
            print(f"\n*** TOOL_CALL [{elapsed:.1f}s] ***")
            print(f"  Tool: {event.payload['tool']}")
            print(f"  Args: {json.dumps(event.payload.get('args', {}), indent=2, ensure_ascii=False)}")
        elif etype == "tool_result":
            p = event.payload
            print(f"  TOOL_RESULT [{elapsed:.1f}s]: {p.get('tool','?')} success={p.get('success','?')}")
            if p.get('stderr'):
                print(f"    stderr: {p['stderr'][:200]}")
        elif etype == "llm_token":
            content = event.payload.get("content", "")
            if content.strip():
                print(f"  LLM_TOKEN [{elapsed:.1f}s] ({len(content)} chars): {content[:500]}")
        elif etype == "task_completed":
            print(f"  TASK_COMPLETED [{elapsed:.1f}s]")
        elif etype == "task_failed":
            print(f"  TASK_FAILED [{elapsed:.1f}s]: {event.payload}")
    
    path = "D:\\Moza\\hello.txt"
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    print(f"\n=== RESULT ===")
    print(f"File exists: {exists}, size: {size}")
    if exists:
        print(f"Content: {open(path).read()}")

if __name__ == "__main__":
    asyncio.run(main())
