"""Final comprehensive test: browser preview, no ool_call markers, no image.png error."""

import asyncio, json, os, uuid, base64
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
    log(f"  {'PASS' if passed else 'FAIL'}: {name} -- {detail}")

async def screenshot(page, name):
    path = os.path.join(SCREENSHOTS, f"final_{name}.png")
    await page.screenshot(path=path, full_page=True)
    log(f"  [SCREENSHOT] final_{name}.png")

async def execute_task(desc, timeout=120):
    sid = uuid.uuid4().hex[:12]
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
    log("[START] Final Fixes Test")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        # Load frontend
        await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
        await screenshot(page, "00_initial")

        # ── Test 1: No ool_call> markers in LLM streaming ──
        log("\n=== TEST 1: No ool_call> markers ===")
        events = await execute_task("Say hello and introduce yourself briefly")
        completed = any(e.get("type") == "task_completed" for e in events)

        # Check ALL LLM_FINISHED content for markers
        llm_finished = [e for e in events if e.get("type") == "llm_finished"]
        all_content = " ".join(e.get("payload", {}).get("content", "") for e in llm_finished)
        markers = ["ool_call>", "ool_result>", "tool_call>", "tool_result>", "<tool_call>", "<function="]
        found = [m for m in markers if m.lower() in all_content.lower()]
        result("No tool_call/ool_call markers in LLM output",
               completed and len(found) == 0,
               f"found={found}" if found else "clean")
        await screenshot(page, "01_no_markers")

        # ── Test 2: Browser preview populates the right panel ──
        log("\n=== TEST 2: Browser preview ===")
        events = await execute_task("Navigate to https://www.google.com and tell me the title")
        completed = any(e.get("type") == "task_completed" for e in events)
        browser_events = [e for e in events if e.get("payload", {}).get("tool") == "browser"]
        has_screenshot = any(
            "screenshot_base64" in str(e.get("payload", {}).get("metadata", {})) or
            "screenshot_base64" in str(e.get("payload", {}))
            for e in browser_events
        )
        result("Browser preview screenshot captured",
               completed and has_screenshot,
               f"browser_events={len(browser_events)}, has_screenshot={has_screenshot}")

        # Check if the frontend's browser visualizer shows the screenshot
        # by inspecting the last browser result event's payload
        browser_results = [e for e in browser_events if e.get("type") == "tool_result"]
        if browser_results:
            last_result = browser_results[-1]
            meta = last_result.get("payload", {}).get("metadata", {})
            b64 = meta.get("screenshot_base64") or last_result.get("payload", {}).get("screenshot_base64", "")
            result("Screenshot base64 data present and valid",
                   bool(b64) and len(b64) > 100,
                   f"b64_len={len(b64) if b64 else 0}")

        # Debug: Print the actual payload structure
        if browser_results:
            last_result = browser_results[-1]
            print("\nDEBUG: Last browser result payload structure:")
            print(json.dumps(last_result, indent=2))
            print("\nDEBUG: Metadata keys:", list(last_result.get("payload", {}).get("metadata", {}).keys()))
            print("DEBUG: Screenshot base64 length:", len(last_result.get("payload", {}).get("metadata", {}).get("screenshot_base64", "")))
        await screenshot(page, "02_browser_preview")

        # ── Test 3: Navigate to a site with bot protection ──
        log("\n=== TEST 3: Bot-protected site ===")
        events = await execute_task("Navigate to https://www.kingsseafood.com and tell me the page title")
        completed = any(e.get("type") == "task_completed" for e in events)
        failed = any(e.get("type") == "task_failed" for e in events)
        browser_errs = [e for e in events if e.get("type") == "tool_result" and e.get("payload", {}).get("tool") == "browser" and e.get("payload", {}).get("success") == False]
        # If it failed due to bot protection, check that error message is clean
        nav_result = any(
            e.get("type") == "tool_result" and
            e.get("payload", {}).get("tool") == "browser"
            for e in events
        )
        result("Bot-protected site navigation (may partially load, no crash)",
               completed or (not failed and nav_result),
               f"completed={completed}, failed={failed}, nav_attempted={nav_result}")
        await screenshot(page, "03_kingsseafood")

        # ── Test 4: No image.png error ──
        log("\n=== TEST 4: No image.png error ===")
        all_events_text = json.dumps(events)
        has_image_png_error = "image.png" in all_events_text and "does not support image" in all_events_text
        result("No 'image.png' model error in any event payload",
               not has_image_png_error,
               "clean" if not has_image_png_error else "FOUND image.png error")

        # ── Test 5: Context persistence across consecutive tasks ──
        log("\n=== TEST 5: Context persistence ===")
        shared_sid = uuid.uuid4().hex[:12]
        client = httpx.AsyncClient(timeout=httpx.Timeout(120))
        events1 = []
        async with client.stream("POST", f"{BACKEND_URL}/v1/task/execute",
            json={"session_id": shared_sid, "description": "Remember my favorite color is green"}) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    try:
                        ev = json.loads(line[5:].strip())
                        events1.append(ev)
                        if ev.get("type") == "waiting_approval":
                            await client.post(f"{BACKEND_URL}/v1/task/{ev['task_id']}/approve")
                    except json.JSONDecodeError:
                        pass
        result("First task (set context)", any(e.get("type") == "task_completed" for e in events1))

        events2 = []
        async with client.stream("POST", f"{BACKEND_URL}/v1/task/execute",
            json={"session_id": shared_sid, "description": "What is my favorite color?"}) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    try:
                        ev = json.loads(line[5:].strip())
                        events2.append(ev)
                        if ev.get("type") == "waiting_approval":
                            await client.post(f"{BACKEND_URL}/v1/task/{ev['task_id']}/approve")
                    except json.JSONDecodeError:
                        pass
        await client.aclose()
        completed2 = any(e.get("type") == "task_completed" for e in events2)
        mentions_green = any("green" in str(e.get("payload", {}).get("content", "")).lower()
                             for e in events2 if e.get("type") == "llm_finished")
        result("Context preserved across same-session tasks",
               completed2 and mentions_green,
               f"completed={completed2}, mentions_green={mentions_green}")
        await screenshot(page, "04_context")

        # ── Final UI check ──
        await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
        await asyncio.sleep(2)
        body_text = await page.inner_text("body")
        ui_markers = ["ool_call>", "ool_result>", "500 Internal Server Error", "Cannot read properties"]
        ui_found = [m for m in ui_markers if m in body_text]
        result("UI has no error text or debug markers",
               len(ui_found) == 0,
               f"found={ui_found}" if ui_found else "clean")
        await screenshot(page, "05_final_ui")

        await browser.close()

    # ── Report ──
    log("\n" + "=" * 65)
    log("FINAL FIXES TEST REPORT")
    log("=" * 65)
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
    total = len(RESULTS)
    log(f"Total: {total} | Passed: {passed} | Failed: {failed} | Rate: {passed/total*100:.1f}%")
    log("-" * 65)
    for r in RESULTS:
        icon = "[OK]" if r["status"] == "PASS" else "[FAIL]"
        log(f"{icon} {r['test']}: {r['detail']}")
    log("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
