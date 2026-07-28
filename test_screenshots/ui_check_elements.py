import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)

        textarea = await page.query_selector("textarea")
        print(f"Textarea found: {textarea is not None}")
        if textarea:
            ph = await textarea.get_attribute("placeholder")
            print(f"Placeholder: {ph}")

        form = await page.query_selector("form")
        print(f"Form found: {form is not None}")

        btn = await page.query_selector("button[type=submit]")
        print(f"Submit button: {btn is not None}")

        status = await page.inner_text("body")
        print(f"Shows Connected: {'Connected' in status}")
        print(f"Shows Execution: {'Execution' in status}")
        print(f"Shows Welcome: {'Welcome' in status}")

        await browser.close()

asyncio.run(main())
