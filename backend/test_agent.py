import asyncio
import sys
sys.path.insert(0, 'D:\\Moza\\backend')
from moza.agents.litellm_tool_agent import LiteLLMToolAgent
from moza.config.models import MOZAConfig
from moza.tools.registry import get_tool_registry
from moza.tools.browser_tool import BrowserTool
from moza.tools.filesystem_tool import FilesystemTool
from moza.tools.terminal_tool import TerminalTool
from moza.core.context import ExecutionContext, Environment, EventBus
from moza.core.models import Session, Task
from moza.core.cancellation import CancellationToken

async def test():
    config = MOZAConfig.from_yaml('D:/Moza/config.yaml')
    registry = get_tool_registry()
    await registry.load(BrowserTool(headless=True))
    await registry.load(FilesystemTool())
    await registry.load(TerminalTool())
    
    agent = LiteLLMToolAgent(config, registry)
    
    session = Session()
    task = Task(session_id=session.id, description='Search Wikipedia for Artificial Intelligence')
    
    env = Environment(cwd='D:/Moza')
    event_bus = EventBus()
    cancellation_token = CancellationToken()
    context = ExecutionContext(session=session, tool_registry=registry, environment=env, cancellation_token=CancellationToken(), event_bus=EventBus())
    context.session.tasks = [task]
    
    print('Starting agent execution...')
    async for event in agent.execute(context):
        print(f'Event: {event.type}')
        if event.type == 'tool_call':
            print(f'  Tool: {event.payload.get("tool")}, Action: {event.payload.get("args")}')
        elif event.type == 'tool_result':
            stdout = event.payload.get('stdout', '')
            print(f'  Tool Result: success={event.payload.get("success")}, stdout={stdout[:150] if stdout else "None"}')
        elif event.type == 'llm_token':
            content = event.payload.get('content', '')
            if content:
                print(f'LLM Token: {content[:50]}...')
        elif event.type == 'llm_finished':
            print('LLM Finished')
            break

asyncio.run(test())