"""Test the 3 critical fixes: Browser, Context, UI markers."""

import asyncio, json, os, uuid
from datetime import datetime

import httpx
from playwright.async_api import async_playwright

SCREENSHOTS = r"D:\Moza\test_screenshots"
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
RESULTS = []

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def result(name, passed, detail=""):
    RESULTS.append({"test": name, "status": "PASS" if passed else "FAIL", "detail": detail})
    log(f"  >>> {'PASS' if passed else 'FAIL'}: {name}")

async def screenshot(page, name):
    path = os.path.join(SCREENSHOTS, f"critical_{name}.png")
    await page.screenshot(path=path, full_page=True)
    log(f"  [SCREENSHOT] critical_{name}.png")

_shared_session = None

async def execute_with_auto_approve(desc, timeout=120, use_same_session=False):
    """Submit task and auto-approve tool calls."""
    global _shared_session
    if use_same_session and _shared_session:
        sid = _shared_session
    else:
        sid = uuid.uuid4().hex[:12]
        _shared_session = sid
    events = []
    client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))
    try:
        async with client.stream("POST", f"{BACKEND_URL}/v1/task/execute",
            json={"session_id": sid, "description": desc}) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    try:
                        ev = json.loads(line[5:].strip())
                        events.append(ev)
                        if ev.get("type") == "waiting_approval":
                            await client.post(f"{BACKEND_URL}/v1/task/{ev['task_id']}/approve")
                    except json.JSONDecodeError:
                        pass
    except httpx.TimeoutException:
        log("  [TIMEOUT]")
    except Exception as e:
        log(f"  [ERROR] {e}")
    finally:
        await client.aclose()
    return events

async def main():
    log("[START] Critical Fixes Test")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=200)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        # Load frontend
        await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
        log("[OK] Frontend loaded")
        await screenshot(page, "00_initial")

        # ── Test 1: Browser tool works ──
        log("\n=== TEST 1: Browser Tool ===")
        events = await execute_with_auto_approve(
            "Navigate to https://www.google.com and tell me the title"
        )
        completed = any(e.get("type") == "task_completed" for e in events)
        has_browser = any("browser" in str(e) for e in events)
        result("Browser Tool execution", completed and has_browser,
               f"events={len(events)}, completed={completed}")
        await screenshot(page, "01_browser_result")

        # Check body text for debug markers
        body = await page.inner_text("body")
        has_debug_markers = "ool_call>" in body or "<function=" in body
        result("No 'ool_call>' debug markers visible", not has_debug_markers)

        # ── Test 2: Context preserved across consecutive messages ──
        log("\n=== TEST 2: Context Persistence ===")
        # Step 1: First message (same session)
        events1 = await execute_with_auto_approve(
            "Remember this fact: my favorite color is blue",
            use_same_session=True
        )
        completed1 = any(e.get("type") == "task_completed" for e in events1)
        result("First message (set context)", completed1)

        # Step 2: Second message referencing first (same session!)
        events2 = await execute_with_auto_approve(
            "What is my favorite color?",
            use_same_session=True
        )
        completed2 = any(e.get("type") == "task_completed" for e in events2)
        # Check if the agent's response mentions "blue"
        has_llm_finished = [e for e in events2 if e.get("type") == "llm_finished"]
        content_has_color = any("blue" in str(e.get("payload", {})).lower() for e in has_llm_finished)
        result("Context preserved - agent remembers favorite color",
               completed2 and content_has_color,
               f"completed={completed2}, mentions_blue={content_has_color}")
        await screenshot(page, "02_context_result")

        # ── Test 3: No UI debug markers ──
        log("\n=== TEST 3: UI Cleanliness ===")
        await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(2000)
        body_text = await page.inner_text("body")
        markers = ["ool_call>", "tool_call>", "tool_result>", "<function=", "Task received."]
        found_markers = [m for m in markers if m in body_text]
        result("No debug markers in UI", len(found_markers) == 0,
               f"found={found_markers}" if found_markers else "clean")
        await screenshot(page, "03_ui_clean")

        await browser.close()

    # Report
    log("\n" + "=" * 60)
    log("CRITICAL FIXES TEST REPORT")
    log("=" * 60)
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
    total = len(RESULTS)
    log(f"Total: {total} | Passed: {passed} | Failed: {failed} | Rate: {passed/total*100:.1f}%")
    for r in RESULTS:
        icon = "[OK]" if r["status"] == "PASS" else "[FAIL]"
        log(f"{icon} {r['test']}: {r['detail']}")

if __name__ == "__main__":
    asyncio.run(main())
