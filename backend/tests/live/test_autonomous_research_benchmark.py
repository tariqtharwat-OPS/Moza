"""
Phase 3.2 — Autonomous Research Benchmark

Agent receives a high-level research task: compare two Python releases
from locally-served HTML fixtures, extract data across two pages,
synthesize a recommendation, and save a structured Markdown report.

Stability guarantee: static HTML served via local HTTP server.
No reliance on live, changing data. 100% reproducible.
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = PROJECT_DIR / "backend"
FIXTURES_DIR = BACKEND_DIR / "tests" / "fixtures" / "research"
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
REASONING_KEYWORDS = ["synthesized", "recommend", "production", "stable", "because", "adoption"]


def psep(title: str) -> None:
    print(f"\n{SEP}\n  {title}\n{SEP}")


def _check_playwright() -> bool:
    try:
        import playwright
        return True
    except ImportError:
        return False


async def main():
    if not _check_playwright():
        print("FAIL: playwright not installed.")
        return False

    psep("1. Starting local HTTP server for fixture pages")
    import http.server
    import socketserver
    import threading

    os.chdir(str(FIXTURES_DIR))
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print(f"   Serving fixtures on http://127.0.0.1:{port}")
    pages = {
        "releases": f"http://127.0.0.1:{port}/releases.html",
        "features": f"http://127.0.0.1:{port}/features.html",
    }
    for name, url in pages.items():
        print(f"   {name}: {url}")

    psep("2. Loading config")
    config = MOZAConfig.from_yaml(PROJECT_DIR / "config.yaml")
    provider = config.get_provider("groq")
    print(f"   Model: {provider.model}")
    if not provider.api_key:
        print("   FAIL: No GROQ_API_KEY")
        return False

    psep("3. Initializing tools")
    registry = ToolRegistry()
    await registry.load(FilesystemTool())
    await registry.load(BrowserTool(headless=True))
    for t in registry.get_all():
        print(f"   Loaded: {t.name} v{t.version}")

    psep("4. Setting up EventBus & Recorder")
    import moza.core.event_recorder as er_mod
    import moza.core.event_bus as eb_mod

    session_dir = BACKEND_DIR / "sessions" / "autonomous_research_benchmark"
    if session_dir.exists():
        shutil.rmtree(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)

    recorder = EventRecorder(base_path=str(session_dir))
    er_mod._recorder = recorder
    eb_mod._event_bus = None
    event_bus = eb_mod.get_event_bus()
    event_bus.subscribe("research-bench")

    psep("5. Creating session & research task")
    workspace_root = session_dir / "workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)
    env = Environment(filesystem={"root_path": str(workspace_root)})

    session = Session(id="research-bench")
    task_description = (
        "Research Python 3.8.0 and Python 3.9.0 using the local documentation "
        f"at {pages['releases']} and {pages['features']}. "
        "Navigate to both pages, extract the release dates, key features, "
        "end-of-life dates, and adoption stability information. "
        "Compare the two releases, determine which one was more stable "
        "for production use, and explain your reasoning. "
        "Save a structured Markdown report named research.md to the workspace "
        "with sections for Version Info, Feature Comparison, and Recommendation."
    )
    task = Task(session_id=session.id, description=task_description)
    session.tasks.append(task)
    print(f"   Session: {session.id}")
    print(f"   Task:    {task.id}")

    psep("6. ExecutionContext")
    ctx = ExecutionContext.build(
        session=session, environment=env,
        tool_registry=registry, event_bus=event_bus,
    )

    psep("7. Executing agent (autonomous research — may take 30-120s)")
    agent = LiteLLMToolAgent(config, provider_name="groq", max_steps=10)
    events: list = []
    t0 = time.monotonic()
    call_count = 0
    final_content = ""

    async for event in agent.execute(ctx):
        events.append(event)
        await event_bus.publish(session.id, event)
        ts = event.timestamp.strftime("%H:%M:%S.%f")[:12]
        etype = event.type.value

        if etype == "llm_token":
            text = event.payload.get("content", "")
            final_content += text
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
            meta = event.payload.get("metadata") or event.payload
            if meta.get("screenshot_base64"):
                print(f"    [screenshot: {len(meta['screenshot_base64'])} base64 chars]")

        elif etype == "llm_finished":
            c = event.payload.get("content", "")
            print(f"\n[{ts}] LLM_FINISHED: {c[:600]}")
        elif etype == "task_completed":
            print(f"[{ts}] TASK_COMPLETED")
        elif etype == "task_failed":
            print(f"[{ts}] TASK_FAILED: {event.payload.get('error', '?')}")
        elif etype == "agent_thinking":
            print(f"[{ts}] AGENT_THINKING: {event.payload.get('content', '')}")

    elapsed = time.monotonic() - t0

    # ── Validate autonomous research sequence ─────────────────────────────
    psep("8. Validating research sequence")

    ev_dicts = [e.model_dump() for e in events]
    navigated_urls: set[str] = set()
    browser_actions: list[str] = []
    used_extract_text = False
    wrote_file = False
    file_content = ""
    has_completed = False
    has_failed = False

    for ev in ev_dicts:
        t = ev.get("type", "")
        p = ev.get("payload", {})
        if t == "tool_call":
            tool = p.get("tool", "")
            args = p.get("args", {})
            action = args.get("action", "")
            if tool == "browser":
                browser_actions.append(action)
                if action == "navigate":
                    navigated_urls.add(args.get("url", ""))
                elif action == "extract_text":
                    used_extract_text = True
            elif tool == "filesystem" and action == "write":
                wrote_file = True
                file_content = args.get("content", "")
        elif t == "task_completed":
            has_completed = True
        elif t == "task_failed":
            has_failed = True

    # Synthesized reasoning: check final output + written file for keywords
    search_text = (final_content + " " + file_content).lower()
    reasoning_found = sum(1 for kw in REASONING_KEYWORDS if kw in search_text)

    results = {
        "used_browser_multiple_times": len(browser_actions) >= 2,
        "navigated_to_more_than_one_source": len(navigated_urls) >= 2,
        "extracted_dom_content": used_extract_text,
        "wrote_file_to_workspace": wrote_file,
        "task_completed": has_completed and not has_failed,
        "contains_synthesized_reasoning": reasoning_found >= 2,
    }

    for check, ok in results.items():
        print(f"   {'PASS' if ok else 'FAIL'}: {check}")

    if navigated_urls:
        print(f"   Pages visited ({len(navigated_urls)}):")
        for u in navigated_urls:
            print(f"     - {u}")
    print(f"   Browser actions: {browser_actions}")

    # ── Event recording check ──────────────────────────────────────────────
    psep("9. Events persisted")
    recorded = recorder.replay(session.id, task.id)
    print(f"   events.jsonl entries: {len(recorded)}")

    # ── Exit Criteria ──────────────────────────────────────────────────────
    psep("10. Phase 3.2 Exit Criteria (Autonomous Research)")
    criteria = {
        "Navigated to multiple pages/sources": results["navigated_to_more_than_one_source"],
        "Used BrowserTool at least twice": results["used_browser_multiple_times"],
        "Extracted DOM content with extract_text": results["extracted_dom_content"],
        "Wrote file via FilesystemTool": results["wrote_file_to_workspace"],
        "Output contains synthesized reasoning (2+ keywords)": results["contains_synthesized_reasoning"],
        "TASK_COMPLETED": results["task_completed"],
    }
    for name, ok in criteria.items():
        print(f"   {'PASS' if ok else 'FAIL'}: {name}")

    # ── Validate written file ──────────────────────────────────────────────
    psep("11. Research report file analysis")
    written_path = None
    if wrote_file and file_content:
        print(f"   File length: {len(file_content)} chars")
        has_markdown = bool(re.search(r"#{1,6}\s", file_content))
        has_version_38 = "3.8.0" in file_content
        has_version_39 = "3.9.0" in file_content
        has_date = bool(re.search(r"20\d{2}-\d{2}-\d{2}", file_content))
        print(f"   Contains Markdown:    {'PASS' if has_markdown else 'FAIL'}")
        print(f"   Mentions 3.8.0:       {'PASS' if has_version_38 else 'FAIL'}")
        print(f"   Mentions 3.9.0:       {'PASS' if has_version_39 else 'FAIL'}")
        print(f"   Contains date:        {'PASS' if has_date else 'FAIL'}")
        criteria["markdown_report_has_structure"] = has_markdown
        criteria["report_mentions_both_versions"] = has_version_38 and has_version_39
        criteria["report_contains_dates"] = has_date
        print(f"\n   --- research.md content ---")
        print(file_content[:1200])
        print("   --- end ---")

    final = all(criteria.values())
    print(f"\n   Result: {'ALL EXIT CRITERIA MET' if final else 'EXIT CRITERIA NOT MET'}")
    print(f"   Elapsed: {elapsed:.1f}s")

    # ── Cleanup ────────────────────────────────────────────────────────────
    psep("12. Cleanup")
    httpd.shutdown()
    print("   HTTP server stopped.")
    await registry.unload("browser")
    shutil.rmtree(session_dir)
    print(f"   Removed: {session_dir}")
    os.chdir(str(PROJECT_DIR))

    return final


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
