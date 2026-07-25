"""
Phase 3.1 — Browser Live Benchmark

Proves the agent can autonomously navigate the web, interact with elements,
extract data, and save artifacts using BrowserTool + PlaywrightEngine.

Task: Open Wikipedia, search for "Python (programming language)",
      extract the first paragraph, take a screenshot, save artifacts.
"""

import asyncio
import json
import os
import shutil
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
from moza.tools.browser_tool import BrowserTool
from moza.tools.filesystem_tool import FilesystemTool
from moza.tools.registry import ToolRegistry

SEP = "=" * 72


def psep(title: str) -> None:
    print(f"\n{SEP}\n  {title}\n{SEP}")


def _ensure_playwright() -> bool:
    try:
        import playwright
        return True
    except ImportError:
        return False


async def main():
    if not _ensure_playwright():
        print("FAIL: playwright not installed. Run: pip install playwright && playwright install chromium")
        return False

    psep("1. Loading config")
    config = MOZAConfig.from_yaml(PROJECT_DIR / "config.yaml")
    provider = config.get_provider("groq")
    print(f"   Model: {provider.model}")
    if not provider.api_key:
        print("   FAIL: No GROQ_API_KEY")
        return False

    psep("2. Initializing tools (Filesystem + Browser)")
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    await registry.load(BrowserTool(headless=True))
    for t in registry.get_all():
        print(f"   Loaded: {t.name} v{t.version}")

    psep("3. Setting up EventBus & Recorder")
    import moza.core.event_recorder as er_mod
    import moza.core.event_bus as eb_mod

    session_dir = BACKEND_DIR / "sessions" / "browser_live_benchmark"
    if session_dir.exists():
        shutil.rmtree(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)

    recorder = EventRecorder(base_path=str(session_dir))
    er_mod._recorder = recorder
    eb_mod._event_bus = None
    event_bus = eb_mod.get_event_bus()
    event_bus.subscribe("browser-bench")

    psep("4. Creating session & task")
    workspace_root = session_dir / "workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)

    env = Environment(filesystem={"root_path": str(workspace_root)})
    session = Session(id="browser-bench")
    task_description = (
        "Perform the following steps using the browser tool:\n"
        "1. Navigate to https://en.wikipedia.org\n"
        "2. Search for 'Python (programming language)' using the search input\n"
        "3. Extract the first paragraph of the main article\n"
        "4. Take a screenshot of the page\n"
        "5. Save the extracted text to a file named 'wikipedia_python.txt' "
        "and note the screenshot was taken\n"
        "Then report what you found."
    )
    task = Task(session_id=session.id, description=task_description)
    session.tasks.append(task)
    print(f"   Session: {session.id}")
    print(f"   Task:    {task.id}")
    print(f"   Workspace: {workspace_root}")

    psep("5. ExecutionContext")
    ctx = ExecutionContext.build(
        session=session,
        environment=env,
        tool_registry=registry,
        event_bus=event_bus,
    )

    psep("6. Executing agent (browser task — may take 30-90s)")
    agent = LiteLLMToolAgent(config, provider_name="groq", max_steps=15)
    events: list = []
    t0 = time.monotonic()
    call_count = 0

    async for event in agent.execute(ctx):
        events.append(event)
        await event_bus.publish(session.id, event)
        ts = event.timestamp.strftime("%H:%M:%S.%f")[:12]
        etype = event.type.value

        if etype == "llm_token":
            text = event.payload.get("content", "")
            print(text, end="", flush=True)

        elif etype == "tool_call":
            call_count += 1
            tool = event.payload.get("tool", "?")
            args = event.payload.get("args", {})
            print(f"\n>>> [{ts}] TOOL_CALL #{call_count}: {tool}")
            for aline in json.dumps(args, indent=2).split("\n"):
                print(f"    {aline}")

        elif etype == "tool_result":
            tool = event.payload.get("tool", "?")
            success = event.payload.get("success", True)
            stdout = event.payload.get("stdout", "")
            stderr = event.payload.get("stderr", "")
            dur = event.payload.get("duration_ms", 0)
            status = "OK" if success else "FAIL"
            print(f"<<< [{ts}] TOOL_RESULT: {tool} {status} ({dur:.0f}ms)")
            if stdout:
                for line in stdout.strip().split("\n")[:8]:
                    print(f"    | {line}")
                if len(stdout.strip().split("\n")) > 8:
                    print(f"    | ... ({len(stdout)} total chars)")
            if stderr:
                for line in stderr.strip().split("\n"):
                    print(f"    ! {line}")
            # Show screenshot base64 presence
            meta = event.payload.get("metadata") or event.payload
            if meta.get("screenshot_base64"):
                b64 = meta["screenshot_base64"]
                print(f"    [screenshot: {len(b64)} base64 chars]")

        elif etype == "llm_finished":
            c = event.payload.get("content", "")
            print(f"\n[{ts}] LLM_FINISHED: {c[:300]}")
        elif etype == "task_completed":
            print(f"[{ts}] TASK_COMPLETED")
        elif etype == "task_failed":
            print(f"[{ts}] TASK_FAILED: {event.payload.get('error', '?')}")
        elif etype == "agent_thinking":
            print(f"[{ts}] AGENT_THINKING: {event.payload.get('content', '')}")

    elapsed = time.monotonic() - t0
    psep(f"7. Agent finished in {elapsed:.1f}s -- {len(events)} events")

    # ── Verify browser action sequence ──────────────────────────────────────
    psep("8. Validating browser action sequence")

    ev_dicts = [e.model_dump() for e in events]
    browser_calls = []
    file_writes = []
    has_completed = False
    has_failed = False

    for ev in ev_dicts:
        t = ev.get("type", "")
        p = ev.get("payload", {})
        if t == "tool_call":
            tool = p.get("tool", "")
            args = p.get("args", {})
            if tool == "browser":
                browser_calls.append(args.get("action", "?"))
            elif tool == "filesystem" and args.get("action") == "write":
                file_writes.append(args.get("path", ""))
        elif t == "task_completed":
            has_completed = True
        elif t == "task_failed":
            has_failed = True

    results = {
        "navigate_to_wikipedia": any(
            a == "navigate" for a in browser_calls
        ),
        "search_interaction": any(
            a in ("type", "click") for a in browser_calls
        ),
        "extracted_text": any(
            a == "extract_text" for a in browser_calls
        ),
        "took_screenshot": any(
            a == "screenshot" for a in browser_calls
        ),
        "saved_artifact_file": len(file_writes) >= 1,
        "task_completed": has_completed and not has_failed,
    }

    # Also verify screenshot_base64 exists in at least one browser result
    screenshot_b64_found = False
    for ev in ev_dicts:
        if ev.get("type") == "tool_result":
            p = ev.get("payload", {})
            meta = p.get("metadata") or p
            if meta.get("screenshot_base64"):
                screenshot_b64_found = True
                break
    results["screenshot_data_valid"] = screenshot_b64_found

    all_pass = all(results.values())
    for check, ok in results.items():
        print(f"   {'PASS' if ok else 'FAIL'}: {check}")

    # ── Event recording check ──────────────────────────────────────────────
    psep("9. Events persisted")
    recorded = recorder.replay(session.id, task.id)
    print(f"   events.jsonl entries: {len(recorded)}")

    # ── Artifact file check ────────────────────────────────────────────────
    psep("10. Artifact files")
    saved_files = list(workspace_root.iterdir()) if workspace_root.exists() else []
    if saved_files:
        for f in saved_files:
            content = f.read_text(encoding="utf-8")
            print(f"   {f.name}: {len(content)} chars")
    else:
        print("   (no files found in workspace)")

    # ── Summary ────────────────────────────────────────────────────────────
    psep("11. Phase 3.1 Exit Criteria")
    criteria = {
        "Navigated to Wikipedia": results["navigate_to_wikipedia"],
        "Performed search (type/click)": results["search_interaction"],
        "Extracted article text": results["extracted_text"],
        "Took screenshot with valid data": results["screenshot_data_valid"],
        "Saved artifact file via filesystem": results["saved_artifact_file"],
        "TASK_COMPLETED": results["task_completed"],
    }
    for name, ok in criteria.items():
        print(f"   {'PASS' if ok else 'FAIL'}: {name}")

    final = all(criteria.values())
    print(f"\n   Result: {'EXIT CRITERIA MET' if final else 'EXIT CRITERIA NOT MET'}")

    # ── Cleanup ────────────────────────────────────────────────────────────
    psep("12. Cleanup")
    await registry.unload("browser")
    shutil.rmtree(session_dir)
    print(f"   Removed: {session_dir}")

    return final


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
