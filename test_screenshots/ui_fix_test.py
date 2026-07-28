"""Test the 3 UI fixes in a visible browser."""

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
    path = os.path.join(SCREENSHOTS, f"{name}.png")
    await page.screenshot(path=path, full_page=True)
    log(f"  [SCREENSHOT] {name}.png")

async def main():
    log("[START] UI Fix Browser Test")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=200)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
        log("[OK] Frontend loaded")
        await screenshot(page, "fix_00_initial_ui")

        await page.wait_for_timeout(2000)

        # Type a greeting to see clean status messages (Fix 1)
        input_el = page.locator('textarea, input[placeholder*="MOZA"], input[placeholder*="task"]').first
        await input_el.fill("Say hello in one word")
        await page.wait_for_timeout(500)
        await screenshot(page, "fix_01_greeting_input")

        # Press Enter
        await input_el.press("Enter")
        await page.wait_for_timeout(8000)
        await screenshot(page, "fix_01_greeting_result")

        # Now type a browser task to see browser panel (Fix 2) and tool log (Fix 3)
        await input_el.fill("Navigate to https://www.google.com and tell me the title")
        await page.wait_for_timeout(500)
        await screenshot(page, "fix_02_browser_task_input")

        # Submit the task with an API call to handle approval automatically
        log("[TASK] Submitting browser task via API...")
        session_id = uuid.uuid4().hex[:12]
        async with httpx.AsyncClient(timeout=180) as client:
            async with client.stream(
                "POST", f"{BACKEND_URL}/v1/task/execute",
                json={"session_id": session_id, "description": "Navigate to https://www.google.com and tell me the page title and current URL"},
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data:"):
                        try:
                            ev = json.loads(line[5:].strip())
                            if ev.get("type") == "waiting_approval":
                                await client.post(f"{BACKEND_URL}/v1/task/{ev['task_id']}/approve")
                        except json.JSONDecodeError:
                            pass

        await page.wait_for_timeout(3000)
        await screenshot(page, "fix_03_after_browser_task")

        await page.wait_for_timeout(2000)
        await screenshot(page, "fix_04_final_state")

        await browser.close()

    log("[DONE] UI test completed")

if __name__ == "__main__":
    asyncio.run(main())
