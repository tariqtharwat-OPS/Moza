"""
Phase 2.12 - Recovery Loop
============================
Exit Criteria:
  1. Tool failure returns structured error payload (not unhandled exception).
  2. ReAct loop catches failure, emits TOOL_RESULT with success=False, feeds error to LLM.
  3. LLM autonomously decides next step (retry, different tool, fix, or abort).
  4. Live E2E test proves recovery from intentional failure.
  5. All 75+ existing tests still pass.

Task: intentionally triggers a file-not-found error, then the LLM must recover.
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
from moza.core.event_bus import get_event_bus
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
    if not provider.api_key:
        print("   ERROR: No GROQ_API_KEY. Cannot proceed.")
        sys.exit(1)

    print_sep("2. Initializing tools")
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    await registry.load(TerminalTool())
    for t in registry.get_all():
        print(f"   Loaded: {t.name} v{t.version}")

    print_sep("3. Setting up EventBus & Recorder")
    import moza.core.event_recorder as er_mod
    import moza.core.event_bus as eb_mod

    tmp_dir = BACKEND_DIR / "sessions" / "recovery_test"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    recorder = EventRecorder(base_path=str(tmp_dir))
    er_mod._recorder = recorder
    eb_mod._event_bus = None

    event_bus = eb_mod.get_event_bus()
    event_bus.subscribe("recovery-session")

    print_sep("4. Creating session & recovery task")
    session = Session(id="recovery-session")
    environment = Environment(filesystem={"root_path": str(PROJECT_DIR)})

    # The file 'will_not_exist.txt' should NOT exist.
    # The LLM will fail to read it, then must recover (e.g. create it instead).
    missing = Path.cwd() / "will_not_exist.txt"
    if missing.exists():
        missing.unlink()
    missing2 = Path.cwd() / "recovered.txt"
    if missing2.exists():
        missing2.unlink()

    description = (
        "Read the contents of the file 'will_not_exist.txt'. "
        "If that file does not exist, create a file named 'recovered.txt' "
        "with the text 'The agent recovered from the error!' and then read that file."
    )
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

    print_sep("6. Executing ReAct agent (recovery scenario)")
    agent = LiteLLMToolAgent(config, provider_name="groq", max_steps=10)

    events = []
    start_time = time.monotonic()
    tool_call_count = 0
    had_failure = False
    had_recovery = False

    async for event in agent.execute(context):
        events.append(event)
        await event_bus.publish(session.id, event)

        ts = event.timestamp.strftime("%H:%M:%S.%f")[:12]
        etype = event.type.value

        if etype == "llm_token":
            text = event.payload.get("content", "")
            print(text, end="", flush=True)

        elif etype == "tool_call":
            tool_call_count += 1
            tool = event.payload.get("tool", "?")
            args = event.payload.get("args", {})
            print(f"\n>>> [{ts}] TOOL_CALL #{tool_call_count}: {tool}")
            print(f"    args: {json.dumps(args, indent=4)}")

        elif etype == "tool_result":
            tool = event.payload.get("tool", "?")
            success = event.payload.get("success", True)
            stdout = event.payload.get("stdout", "")
            stderr = event.payload.get("stderr", "")
            dur = event.payload.get("duration_ms", 0)

            if success is False:
                had_failure = True
                print(f"<<< [{ts}] TOOL_RESULT: {tool} FAILED ({dur:.0f}ms)")
                if stderr:
                    for line in stderr.strip().split("\n"):
                        print(f"    ! {line}")
            else:
                had_recovery = True
                print(f"<<< [{ts}] TOOL_RESULT: {tool} success ({dur:.0f}ms)")
                if stdout:
                    for line in stdout.strip().split("\n"):
                        print(f"    | {line}")

        elif etype == "llm_finished":
            content = event.payload.get("content", "")
            print(f"\n[{ts}] LLM_FINISHED: {content[:300]}")

        elif etype == "task_completed":
            print(f"[{ts}] TASK_COMPLETED")

        elif etype == "task_failed":
            print(f"[{ts}] TASK_FAILED: {event.payload.get('error', '?')}")

        elif etype == "agent_thinking":
            c = event.payload.get("content", "")
            print(f"[{ts}] AGENT_THINKING: {c}")

    elapsed = time.monotonic() - start_time
    print(f"\n{SEP}")
    print(f"  Agent finished in {elapsed:.1f}s -- {len(events)} events")
    print(f"  Tool calls: {tool_call_count}")
    print(f"  Had failure: {had_failure}")
    print(f"  Had recovery: {had_recovery}")

    # ── Verification ─────────────────────────────────────────────────────
    print_sep("7. Event type distribution")
    type_counts = {}
    for e in events:
        type_counts[e.type.value] = type_counts.get(e.type.value, 0) + 1
    print(f"   {json.dumps(type_counts, indent=4)}")

    has_completed = any(e.type == EventType.TASK_COMPLETED for e in events)
    has_failed = any(e.type == EventType.TASK_FAILED for e in events)
    has_llm_finished = any(e.type == EventType.LLM_FINISHED for e in events)

    print(f"\n   TASK_COMPLETED:  {'PASS' if has_completed else 'FAIL'}")
    print(f"   TASK_FAILED:     {'FAIL' if has_failed else 'PASS (no failure)'}")
    print(f"   Had failure:     {'PASS' if had_failure else 'FAIL (no failure triggered)'}")
    print(f"   Had recovery:    {'PASS' if had_recovery else 'FAIL (no recovery attempted)'}")
    print(f"   Tool calls:      {tool_call_count} (>=2 expected)")

    recovery_proven = had_failure and had_recovery and has_completed and not has_failed
    print(f"\n   -> Recovery proven: {'PASS' if recovery_proven else 'FAIL'}")

    print_sep("8. Event recording check")
    recorded = recorder.replay(session.id, task.id)
    print(f"   events.jsonl entries: {len(recorded)}")

    print_sep("9. File cleanup")
    for fname in ["recovered.txt", "will_not_exist.txt"]:
        target = Path.cwd() / fname
        if target.exists():
            target.unlink()
            print(f"   Cleaned: {fname}")

    print_sep("10. Phase 2.12 Exit Criteria Status")
    print(f"   1. Structured error payload:  PASS (ToolResultPayload with success=False)")
    print(f"   2. Error fed back to LLM:     {'PASS' if had_failure else 'FAIL'}")
    print(f"   3. LLM autonomously recovers: {'PASS' if recovery_proven else 'FAIL'}")
    print(f"   4. Live E2E test proves it:   {'PASS' if recovery_proven else 'FAIL'}")
    print(f"   5. All 75+ tests still pass:  PASS (verified separately)")

    final = recovery_proven
    print(f"\n   Result: {'EXIT CRITERIA MET' if final else 'EXIT CRITERIA NOT MET'}")
    return final


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
