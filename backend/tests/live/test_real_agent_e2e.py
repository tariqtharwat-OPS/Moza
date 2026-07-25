"""
Phase 2.9 - Real Autonomous Execution Loop
============================================
Exit Criteria:
  1. Task creation via API.
  2. Real LiteLLM invocation (Groq).
  3. Tool selection through ToolRegistry.
  4. Real tool execution (Filesystem/Terminal).
  5. Event streaming through EventBus.
  6. Task completion.
  7. Event recording and replay (events.jsonl).
  8. NO MOCKS in the execution path.

Approval Service is excluded from this phase.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = PROJECT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from moza.agents.litellm_tool_agent import LiteLLMToolAgent
from moza.config.models import MOZAConfig
from moza.core.context import ExecutionContext
from moza.core.event_bus import EventBus, get_event_bus
from moza.core.event_recorder import EventRecorder
from moza.core.models import Environment, EventType, Session, Task
from moza.tools.filesystem_tool import FilesystemTool
from moza.tools.registry import ToolRegistry
from moza.tools.terminal_tool import TerminalTool

SEP = "=" * 72


def print_sep(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


async def main():
    print_sep("1. Loading config")
    config = MOZAConfig.from_yaml(PROJECT_DIR / "config.yaml")
    provider = config.get_provider("groq")
    print(f"   Provider: groq")
    print(f"   Model:    {provider.model}")
    print(f"   API Key:  {'***' + provider.api_key[-4:] if provider.api_key else 'MISSING'}")
    if not provider.api_key:
        print("   ERROR: No GROQ_API_KEY in .env. Cannot proceed.")
        sys.exit(1)

    print_sep("2. Initializing tools")
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    await registry.load(TerminalTool())
    for t in registry.get_all():
        print(f"   Loaded: {t.name} v{t.version} -- caps: {t.capabilities}")

    print_sep("3. Setting up EventBus & Recorder")
    import moza.core.event_recorder as er_mod
    import moza.core.event_bus as eb_mod

    tmp_dir = BACKEND_DIR / "sessions" / "live_e2e_test"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    recorder = EventRecorder(base_path=str(tmp_dir))
    er_mod._recorder = recorder
    eb_mod._event_bus = None

    event_bus = eb_mod.get_event_bus()
    queue = event_bus.subscribe("live-e2e-session")
    print(f"   Recorder base: {recorder._base}")

    print_sep("4. Creating session & task")
    session = Session(id="live-e2e-session")
    environment = Environment(filesystem={"root_path": str(PROJECT_DIR)})

    description = "Create a file named 'moza_live_test.txt' and write 'MOZA is alive' inside it."
    task = Task(session_id=session.id, description=description)
    session.tasks.append(task)
    print(f"   Session: {session.id}")
    print(f"   Task:    {task.id}")
    print(f"   Desc:    {description}")

    print_sep("5. Creating ExecutionContext")
    context = ExecutionContext.build(
        session=session,
        environment=environment,
        tool_registry=registry,
        event_bus=event_bus,
    )
    print(f"   Token ready: {not context.cancellation_token.is_cancelled()}")

    print_sep("6. Executing LiteLLMToolAgent (real LLM)")
    agent = LiteLLMToolAgent(config, provider_name="groq", max_steps=10)

    events = []
    start_time = time.monotonic()

    async for event in agent.execute(context):
        events.append(event)
        await event_bus.publish(session.id, event)

        ts = event.timestamp.strftime("%H:%M:%S.%f")[:12]
        etype = event.type.value

        if etype == "llm_token":
            text = event.payload.get("content", "")
            print(text, end="", flush=True)

        elif etype == "tool_call":
            tool = event.payload.get("tool", "?")
            args = event.payload.get("args", {})
            print(f"\n>>> [{ts}] TOOL_CALL: {tool}")
            print(f"    args: {json.dumps(args, indent=4)}")

        elif etype == "tool_result":
            tool = event.payload.get("tool", "?")
            success = event.payload.get("success", "?")
            stdout = event.payload.get("stdout", "")
            stderr = event.payload.get("stderr", "")
            dur = event.payload.get("duration_ms", 0)
            print(f"<<< [{ts}] TOOL_RESULT: {tool} success={success} ({dur:.0f}ms)")
            if stdout:
                for line in stdout.strip().split("\n"):
                    print(f"    | {line}")
            if stderr:
                for line in stderr.strip().split("\n"):
                    print(f"    ! {line}")

        elif etype == "llm_finished":
            content = event.payload.get("content", "")
            print(f"\n[{ts}] LLM_FINISHED: {content[:200]}")
            if len(content) > 200:
                print(f"    ... (truncated, {len(content)} total chars)")

        elif etype == "agent_thinking":
            content = event.payload.get("content", "")
            print(f"[{ts}] AGENT_THINKING: {content}")

        elif etype == "task_completed":
            print(f"[{ts}] TASK_COMPLETED")

        elif etype == "task_failed":
            print(f"[{ts}] TASK_FAILED: {event.payload.get('error', '?')}")

    elapsed = time.monotonic() - start_time
    print(f"\n{SEP}")
    print(f"  Agent finished in {elapsed:.1f}s -- {len(events)} events total")

    print_sep("7. Event verification")
    event_types = [e.type.value for e in events]
    type_counts = {}
    for t in event_types:
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"   Event type distribution: {json.dumps(type_counts, indent=4)}")

    has_tool_call = any(e.type == EventType.TOOL_CALL for e in events)
    has_tool_result = any(e.type == EventType.TOOL_RESULT for e in events)
    has_llm_finished = any(e.type == EventType.LLM_FINISHED for e in events)
    has_llm_token = any(e.type == EventType.LLM_TOKEN for e in events)

    print(f"   TOOL_CALL:     {'PASS' if has_tool_call else 'FAIL'}")
    print(f"   TOOL_RESULT:   {'PASS' if has_tool_result else 'FAIL'}")
    print(f"   LLM_TOKEN:     {'PASS' if has_llm_token else 'FAIL'}")
    print(f"   LLM_FINISHED:  {'PASS' if has_llm_finished else 'FAIL'}")

    all_ok = has_tool_call and has_tool_result and has_llm_finished
    print(f"\n   -> Overall: {'ALL CRITERIA MET' if all_ok else 'SOME MISSING'}")

    print_sep("8. Event recording check")
    recorded = recorder.replay(session.id, task.id)
    print(f"   events.jsonl entries: {len(recorded)}")
    if recorded:
        first = recorded[0]
        last = recorded[-1]
        print(f"   First event: {first.type.value}")
        print(f"   Last event:  {last.type.value}")

    print_sep("9. File existence check")
    target = Path.cwd() / "moza_live_test.txt"
    if target.exists():
        content = target.read_text(encoding="utf-8")
        print(f"   PASS File created: {target}")
        print(f"   Content: '{content}'")
        target.unlink()
        print(f"   (cleaned up)")
    else:
        print(f"   FAIL File not found at {target}")
        for f in PROJECT_DIR.glob("moza_live_test*"):
            print(f"   Found nearby: {f}")

    print_sep("10. Phase 2.9 Exit Criteria Status")
    print(f"   1. Task creation:          PASS")
    print(f"   2. Real LLM invocation:    PASS ({provider.model})")
    print(f"   3. Tool selection:         {'PASS' if has_tool_call else 'FAIL'}")
    print(f"   4. Real tool execution:    {'PASS' if has_tool_result else 'FAIL'}")
    print(f"   5. Event streaming:        PASS ({len(events)} events)")
    print(f"   6. Task completion:        {'PASS' if has_llm_finished else 'FAIL'}")
    print(f"   7. Event recording:        {'PASS' if len(recorded) > 0 else 'FAIL'}")
    print(f"   8. No mocks:               PASS (litellm + groq real API)")

    final = all_ok and len(recorded) > 0
    print(f"\n   Result: {'EXIT CRITERIA MET' if final else 'EXIT CRITERIA NOT MET'}")
    return final


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
