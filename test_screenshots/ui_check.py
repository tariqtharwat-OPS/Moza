import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        errors = []
        page.on("console", lambda msg: errors.append(f"{msg.type}: {msg.text}"))

        await page.goto("http://localhost:3000", wait_until="networkidle", timeout=20000)
        await asyncio.sleep(2)

        await page.screenshot(path="ui_check.png", full_page=True)

        body = await page.inner_text("body")
        if "ERROR" in body or "error" in body.lower():
            print("ERROR TEXT IN PAGE BODY:")
            print(body[:2000])
        else:
            print("No error text found in page body.")

        logo = await page.query_selector('img[alt="MOZA"]')
        if logo:
            loaded = await logo.evaluate("el => el.complete && el.naturalWidth > 0")
            print(f"Logo loaded: {loaded}")
        else:
            print("Logo element not found!")

        if errors:
            print("\nConsole errors:")
            for e in errors:
                print(f"  {e}")
        else:
            print("No console errors.")

        print("Screenshot saved to ui_check.png")
        await browser.close()

asyncio.run(main())
