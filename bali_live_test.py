import asyncio
import json
import os
import urllib.request
from playwright.async_api import async_playwright

BALI_QUERY = "search for some good arab restaurants in bali and make me a report with top rated 5 I want the result in nice looking HTML file saved as: D:/0Bali.html"
BACKEND_URL = "http://localhost:8001"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("1. Loading frontend...")
        await page.goto("http://localhost:3001", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        body = await page.evaluate("() => document.body.innerText")
        print(f"   'Backend Connected' = {'Backend Connected' in body}")
        print(f"   'N/A' in UI = {'N/A' in body}")
        print(f"   '#1' in UI = {'#1' in body}")
        print(f"   'groq-moza' in UI = {'groq-moza' in body}")

        textarea = await page.query_selector("textarea")
        if not textarea:
            print("ERROR: No textarea found!")
            await browser.close()
            return

        await textarea.fill(BALI_QUERY)
        print(f"2. Typed Bali query ({len(BALI_QUERY)} chars)")
        await textarea.press("Enter")
        print("3. Submitted - monitoring for 120s...")

        for i in range(12):
            await asyncio.sleep(10)
            body = await page.evaluate("() => document.body.innerText")
            html = await page.evaluate("() => document.documentElement.outerHTML")
            has_browser = "Browser" in body
            has_expand = "M4 8V4m0 0h4M4 4l5 5" in html
            has_result = "0Bali.html" in body or "bali" in body.lower() or "arab" in body.lower()

            print(f"   t={10*(i+1)}s: browser={has_browser}, expand_btn={has_expand}, result_mentioned={has_result}")

            if "0Bali.html" in body:
                print("   >>> File referenced in UI!")
                break

        file_exists = os.path.exists("D:/0Bali.html")
        file_size = os.path.getsize("D:/0Bali.html") if file_exists else 0
        print(f"\n4. D:/0Bali.html exists={file_exists}, size={file_size}")

        try:
            resp = urllib.request.urlopen(f"{BACKEND_URL}/v1/orchestrator/info", timeout=5)
            info = json.loads(resp.read())
            print(f"   Backend: connected, provider={info.get('current_provider')}, model={info.get('current_model')}")
        except Exception as e:
            print(f"   Backend: DISCONNECTED ({e})")

        await browser.close()

asyncio.run(main())
