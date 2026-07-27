"""MOZA Comprehensive Browser Testing — visible headed browser with auto-approval."""

import asyncio, json, os, sys, uuid
from datetime import datetime

import httpx
from playwright.async_api import async_playwright

SCREENSHOTS = r"D:\Moza\test_screenshots"
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
RESULTS = []

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def result(test_name: str, passed: bool, detail: str = ""):
    RESULTS.append({"test": test_name, "status": "PASS" if passed else "FAIL", "detail": detail})
    status = "PASS" if passed else "FAIL"
    log(f"  >>> {status}: {test_name} {'-- ' + detail if detail else ''}")

async def screenshot(page, name: str):
    path = os.path.join(SCREENSHOTS, f"{name}.png")
    await page.screenshot(path=path, full_page=True)
    log(f"  [SCREENSHOT] {name}.png")

async def backend_alive() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{BACKEND_URL}/docs")
            return r.status_code == 200
    except Exception:
        return False

async def call_test_chat(message: str) -> str:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{BACKEND_URL}/v1/test/chat", json={"message": message})
        return r.text

async def execute_task_with_auto_approval(description: str, timeout: int = 180) -> dict:
    """Submit a task via SSE, auto-approve any tool requests, return all events."""
    session_id = uuid.uuid4().hex[:12]
    events = []
    client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))
    try:
        async with client.stream(
            "POST", f"{BACKEND_URL}/v1/task/execute",
            json={"session_id": session_id, "description": description},
        ) as resp:
            async for line in resp.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("data:"):
                    try:
                        ev = json.loads(line[5:].strip())
                        events.append(ev)
                        etype = ev.get("type", "")
                        task_id = ev.get("task_id", "")
                        if etype == "waiting_approval":
                            log(f"  [AUTO-APPROVE] task {task_id}...")
                            await client.post(f"{BACKEND_URL}/v1/task/{task_id}/approve")
                    except json.JSONDecodeError:
                        pass
    except httpx.TimeoutException:
        log("  [TIMEOUT] Task timed out")
    except Exception as e:
        log(f"  [STREAM ERROR] {e}")
    finally:
        await client.aclose()
    return {"session_id": session_id, "events": events, "count": len(events)}

# ---- Tests ----

async def test_browser_tool(page):
    log("\n=== TEST 1: Browser Tool -- Google Navigate ===")
    result_data = await execute_task_with_auto_approval(
        "Navigate to https://www.google.com and tell me the page title and current URL"
    )
    ev = result_data["events"]
    tool_calls = [e for e in ev if e.get("type") in ("tool_call", "tool_result", "browser_action", "browser_started")]
    completed = any(e.get("type") == "task_completed" for e in ev)
    failed = any(e.get("type") == "task_failed" for e in ev)
    passed = completed and not failed
    result("Browser Tool -- Navigate to Google", passed,
           f"{result_data['count']} events, {len(tool_calls)} tool calls, completed={completed}, failed={failed}")
    await screenshot(page, "01_browser_tool")

async def test_filesystem_tool(page):
    log("\n=== TEST 2: Filesystem Tool -- Create & Read ===")
    content = f"MOZA Test File -- {datetime.now().isoformat()}"
    result_data = await execute_task_with_auto_approval(
        f'Write a file to D:\\Moza\\test_screenshots\\test_output.txt with content: "{content}", then read it back and show the content'
    )
    ev = result_data["events"]
    tool_calls = [e for e in ev if e.get("type") in ("tool_call", "tool_result")]
    completed = any(e.get("type") == "task_completed" for e in ev)
    failed = any(e.get("type") == "task_failed" for e in ev)
    file_exists = os.path.exists(r"D:\Moza\test_screenshots\test_output.txt")
    passed = completed and not failed
    result("Filesystem Tool -- Create & Read", passed,
           f"{result_data['count']} events, completed={completed}, file_exists={file_exists}")
    result("  + File exists on disk", file_exists)
    await screenshot(page, "02_filesystem_tool")

async def test_terminal_tool(page):
    log("\n=== TEST 3: Terminal Tool -- Run `dir` ===")
    result_data = await execute_task_with_auto_approval(
        "Run the command 'dir D:\\Moza\\test_screenshots' and tell me what files are listed"
    )
    ev = result_data["events"]
    tool_calls = [e for e in ev if e.get("type") in ("tool_call", "tool_result", "terminal_output")]
    has_terminal = any("terminal" in str(e).lower() or "dir" in str(e).lower() or "test_output" in str(e) for e in tool_calls)
    completed = any(e.get("type") == "task_completed" for e in ev)
    failed = any(e.get("type") == "task_failed" for e in ev)
    passed = completed and not failed
    result("Terminal Tool -- Run dir", passed,
           f"{result_data['count']} events, terminal_used={has_terminal}, completed={completed}, failed={failed}")
    await screenshot(page, "03_terminal_tool")

async def test_conversational_intent(page):
    log("\n=== TEST 4: Conversational Intent ===")
    await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
    await screenshot(page, "04a_frontend_loaded")
    reply = await call_test_chat("What is your name?")
    has_error = "error" in reply.lower()
    passed = len(reply) > 10 and not has_error
    result("Conversational Intent -- Pure LLM no tools", passed,
           f"Reply length: {len(reply)} chars, error={has_error}")
    await screenshot(page, "04b_conversational_result")

async def test_error_recovery(page):
    log("\n=== TEST 5: Error Recovery -- Non-existent file ===")
    result_data = await execute_task_with_auto_approval(
        "Try to read the file D:\\Moza\\test_screenshots\\nonexistent_xyz_file.txt and tell me what error occurs"
    )
    ev = result_data["events"]
    has_error = any("error" in str(e).lower() or "not found" in str(e).lower() or "exist" in str(e).lower() for e in ev)
    completed = any(e.get("type") == "task_completed" for e in ev)
    failed = any(e.get("type") == "task_failed" for e in ev)
    graceful = completed or (failed and has_error)
    passed = graceful
    result("Error Recovery -- Non-existent file handled gracefully", passed,
           f"{result_data['count']} events, error_detected={has_error}, completed={completed}, failed={failed}")
    await screenshot(page, "05_error_recovery")

async def test_vague_request(page):
    log("\n=== TEST 6: Vague Request -- 'Search the web' ===")
    result_data = await execute_task_with_auto_approval("Search the web")
    ev = result_data["events"]
    clarification = any(
        "clarif" in str(e.get("payload", {})).lower()
        or "specific" in str(e.get("payload", {})).lower()
        or "what" in str(e.get("payload", {})).lower()
        for e in ev
    )
    no_tool_execution = not any(e.get("type") == "tool_call" for e in ev[:5])
    passed = clarification or no_tool_execution
    result("Vague Request -- Asks for clarification", passed,
           f"{result_data['count']} events, clarification={clarification}, no_tool_execution={no_tool_execution}")
    await screenshot(page, "06_vague_request")

async def test_multistep(page):
    log("\n=== TEST 7: Multi-Step -- Create, Append, Read ===")
    result_data = await execute_task_with_auto_approval(
        "Step 1: Create a file at D:\\Moza\\test_screenshots\\multistep.txt with content 'Line 1\\n'. "
        "Step 2: Append 'Line 2\\n' to D:\\Moza\\test_screenshots\\multistep.txt. "
        "Step 3: Read D:\\Moza\\test_screenshots\\multistep.txt and show the final content."
    )
    ev = result_data["events"]
    tool_calls = [e for e in ev if e.get("type") in ("tool_call", "tool_result")]
    completed = any(e.get("type") == "task_completed" for e in ev)
    multi_file = os.path.exists(r"D:\Moza\test_screenshots\multistep.txt")
    passed = completed and multi_file and len(tool_calls) >= 2
    result("Multi-Step Task -- Create + Append + Read", passed,
           f"{result_data['count']} events, {len(tool_calls)} tool calls, completed={completed}, file_exists={multi_file}")
    await screenshot(page, "07_multistep_result")

async def generate_report():
    log("\n" + "=" * 60)
    log("COMPREHENSIVE TEST REPORT")
    log("=" * 60)
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
    total = len(RESULTS)
    log(f"\nTotal: {total}  |  Passed: {passed}  |  Failed: {failed}  |  Rate: {passed/total*100:.1f}%")
    log("-" * 60)
    for r in RESULTS:
        icon = "[OK]" if r["status"] == "PASS" else "[FAIL]"
        log(f"{icon} {r['test']}: {r['status']}  {r['detail']}")
    log("-" * 60)
    report_path = os.path.join(SCREENSHOTS, "TEST_REPORT.txt")
    with open(report_path, "w") as f:
        f.write(f"MOZA Comprehensive Browser Test Report\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Total: {total} | Passed: {passed} | Failed: {failed}\n\n")
        for r in RESULTS:
            f.write(f"[{r['status']}] {r['test']}: {r['detail']}\n")
    log(f"[REPORT] Saved: {report_path}")

async def main():
    log("[START] MOZA Comprehensive Browser Testing")
    log(f"Backend: {BACKEND_URL}  |  Frontend: {FRONTEND_URL}")

    if not await backend_alive():
        log("[ERROR] Backend is NOT running! Start: python backend/run_server.py")
        sys.exit(1)
    log("[OK] Backend is alive")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        try:
            await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
            log("[OK] Frontend loaded")
        except Exception as e:
            log(f"[WARN] Frontend load: {e}")
            result("Frontend UI reachable", False, str(e))

        # Run tests
        await test_conversational_intent(page)   # Test 4
        await test_browser_tool(page)            # Test 1
        await test_filesystem_tool(page)         # Test 2
        await test_terminal_tool(page)           # Test 3
        await test_error_recovery(page)          # Test 5
        await test_vague_request(page)           # Test 6
        await test_multistep(page)               # Test 7

        await generate_report()
        await browser.close()

    log("[DONE] All tests completed")

if __name__ == "__main__":
    asyncio.run(main())
